import json
import threading
import time
from collections import defaultdict
from typing import Callable, NamedTuple, Any, Optional
from loguru import logger 
import websocket

from hl_research.hl_types import Subscription, WsMsg


ActiveSubscription = NamedTuple("ActiveSubscription", [("callback", Callable[[Any], None]), ("subscription_id", int)])


def subscription_to_identifier(subscription: Subscription) -> str:
    if subscription["type"] == "l2Book":
        return f'l2Book:{subscription["coin"].lower()}'
    elif subscription["type"] == "trades":
        return f'trades:{subscription["coin"].lower()}'

def ws_msg_to_identifier(ws_msg: WsMsg) -> Optional[str]:
    if ws_msg["channel"] == "pong":
        return "pong"
    elif ws_msg["channel"] == "l2Book":
        return f'l2Book:{ws_msg["data"]["coin"].lower()}'
    elif ws_msg["channel"] == "trades":
        trades = ws_msg["data"]
        if len(trades) == 0:
            return None
        else:
            return f'trades:{trades[0]["coin"].lower()}'


class WebsocketManager:
    def __init__(self, base_url):

        self.subscription_id_counter = 0
        self.ws_ready = False
        self.queued_subscriptions: list[tuple[Subscription, ActiveSubscription]] = []
        self.active_subscriptions: dict[str, list[ActiveSubscription]] = defaultdict(list)
        ws_url = "ws" + base_url[len("http") :] + "/ws"
        
        self.ws = websocket.WebSocketApp(ws_url, on_message=self.on_message, on_open=self.on_open)
        self.ping_sender = threading.Thread(target=self.send_ping, daemon=True)
        self.ws_runner = threading.Thread(target=self.ws.run_forever, daemon=True)

    def __enter__(self):
        self.ping_sender.start()
        self.ws_runner.start()
        return self
    
    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        self.ws.keep_running = False
        self.ping_sender.join()
        self.ws_runner.join()

    def send_ping(self):
        while self.ws.keep_running:
            time.sleep(50)
            logger.debug("Websocket sending ping")
            self.ws.send(json.dumps({"method": "ping"}))

    def on_message(self, _ws, message):
        if message == "Websocket connection established.":
            logger.debug(message)
            return
        logger.debug(f"on_message {message}")
        ws_msg: WsMsg = json.loads(message)
        identifier = ws_msg_to_identifier(ws_msg)
        if identifier == "pong":
            logger.debug("Websocket received pong")
            return
        if identifier is None:
            logger.debug("Websocket not handling empty message")
            return
        active_subscriptions = self.active_subscriptions[identifier]
        if len(active_subscriptions) == 0:
            print("Websocket message from an unexpected subscription:", message, identifier)
        else:
            for active_subscription in active_subscriptions:
                active_subscription.callback(ws_msg)

    def on_open(self, _ws):
        logger.debug("on_open")
        self.ws_ready = True
        for (subscription, active_subscription) in self.queued_subscriptions:
            self.subscribe(subscription, active_subscription.callback, active_subscription.subscription_id)

    def subscribe(
        self, subscription: Subscription, callback: Callable[[Any], None], subscription_id: Optional[int] = None
    ) -> int:
        if subscription_id is None:
            self.subscription_id_counter += 1
            subscription_id = self.subscription_id_counter
        if not self.ws_ready:
            logger.debug("enqueueing subscription")
            self.queued_subscriptions.append((subscription, ActiveSubscription(callback, subscription_id)))
        else:
            logger.debug("subscribing")
            identifier = subscription_to_identifier(subscription)
            self.active_subscriptions[identifier].append(ActiveSubscription(callback, subscription_id))
            self.ws.send(json.dumps({"method": "subscribe", "subscription": subscription}))
        return subscription_id

    def unsubscribe(self, subscription: Subscription, subscription_id: int) -> bool:
        if not self.ws_ready:
            raise NotImplementedError("Can't unsubscribe before websocket connected")
        identifier = subscription_to_identifier(subscription)
        active_subscriptions = self.active_subscriptions[identifier]
        new_active_subscriptions = [x for x in active_subscriptions if x.subscription_id != subscription_id]
        if len(new_active_subscriptions) == 0:
            self.ws.send(json.dumps({"method": "unsubscribe", "subscription": subscription}))
        self.active_subscriptions[identifier] = new_active_subscriptions
        return len(active_subscriptions) != len(active_subscriptions)
