"""User model tests."""
import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup(
            email="userone@test.com",
            username="testuser1",
            password="HASHED_PASSWORD",
            image_url=None
        )

        u1id = 1111
        u1.id = u1id

        u2 = User.signup(
            email="usertwo@test.com",
            username="testuser2",
            password="HASHED_PASSWORD",
            image_url=None
        )

        u2id = 2222
        u2.id = u2id

        db.session.commit()

        u1 = User.query.get(u1id)
        u2 = User.query.get(u2id)

        self.u1 = u1
        self.u1id = u1id

        self.u2 = u2
        self.u2id = u2id

        self.client = app.test_client()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

################# Basic User Tests

    def test_user_model(self):
        """Does basic model work?"""
        # User should have no messages & no followers
        self.assertEqual(len(self.u1.messages), 0)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u2.messages), 0)
        self.assertEqual(len(self.u2.followers), 0)



    def test_user_repr(self):
        """Test user repr method"""
        self.assertEqual(self.u1.__repr__(), f"<User #{self.u1.id}: testuser1, userone@test.com>")
        self.assertEqual(self.u2.__repr__(), f"<User #{self.u2.id}: testuser2, usertwo@test.com>")

################# User Follows

    def test_user_follows(self):
        """Test user follows"""
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u2.followers), 1)

        self.assertEqual(self.u1.following[0].id, self.u2.id)
        self.assertEqual(self.u2.followers[0].id, self.u1.id)



    def test_is_following(self):
        """Test user is following"""
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(self.u1.is_following(self.u2), True)
        self.assertEqual(self.u2.is_following(self.u1), False)

    

    def test_is_follower(self):
        """Test user is a follower"""
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(self.u1.is_followed_by(self.u2), False)
        self.assertEqual(self.u2.is_followed_by(self.u1), True)

################# User SignUp

    def test_valid_signup(self):
        """Test user valid signup"""
        u_test = User.signup("tester", "tester@test.com", "password", None)
        uid = 9999
        u_test.id = uid
        db.session.commit()

        u_test = User.query.get(uid)

        self.assertIsNotNone(u_test)
        self.assertEqual(u_test.username, "tester")
        self.assertEqual(u_test.email, "tester@test.com")
        self.assertNotEqual(u_test.password, "password")
        self.assertTrue(u_test.password.startswith("$2b$"))


    def test_invalid_username_signup(self):
        """Test invalid username with user signup"""
        invalid = User.signup(None, 'tester@test.com', 'password', None)
        uid = 123456789
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_invalid_password_signup(self):
        """Test invalid email with user signup"""
        invalid = User.signup('tester', None, 'password', None)
        uid = 1234567
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_invalid_password_signup(self):
        """Test invalid password on user signup"""
        with self.assertRaises(ValueError) as context:
            User.signup('tester', 'tester@test.com', '', None)

        
################# User Authentication

    def test_valid_authenticate(self):

        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.u1id)

    def test_invalid_username(self):
        self.assertFalse(User.authenticate("notauser", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "wrongpassword"))



