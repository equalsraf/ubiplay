import unittest, json
from app import app

class TestNoMDP(unittest.TestCase):
    """
    Tests for when MPD is not present
    """
    
    def setUp(self):
        self.app = app.test_client()

    def test_frontpage(self):
        """Frontpage returns 200"""
        resp = self.app.get('/')
        self.assertEquals(resp.status_code, 200)

    def test_ws(self):
        """REST services return error object w/ code 503"""
        for rule in app.url_map.iter_rules():

            # ignore /stattic, and non-GET routes
            if rule.endpoint in ('static',):
                continue
            if rule.arguments:
                continue
            if not 'GET' in rule.methods:
                continue
            # / is the frontpage, skip it
            if rule.rule == '/':
                continue
            resp = self.app.get(rule.rule)
            self.assertEquals(resp.status_code, 503)

            # See python issue #10976
            data = json.loads(resp.data.decode(resp.charset or 'utf8'))
            self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main()

