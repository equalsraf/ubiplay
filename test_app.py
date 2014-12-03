import unittest
from app import app

class TestUbiPlayApp(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()

    def test_frontpage(self):
        """Frontpage returns 200"""
        resp = self.app.get('/')
        self.assertEquals(resp.status_code, 200)

if __name__ == '__main__':
    unittest.main()

