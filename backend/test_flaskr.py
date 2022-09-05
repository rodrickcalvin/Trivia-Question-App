import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgresql://{}:{}@{}/{}".format(
            'student', 'student', 'localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # sample for a create new question
        self.new_question = {
            'question': 'What does the term "ruminant" mean?',
            'answer': 'An animal with a four-chambered stomach and two-toed feet',
            'difficulty': 5,
            'category': '1'
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_get_categories(self):
        """Tests category retrieval success"""

        # get response and load data
        response = self.client().get('/categories')
        data = json.loads(response.data)

        # check status code and message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

        # check that categories return data
        self.assertTrue(data['categories'])

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # TESTING QUESTION FETCHING=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

    def test_get_paginated_questions(self):
        """Tests question pagination success"""

        # get response and load data
        response = self.client().get('/questions')
        data = json.loads(response.data)

        # check status code and message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

        # check that categories, total_questions and questions return data
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['questions'])
        self.assertTrue(data['categories'])

    def test_404_request_beyond_valid_page(self):
        """Tests question pagination failure return 404"""

        # send request with bad page data, load response
        response = self.client().get('/questions?page=55555')
        data = json.loads(response.data)

        # check status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # TESTING QUESTION DELETION=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

    def test_delete_question(self):
        """Tests question deletion success"""

        # create a new question to be deleted
        question = Question(
            question=self.new_question['question'],
            answer=self.new_question['answer'],
            category=self.new_question['category'],
            difficulty=self.new_question['difficulty'])
        question.insert()

        # get the id of the new question
        q_id = question.id

        # get number of questions before delete
        questions_before = Question.query.all()

        # delete the question and store response
        response = self.client().delete('/questions/{}'.format(q_id))
        data = json.loads(response.data)

        # get number of questions after delete
        questions_after = Question.query.all()

        # see if the question has been deleted
        question = Question.query.filter(Question.id == 1).one_or_none()

        # check status code and success message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

        # check if question id matches deleted id
        self.assertEqual(data['deleted'], q_id)

        # check if one less question after delete
        self.assertTrue(len(questions_before) - len(questions_after) == 1)

        # check if question equals None after delete
        self.assertEqual(question, None)

    def test_404_if_question_deletion_fails(self):
        """Tests question deletion failure 422"""

        # get number of questions before delete
        questions_before = Question.query.all()

        # delete question with bad id, then load response data
        response = self.client().delete('/questions/5555')
        data = json.loads(response.data)

        # get number of questions after delete
        questions_after = Question.query.all()

        # check status code and success message
        self.assertEqual(response.status_code, 422)
        self.assertEqual(data['success'], False)

        # check if questions_after and questions_before are equal
        self.assertTrue(len(questions_after) == len(questions_before))

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # TESTING QUESTION CREATION=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

    def test_create_new_question(self):
        """Tests question creation success"""

        # get number of questions before post
        questions_before = Question.query.all()

        # create new question and load response data
        response = self.client().post('/questions', json=self.new_question)
        data = json.loads(response.data)

        # get number of questions after post
        questions_after = Question.query.all()

        # see if the question has been created
        question = Question.query.filter_by(id=data['created']).one_or_none()

        # check status code and success message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

        # check if one more question after post
        self.assertTrue(len(questions_after) - len(questions_before) == 1)

        # check that question is not None
        self.assertIsNotNone(question)

    def test_422_if_question_creation_fails(self):
        """Tests question creation failure 422"""

        # get number of questions before post
        questions_before = Question.query.all()

        # create new question without json data, then load response data
        response = self.client().post('/questions', json={})
        data = json.loads(response.data)

        # get number of questions after post
        questions_after = Question.query.all()

        # check status code and success message
        self.assertEqual(response.status_code, 422)
        self.assertEqual(data['success'], False)

        # check if questions_after and questions_before are equal
        self.assertTrue(len(questions_after) == len(questions_before))

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # TESTING SEARCH FEATURE-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

    def test_search_questions(self):
        """Tests search questions success"""

        # send post request with search term
        response = self.client().post('/questions',
                                      json={'search_term': 'which'})

        # load response data
        data = json.loads(response.data)

        # check response status code and message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

        # check that number of results = 1
        self.assertEqual(len(data['questions']), 7)

        # check that id of question in response is correct
        self.assertEqual(data['questions'][0]['id'], 10)

    def test_404_for_no_results(self):
        """Tests search for 404 when there are no results"""

        # send post request with search term that should fail
        response = self.client().post('/questions',
                                      json={'search_term': 'Bweyogerere'})

        # load response data
        data = json.loads(response.data)

        # check response status code and message
        self.assertEqual(response.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # TESTING GET QUESTIONS BY SPECIFIC CATEGORY-=-=-=-=-=-=-=-=-=-=-=-=-=-=

    def test_get_questions_by_category(self):
        """Tests getting questions by category success"""

        # send request with category id 1 for science
        response = self.client().get('/categories/1/questions')

        # load response data
        data = json.loads(response.data)

        # check response status code and message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

        # check that questions are returned (len != 0)
        self.assertNotEqual(len(data['questions']), 0)

        # check that current category returned is science
        self.assertEqual(data['current_category'], 'Science')

    def test_404_if_categorized_questions_fail(self):
        """Tests getting questions by category failure 400"""

        # send request with category id 100
        response = self.client().get('/categories/100/questions')

        # load response data
        data = json.loads(response.data)

        # check response status code and message
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # TESTING GET RANDOM QUESTIONS FOR THE QUIZ=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # CHECK IF QUESTIONS ARE UNIQUE=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

    def test_play_quiz(self):
        """Tests playing quiz game success"""

        # send post request with category and previous questions
        response = self.client().post('/quizzes', json={
            'previous_questions': [16, 17],
            'quiz_category': {'type': 'Geography', 'id': '3'}})

        # load response data
        data = json.loads(response.data)

        # check response status code and message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

        # check that a question is returned
        self.assertTrue(data['question'])

        # check that the question returned is in correct category
        self.assertEqual(data['question']['category'], 3)

        # check that question returned is not on previous q list
        self.assertNotEqual(data['question']['id'], 16)
        self.assertNotEqual(data['question']['id'], 17)

    def test_play_quiz_fails(self):
        """Tests playing quiz game failure 422"""

        # send post request without json data
        response = self.client().post('/quizzes', json={})

        # load response data
        data = json.loads(response.data)

        # check response status code and message
        self.assertEqual(response.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
