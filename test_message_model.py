"""User model tests."""
import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u = User.signup(
            email="tester@test.com",
            username="tester",
            password="password",
            image_url=None
        )

        uid = 3333
        u.id = uid

        db.session.commit()
        u = User.query.get(uid)
        self.u = u
        self.uid = uid
        self.client = app.test_client()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


################# Basic Message Tests

    def test_message_model(self):
        """Does basic model work?"""

        msg = Message(
            text="Hello Everybody!",
            user_id=self.uid
        )

        msg_id = 123
        msg.id = msg_id

        db.session.add(msg)
        db.session.commit()

        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, 'Hello Everybody!')


    def test_message_repr(self):
        """Test message repr method"""
        msg = Message(
            text="Hello Everybody!",
            user_id=self.uid
        )

        msg_id = 123
        msg.id = msg_id

        db.session.add(msg)
        db.session.commit()

        m = Message.query.get(msg_id)
        
        self.assertEqual(m.__repr__(), f"<Message #{m.id}: {m.user_id}, {m.timestamp}>")
 

################# Message Likes

    def test_message_likes(self):
        """Test message likes"""

        m1 = Message(
            text="Hello Everybody!",
            user_id=self.uid
        )

        m2 = Message(
            text="Goodbye Everybody!",
            user_id=self.uid
        )

        u = User.signup("tester_two", "tester_two@test.com", "password", None)
        uid = 555
        u.id = uid

        db.session.add_all([m1, m2, u])
        db.session.commit()

        u.likes.append(m1)
        db.session.commit()

        l = Likes.query.filter(Likes.user_id == uid).all()
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0].message_id, m1.id)

