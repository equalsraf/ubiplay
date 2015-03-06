import unittest, json
from app import app

class TestVLC(unittest.TestCase):
    """
    Tests for when VLC is running
    """

    def setUp(self):
        self.app = app.test_client()

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
            resp = self.app.get(rule.rule)
            self.assertEquals(resp.status_code, 200, rule.rule)

    def post(self, path, data):
        return self.app.post(path, data=json.dumps(data), content_type='application/json')

    def testvol(self):
        self.post('/setvol', dict(volume=50))
        resp = self.app.get('/status')
        data = json.loads(resp.data.decode(resp.charset or 'utf8'))
        self.assertEquals(data['volume'], 50)


if __name__ == '__main__':
    unittest.main()

