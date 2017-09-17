from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from flask import request

import datetime
import re
import uuid
import sys

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response



# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///car-configurator.db")

@app.route("/")
def index():
    cars = db.execute("SELECT * FROM cars")
    return render_template("index.html", cars=cars)

@app.route('/car/<int:car_id>')
def carConfig(car_id):
    car = db.execute("SELECT * FROM cars WHERE id =:car_id", car_id=car_id)
    optionCategories = db.execute("SELECT * FROM optionCategories WHERE carId =:car_id ORDER BY optionCategories.ordered ASC", car_id=car_id)
    options = db.execute("SELECT * FROM options")
    optionValues = db.execute("SELECT * FROM optionValues")
    return render_template("car.html", car=car[0], optionCategories=optionCategories, options=options, optionValues=optionValues)

@app.route("/result", methods=["POST"])
def result():
    results = dict(request.form)
    orderId = uuid.uuid4().hex[:6].upper()
    db.execute("INSERT INTO orders VALUES(:id, :car_id)", id=orderId, car_id=results["car"])

    for key, value in results.items():
        if key != "car":
            db.execute("INSERT INTO orderOptionValues VALUES(:order_id, :option_id, :option_value_id)", order_id=orderId, option_id=parseN(key), option_value_id=parseN(value[0]))

    return redirect(url_for("order", order_id=orderId))

@app.route("/order/<order_id>")
def order(order_id):
    order = db.execute("SELECT * FROM orders WHERE id =:order_id", order_id=order_id)[0]
    orderOptionValues = db.execute("SELECT * FROM orderOptionValues WHERE orderId =:order_id", order_id=order_id)

    car = db.execute("SELECT * FROM cars WHERE id =:car_id", car_id=order["carId"])[0]
    optionCategories = db.execute("SELECT * FROM optionCategories WHERE carId =:car_id ORDER BY optionCategories.ordered ASC", car_id=order["carId"])
    options = db.execute("SELECT * FROM options")
    optionValues = db.execute("SELECT * FROM optionValues")

    print(orderOptionValues, file=sys.stderr)

    return render_template("order.html", order=order, orderOptionValues=orderOptionValues, car=car, optionCategories=optionCategories, options=options, optionValues=optionValues)

def parseN(inputS):
    return ''.join(x for x in inputS if x.isdigit())
