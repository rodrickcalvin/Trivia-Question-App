import os
from flask import Flask, request, abort, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category
from decorators.paginate import paginate_items


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    # CORS Headers
    @app.after_request
    def after_request(response):
        """
        After_request decorator to set Access-Control-Allow
        """
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    @app.route('/categories')
    def get_categories():
        """
        '/categories' handles GET requests for all
        available trivia question categories.
        """
        categories = Category.query.order_by(Category.id).all()
        categories_object = {
            category.id: category.type for category in categories
            }

        return jsonify({
            'success': True,
            'categories': categories_object
        })

    @app.route('/questions')
    def get_questions():
        """
        '/questions' handles GET requests for all questions,
        including pagination.

        @TEST: test_get_paginated_questions, test_404_request_beyond_valid_page
        """
        # All questions
        questions = Question.query.order_by(Question.id).all()

        # Paginated questions
        current_questions = paginate_items(request, questions)

        if len(current_questions) == 0:
            abort(404)

        categories = Category.query.order_by(Category.id).all()
        formatted_categories = {
            category.id: category.type for category in categories
        }

        return jsonify({
            'success': True,
            'categories': formatted_categories,
            'questions': current_questions,
            'total_questions': len(questions)
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        """
        Handles DELETE requests for specific question using a question ID.

        @TESTS: test_delete_question
        """
        try:
            # Get specific question by ID
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            # Abort if question doesn't exist
            if question is None:
                abort(404)

            # Delete question
            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id
            })

        except:
            # Abort if error
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        """
        Handles POST requests:
        - creation of a new question which will require
        the question and answer text, category, and difficulty score.
        - get questions by search term that is a substring.

        @TESTS:Create Question:
            -test_create_new_question,
            -test_422_if_question_creation_fails.
        @TESTS: Search:- test_search_questions, test_404_for_no_results.
        """
        try:
            body = request.get_json()

            # Get questions by search-term
            if body.get('search_term'):
                search_term = body.get('search_term')

                # filter list of questions by search-term
                filtered_questions = Question.query.filter(
                    Question.question.ilike(f'%{search_term}%')).all()

                # if no questions found abort
                if len(filtered_questions) == 0:
                    abort(Response(
                        'No questions found for {}'.format(search_term), 404
                        )
                    )

                # paginate filtered questions
                paginated_results = paginate_items(request, filtered_questions)

                # return results
                return jsonify({
                    'success': True,
                    'questions': paginated_results,
                    'total_questions': len(filtered_questions)
                })

            # Create new question
            else:
                new_question = body.get('question')
                new_answer = body.get('answer')
                new_difficulty = body.get('difficulty')
                new_category = body.get('category')

                # Abort if question, answer, category or difficulty are missing
                if (
                    new_question is None or
                    new_answer is None or
                    new_category is None or
                    new_difficulty is None
                ):
                    abort(422)

                # create instance of Question model
                question = Question(question=new_question, answer=new_answer,
                                    difficulty=new_difficulty,
                                    category=new_category
                                    )
                question.insert()

                # Return new question with all other questions
                all_questions = Question.query.order_by(Question.id).all()
                paginated_questions = paginate_items(request, all_questions)

                return jsonify({
                    'success': True,
                    'questions': paginated_questions,
                    'total_questions': len(all_questions),
                    'created': question.id
                })

        except:
            abort(422)

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        """
        Gets questions based on category.

        @TESTS:
        - test_get_questions_by_category,
        - test_404_if_categorized_questions_fail
        """

        # Abort if category doesn't exist
        selected_category = Category.query.filter(
            Category.id == category_id).one_or_none()
        if selected_category is None:
            abort(404)

        # Get questions by category
        categorized_questions = Question.query.filter(
            Question.category == category_id).all()

        # paginate questions
        paginated_questions = paginate_items(request, categorized_questions)

        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': len(categorized_questions),
            'current_category': selected_category.type
        })

    @app.route('/quizzes', methods=['POST'])
    def get_random_questions():
        """
        Handles request to get randomized questions to play the quiz.

        @TESTs: test_play_quiz, test_play_quiz_fails
        """
        try:
            body = request.get_json()

            # Get previous questions
            previous_questions = body.get('previous_questions')

            # Get category
            category = body.get('quiz_category')
            # Abort if category or previous questions don't exist
            if category is None or previous_questions is None:
                abort(400)

            # Get questions by category
            # return all questions if no/all category is selected
            if category['id'] == 0:
                # Check if question was already asked
                # If it was, get new question
                questions = Question.query.filter(
                    Question.id.not_in(previous_questions)).all()
            else:
                # Check if question was already asked
                # If it was, get new question
                questions = Question.query.filter(
                    Question.id.not_in(previous_questions),
                    Question.category == category['id']).all()

            # Get random question
            next_random_question = random.choice(questions)

            return jsonify({
                'success': True,
                'question': next_random_question.format(),
            })

        except:
            abort(422)

    # Error handlers for all expected errors==================================
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "internal server error"
        }), 500

    return app
