import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
from datetime import date

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd   #Makes the format easier to look like usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)                                #store sessions on local disk instead of digital cookies (Flask's default)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")





#AFTER FINISH< TRY MAKE THE STOCK PRICE UPDATE LIVE ON WEBSITE USING AJAX (DO THIS FOR FINAL PROJECT)




@app.route("/")
@login_required    #Ensure login route is successfully executed first
def index():

    ticker = db.execute("SELECT ticker, SUM(shares) FROM transactions GROUP BY ticker")
    db.execute("INSERT INTO indexes (userid, ticker, name, shares, price, total) VALUES(?, ?, ?, ?, ?, ?)", session["user_id"], "none", "none", 0, 0, 0)
    home = db.execute("SELECT ticker FROM indexes")
    for i in ticker:
        counter = 0
        symbol = i.get("ticker")
        shares = i.get("SUM(shares)")
        info = lookup(symbol)
        price = info.get("price")
        name = info.get("name")
        total = shares * price

        print(symbol, shares, total)
        for z in home:
            if symbol == z.get("ticker"):
                counter = counter + 1


        if counter == 0:
            db.execute("INSERT INTO indexes (userid, ticker, name, shares, price, total) VALUES(?, ?, ?, ?, ?, ?)", session["user_id"], symbol, name, shares, price, total)

        elif counter == 1:
            db.execute("UPDATE indexes SET shares = ?, price = ?, total = ? WHERE ticker = ?", shares, price, total, symbol)


    indexes = db.execute("SELECT ticker, name, shares, price, total FROM indexes WHERE userid = ? GROUP BY ticker", session["user_id"])
    cash = float(db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"])
    stock = db.execute("SELECT total FROM indexes WHERE userid = ? GROUP BY ticker", session["user_id"])
    value = 0
    for s in stock:
        value = value + float(s.get("total"))

    total = cash + value

    #new companies bought and sold are not being counted on index homepage
    #stop creating new rows in database when there is no action occured


    return render_template("index.html", indexes=indexes, cash=cash, total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        session["symbol2"] = request.form.get("symbol").upper()
        session["shares"] = request.form.get("shares")
        if not session["symbol2"]:
            return apology("must provide symbol", 403)
        if not session["shares"]:
            return apology("must provide shares", 403)
        if int(session["shares"]) < 1:
            return apology("must purchase at least 1 share", 403)

        session["info2"] = lookup(session["symbol2"])
        if session["info2"] == None:
            return apology("symbol does not exist")


        session["price"] = session["info2"].get("price")
        session["company"] = session["info2"].get("name")
        session["pay"] = session["price"] * float(session["shares"])
        session["cash"] = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
        session["date"] = date.today()


        if session["cash"] >= session["pay"]:
            session["cash"] = session["cash"] - session["pay"]
            db.execute("INSERT INTO transactions (userid, ticker, name, shares, price, date, total) VALUES(?, ?, ?, ?, ?, ?, ?)", session["user_id"], session["symbol2"], session["company"], session["shares"], session["price"], session["date"], session["pay"])
            db.execute("UPDATE users SET cash = ? WHERE id = ?", session["cash"], session["user_id"])

            return render_template("bought.html")

        if session["cash"] < session["pay"]:
            return render_template("broke.html")


                                                                 #inform the user stock has been purchased
                                                                 #how to build another table in SQL
                                                                 #table needs to include ticker, shares, price, user(user_id), date,remaining cash
                                                                 #CREATE TABLE transactions (id INTEGER, userid INTEGER, ticker TEXT NOT NULL, name TEXT NOT NULL, shares NUMERIC NOT NULL, price NUMERIC NOT NULL, date TEXT NOT NULL, total NUMERIC, PRIMARY KEY(id));
    else:
        return render_template("buy.html")



@app.route("/history")
@login_required
def history():

    history = db.execute("SELECT ticker, shares, price, total, date FROM transactions WHERE userid = ?", session["user_id"])
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        session["symbol"] = request.form.get("symbol").upper()
        session["info"] = lookup(session["symbol"])
        if session["info"] == None:
            return apology("Cannot find symbol", 403)
        return render_template("quoted.html")
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Ensure username was submitted
        session["username"] = request.form.get("username")
        if not session["username"]:
            return apology("must provide username", 403)


        # Ensure password was submitted
        session["password"] = request.form.get("password")

        if not session["password"]:
            return apology("must provide password", 403)

        session["confirmation"] = request.form.get("confirmation")
        if not session["confirmation"]:
            return apology("must confirm password", 403)

        if session["confirmation"] != session["password"]:
            return apology("Passwords do not match", 403)


        hash = generate_password_hash(session["password"])

        rows = db.execute("SELECT * FROM users WHERE username = ?", session["username"])
        if len(rows) != 0:
            exist = 1
            session["exist"] = exist
            return apology("username already exists", 403)


        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", session["username"], hash)
        return redirect("/login")

    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():

    if request.method == "POST":
        session["symbol3"] = request.form.get("Symbol").upper()
        session["shares2"] = request.form.get("shares")
        print(session["shares2"])
        if not session["symbol3"]:
            return apology("must provide symbol", 403)
        if not session["shares2"]:
            return apology("must provide shares", 403)
        if int(session["shares2"]) < 1:
            return apology("must sell at least 1 share", 403)

        shares = db.execute("SELECT SUM(shares) FROM transactions WHERE ticker = ?", session["symbol3"])[0]["SUM(shares)"]
        if int(session["shares2"]) > shares:
           return apology("Does not own enough shares", 403)

        session["info3"] = lookup(session["symbol3"])

        session["price2"] = session["info3"].get("price")
        session["company2"] = session["info3"].get("name")
        session["earn"] = session["price2"] * float(session["shares2"])
        session["cash2"] = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
        session["date2"] = date.today()

        session["cash2"] = session["cash2"] + session["earn"]
        db.execute("INSERT INTO transactions (userid, ticker, name, shares, price, date, total) VALUES(?, ?, ?, ?, ?, ?, ?)", session["user_id"], session["symbol3"], session["company2"], -abs(int(session["shares2"])), session["price2"], session["date2"], -abs(session["earn"]))
        db.execute("UPDATE users SET cash = ? WHERE id = ?", session["cash2"], session["user_id"])
        return render_template("sold.html")

    else:
        indexes = db.execute("SELECT ticker, name, SUM(shares), price, total FROM transactions GROUP BY ticker")
        return render_template("sell.html", indexes=indexes)




def errorhandler(e):

    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
