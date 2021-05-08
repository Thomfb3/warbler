"""Message View tests."""
import os
from unittest import TestCase

from models import db, connect_db, Message, User

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="password",
                                    image_url=None
                                    )

        self.testuser_id = 12345
        self.testuser.id = self.testuser_id 

        db.session.commit()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_add_message(self):
        """Can use add a message?"""
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
    


    def test_add_no_session(self):
        """Test add a message without session"""
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))


    
    def test_add_invalid_user(self):
        """Test add a message with invalid user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 999999999
                # user does not exist
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))



    def test_message_show(self):
        """Test showing a message"""        
        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser_id
            )

        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            m = Message.query.get(1234)

            resp = c.get(f'/messages/{m.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(m.text, str(resp.data))



    def test_invalid_message_show(self):
        """Test invalid message"""        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/messages/9999999')

            self.assertEqual(resp.status_code, 404)



    def test_delete_message(self):
        """Test delete message"""
        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser_id
            )

        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.post('/messages/1234/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            m = Message.query.get(1234)
            self.assertIsNone(m)



    def test_unauthorized_message_delete(self):
        """Test unauthorized message delete"""

        u2 = User.signup(username="testuser_two",
                        email="test_two@test.com",
                        password="password",
                        image_url=None
                        )
        u2.id = 98765

        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser_id
            )

        db.session.add_all([u2, m])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 98765
            
            resp = c.post('/messages/1234/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(1234)
            self.assertIsNotNone(m)

