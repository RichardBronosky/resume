"""Regression tests for review isolation and the command entrypoint."""

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

TOOLS = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


commands = module('commands', TOOLS / 'commands.py')
review_server = module('review_server', TOOLS / 'review-server.py')


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.state = patch.object(commands, 'STATE', self.directory)
        self.state.start()
        self.addCleanup(self.state.stop)

    def test_make_rejects_variable_command_injection(self):
        with patch.object(commands, 'run') as run:
            for args in (['make', 'SHELL=sh'], ['make', '-f', '/tmp/evil'],
                         ['make', 'VERSION=$(touch bad)']):
                with self.assertRaises(RuntimeError):
                    commands.main(args)
            run.assert_not_called()

    def test_existing_route_is_reused_but_not_owned(self):
        route = {'Web': {'host:8765': {'Handlers': {'/': {'Proxy': commands.LOCAL}}}}}
        with patch.object(commands, 'serve_config', return_value=route), patch.object(commands, 'run') as run:
            self.assertEqual(commands.ensure_route(), 'https://host:8765' + commands.PAGE)
            run.assert_not_called()
            self.assertFalse(commands.read('route.json')['created'])

    def test_unrelated_route_and_public_funnel_are_rejected(self):
        for proxy, public in (('http://127.0.0.1:9999', False), (commands.LOCAL, True)):
            route = {'Web': {'host:8765': {'Handlers': {'/': {'Proxy': proxy}}}},
                     'AllowFunnel': {'host:8765': public}}
            with patch.object(commands, 'serve_config', return_value=route), patch.object(commands, 'run') as run:
                with self.assertRaises(RuntimeError): commands.ensure_route()
                run.assert_not_called()

    def test_stop_preserves_preexisting_route_and_foreign_process(self):
        commands.write('route.json', {'created': False, 'host': 'host:8765'})
        commands.write('server.json', {'pid': 123, 'token': 'foreign'})
        with patch.object(commands, 'run') as run, patch.object(commands, 'server_owned', return_value=False), patch.object(commands.os, 'kill') as kill:
            commands.stop()
            run.assert_not_called()
            kill.assert_not_called()

    def test_changed_route_is_not_deleted(self):
        commands.write('route.json', {'created': True, 'host': 'host:8765'})
        changed = {'Web': {'host:8765': {'Handlers': {'/': {'Proxy': 'http://other'}}}}}
        with patch.object(commands, 'serve_config', return_value=changed), patch.object(commands, 'run') as run:
            with self.assertRaises(RuntimeError): commands.stop()
            run.assert_not_called()

    def test_reused_tab_number_does_not_grant_ownership(self):
        with patch.object(commands, 'browser_tabs', return_value=[{'tabId': 't3', 'targetId': 'NEW'}]):
            self.assertIsNone(commands.owned_tab('mobile', {'id': 't3', 'target': 'OLD'}))

    def test_stop_removes_only_matching_owned_route(self):
        commands.write('route.json', {'created': True, 'host': 'host:8765'})
        config = {'Web': {'host:8765': {'Handlers': {'/': {'Proxy': commands.LOCAL}}},
                          'host:443': {'Handlers': {'/': {'Proxy': 'http://unrelated'}}}}}
        with patch.object(commands, 'serve_config', return_value=config), patch.object(commands, 'run') as run:
            commands.stop()
            run.assert_called_once_with('tailscale', 'serve', '--https=8765', 'off')

    def test_failed_demo_check_still_prepares_review_handoff(self):
        with patch.object(commands, 'html'), patch.object(commands, 'public_check'), \
             patch.object(commands, 'start'), patch.object(commands, 'open_tab'), \
             patch.object(commands, 'layout_check', side_effect=RuntimeError('overflow')), \
             patch.object(commands, 'themes_check') as themes, \
             patch.object(commands, 'screenshot') as screenshots, \
             patch.object(commands, 'review_url', return_value='https://review.example'):
            with self.assertRaisesRegex(RuntimeError, 'Demo is ready'):
                commands.review(['demo'])
            themes.assert_called_once()
            self.assertEqual([call.args[0] for call in screenshots.call_args_list], ['wide', 'mobile'])

    def test_public_check_detects_injected_html(self):
        (self.directory / 'build').mkdir()
        artifact = self.directory / 'build/index.html'
        with patch.object(commands, 'ROOT', self.directory):
            artifact.write_text('<html>resume</html>')
            commands.public_check()
            artifact.write_text('<script src="/__review/diagnostics.js"></script>')
            with self.assertRaises(RuntimeError): commands.public_check()

    def test_entrypoint_works_from_another_directory(self):
        result = subprocess.run([str(TOOLS.parent / 'tools.sh'), 'help'],
                                cwd=self.directory, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('review demo', result.stdout)


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        (root / 'build').mkdir()
        (root / 'tools').mkdir()
        self.original = b'<html><body>resume</body></html>'
        self.artifact = root / 'build/bruno.bronosky.resume.html'
        self.artifact.write_bytes(self.original)
        (root / 'tools/review-diagnostics.js').write_text('// private diagnostics')
        self.root_patch = patch.object(review_server, 'ROOT', root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.config = root / 'config.json'
        self.config.write_text('{"diagnostics": false}')
        self.server = review_server.ThreadingHTTPServer(('127.0.0.1', 0), review_server.Handler)
        self.server.config_path = self.config
        self.server.owner_token = 'test-owner'
        self.server.report_path = root / 'reports.jsonl'
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def get(self, path):
        return urllib.request.urlopen(self.url + path, timeout=3)

    def test_default_is_clean_and_diagnostics_are_response_only(self):
        with self.get('/bruno.bronosky.resume.html?review=old') as response:
            self.assertEqual(response.read(), self.original)
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get('/__review/diagnostics.js')
        error.exception.close()
        self.config.write_text('{"diagnostics": true}')
        with self.get('/bruno.bronosky.resume.html') as response:
            self.assertIn(b'/__review/diagnostics.js', response.read())
        self.assertEqual(self.artifact.read_bytes(), self.original)
        self.config.write_text('{"diagnostics": false}')
        with self.get('/bruno.bronosky.resume.html') as response:
            self.assertEqual(response.read(), self.original)

    def test_reports_require_enabled_diagnostics_and_same_origin(self):
        def post(origin):
            req = urllib.request.Request(self.url + '/__review/report', b'{"reason":"manual"}',
                                         headers={'Origin': origin})
            return urllib.request.urlopen(req, timeout=3)
        with self.assertRaises(urllib.error.HTTPError) as error: post(self.url)
        self.assertEqual(error.exception.code, 404)
        error.exception.close()
        self.config.write_text('{"diagnostics": true}')
        with self.assertRaises(urllib.error.HTTPError) as error: post('https://unrelated.example')
        self.assertEqual(error.exception.code, 403)
        error.exception.close()
        with post(self.url) as response: self.assertEqual(response.status, 204)
        self.assertEqual(json.loads(self.server.report_path.read_text())['reason'], 'manual')


if __name__ == '__main__':
    unittest.main()
