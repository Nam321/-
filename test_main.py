import unittest
import json
from main import app, db, User, Task


class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_register_user(self):

        data = {'email': 'test@example.com', 'password': 'testpassword'}
        response = self.app.post('/register', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)['message'], 'User registered successfully')

    def test_login_user(self):
        data = {'email': 'test@example.com', 'password': 'testpassword'}
        self.app.post('/register', data=json.dumps(data), content_type='application/json')
        response = self.app.post('/login', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', json.loads(response.data))


if __name__ == '__main__':
    unittest.main()
