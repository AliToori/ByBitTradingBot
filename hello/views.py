import json
import logging.config
import os
from time import sleep

import pandas as pd
from django.shortcuts import render
from pybit import usdt_perpetual
# from dotenv import load_dotenv
from .models import Greeting
from threading import Thread

# load_dotenv()

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    'formatters': {
        'colored': {
            '()': 'colorlog.ColoredFormatter',  # colored output
            # --> %(log_color)s is very important, that's what colors the line
            'format': '[%(asctime)s,%(lineno)s] %(log_color)s[%(message)s]',
            'log_colors': {
                'DEBUG': 'green',
                'INFO': 'cyan',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            },
        },
        'simple': {
            'format': '[%(asctime)s,%(lineno)s] [%(message)s]',
        },
    },
    "handlers": {
        "console": {
            "class": "colorlog.StreamHandler",
            "level": "INFO",
            "formatter": "colored",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": 'app-log.log'
        },
    },
    "root": {"level": "INFO",
             "handlers": ["console", "file"]
             }
})
LOGGER = logging.getLogger()

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")
symbol = os.getenv("SYMBOL")
client = usdt_perpetual.HTTP(endpoint='https://api-testnet.bybit.com', api_key=api_key, api_secret=api_secret)
ws = usdt_perpetual.WebSocket(test=False, api_key=api_key, api_secret=api_secret)

buy_price = 93.40
quantity = 1
take_profit = 95
stop_loss = 90
position = False
tp_order = None


def handle_execution(message):
    order = json.loads(json.dumps(message, indent=4))
    print(f'Execution Status: {order["data"][0]["order_status"]}')
    if order["data"][0]["order_status"] == "Filled":
        print(f'Placing buy limit TP/SL order')
        tp_order = client.place_active_order(
            symbol=symbol,
            side="Buy",
            order_type="Market",
            qty=quantity,
            # price=buy_price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            time_in_force="GoodTillCancel",
            reduce_only=False,
            close_on_trigger=False
        )
        tp_order = json.loads(json.dumps(tp_order, indent=4))['result']
        print(f"TP/SL limit order: {tp_order}")


# Check on your order and position through WebSocket.
def handle_order(message):
    order = json.loads(json.dumps(message, indent=4))
    print(f'Order Data: {order}')
    print(f'Order Status: {order["data"][0]["order_status"]}')
    if order["data"][0]["order_status"] == "Filled":
        print(f'Placing buy limit TP/SL order')
        tp_order = client.place_active_order(
            symbol=symbol,
            side="Buy",
            order_type="Market",
            qty=quantity,
            price=buy_price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            time_in_force="GoodTillCancel",
            reduce_only=False,
            close_on_trigger=False
        )
        tp_order = json.loads(json.dumps(tp_order, indent=4))['result']
        print(f"TP/SL limit order: {tp_order}")


def handle_trade(message):
    trade_data = json.loads(json.dumps(message, indent=4))
    trade_data = trade_data["data"]
    print(f'Trade Data: {trade_data}')


# Subscribe to the execution topics
def get_connected():
    # Subscribe to the execution topics
    # ws.trade_stream(callback=handle_trade, symbol=symbol)
    # ws.order_stream(handle_order)
    ws.execution_stream(handle_execution)
    # ws.position_stream(handle_position)
    print(f'Websocket connected')
    while True:
        sleep(1)


# Start WebSocket in a separate thread
Thread(target=get_connected).start()


# Create your views here.
def index(request):
    return render(request, "index.html")


def trades(request):
    # It needs to be able to receive a webhook post from Trading View, then it would place a limit order on Bybit.
    # After that it would subscribe to the executions topic, wait for the order to be filled, and when it's filled,
    # it would place Take Profit Limit Orders.
    if request.method == 'POST':
        account_balance = client.get_wallet_balance(coin='USDT')["result"]["USDT"]["wallet_balance"]
        print(f"Account Balance: {account_balance}")
        print(f'Request Post Data: {request.POST["buyprice"]}, {request.POST["takeprofit"]}, {request.POST["stoploss"]}')
        buy_price = float(request.POST["buyprice"])
        take_profit = float(request.POST["takeprofit"])
        stop_loss = float(request.POST["stoploss"])
        # quantity = round(account_balance / buy_price)
        quantity = 1
        order = client.place_active_order(
            symbol=symbol,
            side="Buy",
            order_type="Limit",
            qty=quantity,
            price=buy_price,
            time_in_force="GoodTillCancel",
            reduce_only=False,
            close_on_trigger=False
        )
        order = json.loads(json.dumps(order, indent=4))["result"]
        print(f"Buy Market order has been placed: {order}")
        order = {"order_id": order["order_id"], "symbol": order["symbol"], "side": order["side"],
                 "order_type": order["order_type"], "price": order["price"],
                 "qty": order["qty"], "order_status": order["order_status"], "created_time": order["created_time"]
                 }
        return render(request, 'trades.html', {"order": order})
    return render(request, 'trades.html')


def db(request):
    greeting = Greeting()
    greeting.save()
    greetings = Greeting.objects.all()
    return render(request, "db.html", {"greetings": greetings})
