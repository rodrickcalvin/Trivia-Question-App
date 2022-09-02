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
    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
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
        '/categories' handles GET requests for all available trivia question categories.
        """
        categories = Category.query.order_by(Category.id).all()
        formatted_categories = [category.format() for category in categories]
        return jsonify({
            'success': True,
            'categories': formatted_categories
        })

    @app.route('/questions')
    def get_questions():
        """
        '/questions' handles GET requests for all questions,
        including pagination.

        @TEST: At this point, when you start the application
        you should see questions and categories generated,
        ten questions per page and pagination at the bottom of the screen for three pages.
        Clicking on the page numbers should update the questions.
        """
        # All questions
        questions = Question.query.order_by(Question.id).all()

        # Paginated questions
        current_questions = paginate_items(request, questions)

        categories = Category.query.order_by(Category.id).all()
        formatted_categories = [category.format() for category in categories]

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(questions),
            'categories': formatted_categories
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        """
        Handles DELETE requests for specific question using a question ID.

        TEST: When you click the trash icon next to a question, the question will be removed.
        This removal will persist in the database and when you refresh the page.
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

        @TEST: When you submit a question on the "Add" tab,
        the form will clear and the question will appear at the end of the last page
        of the questions list in the "List" tab.

        @TEST: Search by any phrase. The questions list will update to include
        only question that include that string within their question.
        Try using the word "title" to start.
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
                    abort(
                        Response('No questions found for {}'.format(search_term), 404))

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
                if new_question is None or new_answer is None or new_category is None or new_difficulty is None:
                    abort(422)

                # create instance of Question model
                question = Question(question=new_question, answer=new_answer,
                                    difficulty=new_difficulty, category=new_category)
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

    app.route('/categories/<int:category_id>/questions')

    def get_questions_by_category(category_id):
        """
        Gets questions based on category.

        @TEST: In the "List" tab / main screen, clicking on one of the
        categories in the left column will cause only questions of that
        category to be shown.
        """
        selected_category = Category.query.filter(
            Category.id == category_id).one_or_none()

        # Abort if category doesn't exist
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
    def get_random_questions(quiz_category, previous_qns):
        """
        Handles request to get randomized questions to play the quiz.

        TEST: In the "Play" tab, after a user selects "All" or a category,
        one question at a time is displayed, the user is allowed to answer
        and shown whether they were correct or not.
        """
        try:
            body = request.get_json()

            # Get previous questions
            previous_questions = body.get(previous_qns)

            # Get category
            category = body.get(quiz_category)


            # Abort if category or previous questions don't exist
            if category is None or previous_questions is None:
                abort(400)

            # Get questions by category and return all questions if no category is selected
            if category['id'] == 0:
                questions = Question.query.order_by(Question.id).all()
            else:
                questions = Question.query.filter(
                    Question.category == category['id']).all()

            
            # Get random number
            random_number = random.randint(0, len(questions) - 1)

            # Get random question 
            next_random_question = questions[random_number]
        
            # Check if question was already asked
            # If it was, get new question
            while next_random_question.id not in previous_qns:
                next_random_question = questions[random_number]

                return jsonify({
                    'success': True,
                    'question': {
                        'id': next_random_question.id,
                        'question': next_random_question.question,
                        'category': next_random_question.category,
                        'difficulty': next_random_question.difficulty,
                        'answer': next_random_question.answer
                    },
                    'previous_questions': previous_questions
                })

        except:
            abort(422)






    # Error handlers for all expected errors========================================
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

    return app
