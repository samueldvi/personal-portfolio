#!/usr/bin/env python3
"""Serve an isolated editorial admin build on localhost without request logs."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile

from build_admin import build, load_local_config


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Robots-Tag', 'noindex, nofollow')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description='Serve the private editorial preview on localhost')
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--env-file', type=Path, default=Path(__file__).with_name('.env.local'))
    args = parser.parse_args()
    config = load_local_config(args.env_file)
    with tempfile.TemporaryDirectory(prefix='editorial-admin-local-') as folder:
        output = build(Path(folder) / 'admin', config=config)
        handler = partial(QuietHandler, directory=str(output))
        with ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
            print(f'Editorial admin: http://127.0.0.1:{server.server_port}/', flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass


if __name__ == '__main__':
    main()
