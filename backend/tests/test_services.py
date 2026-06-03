"""Service / container reachability tests.

These FAIL (not skip) when a required service is down, because the whole point
is to verify the stack is up and talking: backend (:8091), static web server
(:8090), the Calibre Content Server, and — when configured — Audiobookshelf.
"""
import unittest

import requests

from tests import _base as b


class TestBackendService(unittest.TestCase):
    def test_health_ok_and_calibre_connected(self):
        r = b.get('/health')
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertEqual(j.get('status'), 'ok', msg=f'health degraded: {j}')
        self.assertTrue(j.get('calibre_connected'), 'Calibre not connected')
        self.assertTrue(j.get('version'))


class TestStaticServer(unittest.TestCase):
    def _ok_html(self, path):
        r = requests.get(b.STATIC + path, timeout=b.TIMEOUT)
        self.assertEqual(r.status_code, 200, msg=f'{path} -> {r.status_code}')
        return r

    def test_index_served(self):
        r = self._ok_html('/index.html')
        self.assertIn('text/html', r.headers.get('Content-Type', ''))

    def test_reader_served(self):
        self._ok_html('/reader.html')

    def test_player_assets_served(self):
        self._ok_html('/player.html')
        r = requests.get(b.STATIC + '/player.js', timeout=b.TIMEOUT)
        self.assertEqual(r.status_code, 200)
        self.assertIn('javascript', r.headers.get('Content-Type', '').lower())


class TestCalibreUpstream(unittest.TestCase):
    def test_library_info_reachable(self):
        r = requests.get(b.CALIBRE + '/ajax/library-info', timeout=b.TIMEOUT)
        self.assertEqual(r.status_code, 200)
        self.assertIn('library_map', r.json())


class TestAudiobookshelfUpstream(unittest.TestCase):
    def setUp(self):
        if not b.abs_enabled():
            self.skipTest('Audiobookshelf not configured/enabled')

    def test_abs_healthcheck_reachable(self):
        # ABS exposes an unauthenticated /healthcheck (older builds: /ping).
        last = None
        for path in ('/healthcheck', '/ping'):
            try:
                r = requests.get(b.ABS + path, timeout=b.TIMEOUT)
                if r.status_code == 200:
                    return
                last = r.status_code
            except requests.RequestException as e:
                last = e
        self.fail(f'ABS not reachable at {b.ABS} (/healthcheck, /ping): {last}')


if __name__ == '__main__':
    unittest.main()
