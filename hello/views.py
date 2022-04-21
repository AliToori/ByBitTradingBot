import logging.config
import os
from pathlib import Path

import pandas as pd
from django.shortcuts import render
from pybit import usdt_perpetual

from .models import Greeting


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

PROJECT_ROOT = Path(os.path.abspath(os.path.dirname(__file__)))
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")
symbol = os.getenv("SYMBOL")
session = usdt_perpetual.HTTP(endpoint='https://api-testnet.bybit.com', api_key=api_key, api_secret=api_secret)
ws = usdt_perpetual.WebSocket(test=False, api_key=api_key, api_secret=api_secret)


# Check on your order and position through WebSocket.
def handle_position(message):
    df = pd.DataFrame([message])
    df = df.loc[:, ['E', 's', 'c']]
    df.columns = ['Time', 'Symbol', 'Price']
    df["Price"] = df["Price"].astype(float)
    df["Time"] = pd.to_datetime(df["Time"], unit='ms')
    file_path = str(PROJECT_ROOT / f'{symbol}.csv')
    df.to_csv(file_path, index=False)


# Create your views here.
def index(request):
    return render(request, "index.html")


def trades(request):

    # {{plot_7}} {{plot_8}} {{plot_4}}
    # buyprice takeprofit stoploss
    if request.method == 'POST':
        account_balance = session.get_wallet_balance()
        LOGGER.info(f"Account Balance: {account_balance}")
        order_data = {
            "Symbol": request.POST["symbol"],
            "BuyPrice": request.POST["buyprice"],
            "TakeProfit": request.POST["takeprofit"],
            "StopLoss": request.POST["stoploss"]
        }
        quantity = round(account_balance / order_data["BuyPrice"])
        buy_order = session.place_conditional_order(
            symbol=symbol,
            order_type="Limit",
            side="Buy",
            qty=quantity,
            price=order_data["BuyPrice"],
            base_price=order_data["BuyPrice"],
            stop_px=order_data["BuyPrice"],
            time_in_force="GoodTillCancel",
            order_link_id="cus_order_id_1",
            reduce_only=False,
            close_on_trigger=False,
        )
        LOGGER.info(f"Buy Order has been placed: {buy_order}")
        # Subscribe to the execution topic
        ws.position_stream(handle_position)
        # return render(request, 'trades.html', {"order_data": order_data})
    order_data = {
        "symbol": "LUNAUSDT",
        "price": 5
    }
    return render(request, 'trades.html', {"order_data": order_data})


def db(request):
    greeting = Greeting()
    greeting.save()
    greetings = Greeting.objects.all()
    return render(request, "db.html", {"greetings": greetings})
