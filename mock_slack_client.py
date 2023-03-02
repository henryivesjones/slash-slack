#!/usr/bin/env python
import argparse
import json
import urllib.parse
import webbrowser
from concurrent.futures import ThreadPoolExecutor, wait
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

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

        th.submit(_shutdown_server)

    def log_request(self, _) -> None:
        return


tasks = []
th = ThreadPoolExecutor()
server = HTTPServer(("localhost", _CALLBACK_SERVER_PORT), CallbackHandler)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(dest="text", help="The text in the message.")
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
    return args.text, args.port, args.path


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
        print(f"Response visibility is {data['response_type']}")
        del data["response_type"]
    webbrowser.open_new_tab(f"{_BASE_URL}{urllib.parse.quote(json.dumps(data))}")


def _run_callback_server():
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def _send_message(port: int, path: str, data: dict):
    response = requests.post(f"http://localhost:{port}{path}", data=data)
    if response.status_code != 200:
        print("Receipt failed...")
        _shutdown_server()
        return
    if len(response.content) > 0:
        receipt_content = response.json()
        _open_slack_block_builder(receipt_content)
        _shutdown_server()


def _shutdown_server():
    server.shutdown()


text, port, path = _parse_args()

t_params = {**_BASE_PARAMS}
t_params["text"] = text


tasks.append(th.submit(_run_callback_server))
tasks.append(th.submit(_send_message, port, path, t_params))

wait(tasks)

th.shutdown()
