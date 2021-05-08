"""User View tests."""
import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False



class UserViewTestCase(TestCase):
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

        self.u1 = User.signup("Tom", "test1@test.com", "password", None)
        self.u1_id = 111
        self.u1.id = self.u1_id

        self.u2 = User.signup("John", "test2@test.com", "password", None)
        self.u2_id = 222
        self.u2.id = self.u2_id

        self.u3 = User.signup("Bob", "test3@test.com", "password", None)
        self.u3_id = 333
        self.u3.id = self.u3_id

        self.u4 = User.signup("Jack", "test4@test.com", "password", None)
        self.u4_id = 444
        self.u4.id = self.u4_id

        db.session.commit()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_user_index(self):
        """Test user index"""
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@Tom", str(resp.data))
            self.assertIn("@John", str(resp.data))    
            self.assertIn("@Bob", str(resp.data))
            self.assertIn("@Jack", str(resp.data))
            self.assertIn("@testuser", str(resp.data))            


    def test_users_search(self):
        """Test Users Search"""
        with self.client as c:
            resp = c.get("/users?q=test")

            self.assertIn("@testuser", str(resp.data))
         
            self.assertNotIn("@Tom", str(resp.data))
            self.assertNotIn("@Bob", str(resp.data))
            self.assertNotIn("@Jack", str(resp.data))
            self.assertNotIn("@John", str(resp.data))   



    def test_user_show(self):
        """Test User Show"""
        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))


    def setup_likes(self):
        """Setup Like"""
        m1 = Message(text="trending warble", user_id=self.testuser_id)
        m2 = Message(text="Eating some lunch", user_id=self.testuser_id)
        m3 = Message(id=9876, text="likable warble", user_id=self.u1_id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.testuser_id, message_id=9876)

        db.session.add(l1)
        db.session.commit()



    def test_add_like(self):
        """Test Add Like"""
        m = Message(id=1984, text="The earth is round", user_id=self.u1_id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post("/users/add_like/1984", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==1984).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)



    def test_remove_like(self):
        """Test Remove Like"""
        self.setup_likes()

        m = Message.query.filter(Message.text=="likable warble").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.testuser_id)

        l = Likes.query.filter(
            Likes.user_id==self.testuser_id and Likes.message_id==m.id
        ).one()

        # Now we are sure that testuser likes the message "likable warble"
        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post(f"/users/delete_like/{m.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            # the like has been deleted
            self.assertEqual(len(likes), 0)



    def test_unauthenticated_like(self):
        """Test Unauthenticated Like"""
        self.setup_likes()

        m = Message.query.filter(Message.text=="likable warble").one()
        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/users/add_like/{m.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))

            # The number of likes has not changed since making the request
            self.assertEqual(like_count, Likes.query.count())




    def setup_followers(self):
        """Setup Followers"""
        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()



    def test_show_following(self):
        """Test show following"""
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/following")
            self.assertEqual(resp.status_code, 200)

            self.assertIn("@Tom", str(resp.data))
            self.assertIn("@John", str(resp.data))
            self.assertNotIn("@Bob", str(resp.data))
            self.assertNotIn("@Jack", str(resp.data))



    def test_show_followers(self):
        """Test show followers"""
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/followers")

            self.assertIn("@Tom", str(resp.data))
            self.assertNotIn("@John", str(resp.data))
            self.assertNotIn("@Bob", str(resp.data))
            self.assertNotIn("@Jack", str(resp.data))



    def test_unauthorized_following_page_access(self):
        """Test unauthorized following page access"""
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@Tom", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))



    def test_unauthorized_followers_page_access(self):
        """Test unauthorized followers page access"""
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@Tom", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))
