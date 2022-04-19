from django.shortcuts import render
from django.http import HttpResponse

from .models import Greeting
from pybit import usdt_perpetual


session = usdt_perpetual.HTTP(endpoint='https://api.bybit.com', api_key='...', api_secret='...')
ws = usdt_perpetual.WebSocket(test=False, api_key="...", api_secret="...")
# Get orderbook.
session.orderbook(symbol='LUNAUSDT')

# Create five long orders.
orders = [{
    "symbol": "LUNAUSDT",
    "order_type": "Limit",
    "side": "Buy",
    "qty": 100,
    "price": i,
    "time_in_force": "GoodTillCancel"
} for i in [5000, 5500, 6000, 6500, 7000]]

# Submit the orders in bulk.
session.place_active_order_bulk(orders)


# Check on your order and position through WebSocket.
def handle_orderbook(message):
    print(message)


def handle_position(message):
    print(message)

ws.orderbook_25_stream(handle_orderbook, "LUNAUSDT")
ws.position_stream(handle_position)

while True:
    # Run your main trading strategy here
    pass  # To avoid CPU utilisation, use time.sleep(1)

# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "index.html")


def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, "db.html", {"greetings": greetings})


# PyBit Methods
# user_trade_records()
# closed_profit_and_loss()
# get_wallet_balance()
# close_position()
# place_active_order()
# replace_active_order()
# place_conditional_order()
# get_conditional_order()
#