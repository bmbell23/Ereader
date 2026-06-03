"""Audiobook lifecycle + HLS-proxy tests.

Exercises the full playback path the WebView uses: start a session, confirm the
track URL was rewritten to the *backend's* CORS-clean HLS proxy (not raw ABS),
load the manifest and a .ts segment through that proxy, sync, then close.

Skipped wholesale when Audiobookshelf isn't configured (degraded Calibre-only
mode is a valid deployment).
"""
import unittest

import requests

from tests import _base as b


@unittest.skipUnless(b.abs_enabled(), 'Audiobookshelf not configured/enabled')
class TestAudiobookPlayback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.book = b.first_dual_book()
        if not cls.book:
            raise unittest.SkipTest('no matched (dual-format) audiobook found')
        cls.abs_id = cls.book['absId']
        cls.sid = None

    def setUp(self):
        # Each test starts its own session and tears it down so ABS sessions
        # don't leak.
        self.session = b.post(f'/audiobooks/{self.abs_id}/play').json()
        self.sid = self.session.get('id')
        self.addCleanup(self._close)

    def _close(self):
        if self.sid:
            try:
                b.post(f'/audiobooks/sessions/{self.sid}/close')
            except Exception:
                pass
            self.sid = None

    def _hls_track(self):
        for t in self.session.get('audioTracks') or []:
            if '.m3u8' in (t.get('contentUrl') or ''):
                return t
        return None

    def test_play_session_shape(self):
        self.assertTrue(self.sid)
        self.assertIsNotNone(self.session.get('playMethod'))
        self.assertTrue(self.session.get('audioTracks'))

    def test_track_url_points_at_backend_proxy(self):
        t = self._hls_track()
        if not t:
            self.skipTest('session is direct-play (no HLS track)')
        # Must be routed through THIS backend, never raw ABS (CORS + token hiding).
        self.assertIn('/api/audiobooks/hls/', t['contentUrl'])
        self.assertNotIn(':13378', t['contentUrl'])

    def test_manifest_loads_with_cors(self):
        t = self._hls_track()
        if not t:
            self.skipTest('session is direct-play (no HLS track)')
        r = requests.get(t['contentUrl'], timeout=b.TIMEOUT)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get('Access-Control-Allow-Origin'), '*')
        self.assertTrue(r.text.startswith('#EXTM3U'))

    def test_segment_streams_through_proxy(self):
        t = self._hls_track()
        if not t:
            self.skipTest('session is direct-play (no HLS track)')
        manifest = requests.get(t['contentUrl'], timeout=b.TIMEOUT).text
        segs = [ln.strip() for ln in manifest.splitlines()
                if ln.strip().endswith('.ts')]
        self.assertTrue(segs, 'manifest had no .ts segments')
        base = t['contentUrl'].rsplit('/', 1)[0]
        r = requests.get(base + '/' + segs[0], timeout=40)
        self.assertEqual(r.status_code, 200)
        self.assertIn('video/mp2t', r.headers.get('Content-Type', ''))
        self.assertGreater(len(r.content), 0)

    def test_sync_and_close(self):
        r = b.post(f'/audiobooks/sessions/{self.sid}/sync',
                   {'currentTime': 5, 'timeListened': 5, 'duration': 100})
        self.assertEqual(r.status_code, 200)
        c = b.post(f'/audiobooks/sessions/{self.sid}/close',
                   {'currentTime': 5, 'duration': 100})
        self.assertEqual(c.status_code, 200)
        self.assertTrue(c.json().get('ok'))
        self.sid = None  # already closed

    def test_audiobook_cover_proxy(self):
        r = b.get(f'/audiobooks/{self.abs_id}/cover')
        self.assertEqual(r.status_code, 200)
        self.assertIn('image', r.headers.get('Content-Type', ''))


if __name__ == '__main__':
    unittest.main()
