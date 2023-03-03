#!/usr/bin/env python
import argparse
import asyncio
import json
import urllib.parse
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, HTTPServer

import aiohttp

_CALLBACK_SERVER_PORT = 9863
_BASE_PARAMS = {
    "token": "gIkuvaNzQIHg97ATvDxqgjtO",
    "team_id": "T0001",
    "team_domain": "example",
    "enterprise_id": "E0001",
    "enterprise_name": "Example Corp",
    "channel_id": "C2147483705",
    "channel_name": "test",
    "user_id": "U2147483697",
    "user_name": "John Doe",
    "command": "/slash_slack",
    "text": None,
    "response_url": f"http://localhost:{_CALLBACK_SERVER_PORT}",
    "trigger_id": "13345224609.738474920.8088930838d88f008e0",
    "api_app_id": "A123456",
}

_BASE_URL = "https://app.slack.com/block-kit-builder/#"


class CallbackHandler(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        _open_slack_block_builder(data=json.loads(post_data.decode()))
        self._set_response()

    def log_request(self, _) -> None:
        return


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port",
        default=9002,
        type=int,
        help="The port which the SlashSlack server is running.",
    )
    parser.add_argument(
        "--path",
        default="/slash_slack",
        help="The path which the SlashSlack server is listening.",
    )

    args = parser.parse_args()
    return args.port, args.path


_CALLBACK_SERVER_PORT = 9863
_BASE_PARAMS = {
    "token": "gIkuvaNzQIHg97ATvDxqgjtO",
    "team_id": "T0001",
    "team_domain": "example",
    "enterprise_id": "E0001",
    "enterprise_name": "Example Corp",
    "channel_id": "C2147483705",
    "channel_name": "test",
    "user_id": "U2147483697",
    "user_name": "John Doe",
    "command": "/slash-slack",
    "text": None,
    "response_url": f"http://localhost:{_CALLBACK_SERVER_PORT}",
    "trigger_id": "13345224609.738474920.8088930838d88f008e0",
    "api_app_id": "A123456",
}

_BASE_URL = "https://app.slack.com/block-kit-builder/#"


def _open_slack_block_builder(data: dict):
    if "response_type" in data:
        del data["response_type"]
    webbrowser.open(f"{_BASE_URL}{urllib.parse.quote(json.dumps(data))}", new=0)


def _run_callback_server(server: HTTPServer):
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


async def _send_message(port: int, path: str, data: dict):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"http://localhost:{port}{path}",
            data=data,
        ) as resp:
            if resp.status != 200:
                print("Receipt failed...")
                return
            if resp.content_length == 0:
                return
            receipt_content = await resp.json()
            _open_slack_block_builder(receipt_content)


def main():
    with ThreadPoolExecutor() as th:
        port, path = _parse_args()
        tasks = []
        server = HTTPServer(("localhost", _CALLBACK_SERVER_PORT), CallbackHandler)
        tasks.append(th.submit(_run_callback_server, server))

        t_params = {**_BASE_PARAMS}
        try:
            while True:
                msg = input("MSG: ")
                t_params["text"] = msg
                asyncio.run(_send_message(port, path, t_params))
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
