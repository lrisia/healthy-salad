import sys
from flask import Flask, current_app, request, abort
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from flask_openapi3 import APIBlueprint

from api.routes import ApiRouteInterface
from model.line_connection import LineConnection


class LineWebhookPostRoute(ApiRouteInterface):
    __line_connection: LineConnection

    def __init__(self, access_token: str, channel_secret: str):
        self.__line_connection = LineConnection(access_token, channel_secret)

    def register(self, app: APIBlueprint):
        @app.post("/callback")
        def callback():
            # get X-Line-Signature header value
            signature = request.headers["X-Line-Signature"]

            # get request body as text
            body = request.get_data(as_text=True)
            print("Request body: " + body)

            # handle webhook body
            try:
                self.__line_connection.handler.handle(body, signature)
            except InvalidSignatureError:
                current_app.logger.info(
                    "Invalid signature. Please check your channel access token/channel secret."
                )
                abort(400)

            return "OK", 200

        @self.__line_connection.handler.add(MessageEvent, message=TextMessageContent)
        def handle_message(event):
            with ApiClient(self.__line_connection.configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=event.message.text)],  # type: ignore
                    )
                )