import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

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
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
uri = os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://")
db = SQL(uri)

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    """return apology("TODO")"""
    # TODO: Display the entries in the database on index.html
    # get user cash total

    result = db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])
    cash = result[0]['cash']

    # pull all transactions belonging to user
    db.execute("DELETE FROM buy WHERE id=:id and shares=0", id=session["user_id"])
    portfolio = db.execute("SELECT price,symbol,name,shares FROM buy WHERE id=:id", id=session["user_id"])
    grand_total = cash

    # determine current price, stock total value and grand total value
    for stock in portfolio:
        price = lookup(stock['symbol'])['price']
        total = stock['shares'] * price
        grand_total += total
        stock.update({'price': usd(price), 'total': usd(total)})

    cash=usd(cash)
    grand_total=usd(grand_total)


    return render_template("index.html", stocks=portfolio, cash=cash, total=grand_total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    """return apology("TODO")"""
    if request.method == "POST":
        quote=request.form.get("symbol").upper()

        if lookup(quote)== None:
            return apology("Stock symbol not valid, please try again",400)

        while True:

            try:
                int(request.form.get("shares"))
            except (ValueError):
                return apology("must provide stock symbol and number of shares",400)
            else:
                break



        # ensure stock symbol and number of shares was submitted
        if (not request.form.get("symbol")) or (not request.form.get("shares")):
            return apology("must provide stock symbol and number of shares",400)

        # ensure number of shares is valid
        if int(request.form.get("shares")) <= 0:
            return apology("must provide valid number of shares (integer)")

        else:
            rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
            stock=lookup(quote)
            stockName={
                'name':stock['name'],
                'symbol':stock['symbol'],
                'price':stock['price']}
            cost=int(request.form.get("shares"))*int(stockName['price'])
            result= db.execute("SELECT cash FROM users WHERE id=:id",id=session["user_id"])
            if result[0]["cash"]>=cost:
                current= db.execute("SELECT name FROM buy WHERE name=:name and id=:id", name=stockName["name"],id=session["user_id"])
                if not current:
                    db.execute("INSERT INTO buy (id, shares, price, symbol,name) VALUES(?, ?, ?, ?,?)", session["user_id"], request.form.get("shares"),stockName['price'],stockName['symbol'],stockName['name'])
                    db.execute("UPDATE users SET cash=cash-:cost WHERE id=:id", cost=cost, id=session["user_id"]);
                    db.execute("INSERT INTO transactions (id, symbol, shares, price,transacted) VALUES(?, ?, ?, ?,?)", session["user_id"], stockName['symbol'],request.form.get("shares"),stockName['price'],datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    # Redirect user to home page
                    return redirect("/")

                else:
                    db.execute("UPDATE buy SET shares=shares+:shares WHERE id=:id", shares=int(request.form.get("shares")), id=session["user_id"]);
                    db.execute("UPDATE users SET cash=cash-:cost WHERE id=:id", cost=cost, id=session["user_id"]);
                    db.execute("INSERT INTO transactions (id, symbol, shares, price,transacted) VALUES(?, ?, ?, ?,?)", session["user_id"], stockName['symbol'],request.form.get("shares"),stockName['price'],datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    # Redirect user to home page
                    return redirect("/")

            else:
                return apology("You need more money", 400)





    else:
        return render_template("buy.html")





@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    """return apology("TODO")"""
    transact = db.execute("SELECT * FROM transactions WHERE id=:id", id=session["user_id"])
    return render_template("history.html", stocks=transact)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

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
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    """return apology("TODO")"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide symbol", 400)


        quote=request.form.get("symbol").upper()

        # check is valid stock name provided
        if lookup(quote)== None:
            return apology("Stock symbol not valid, please try again",400)

        # stock name is valid
        else:
            stock=lookup(quote)
            return render_template("quoted.html", stockName={
                'name':stock['name'],
                'symbol':stock['symbol'],
                'price':usd(stock['price'])
            })





    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    """return apology("TODO")"""

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username") or not request.form.get("password"):
            return apology("must provide username/password")


        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username doesnt exist and password is correct
        if len(rows) == 1 or  (request.form.get("password")!=request.form.get("confirmation")):
            return apology("invalid username and/or password")

        #Insert details into Database
        username = request.form.get("username")
        #Change password to hash
        passw = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        db.execute("INSERT INTO users (username,hash) VALUES(?,?)", username, passw)
        return redirect("/")

    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():

    """Sell shares of stock"""
    """return apology("TODO")"""
    if request.method == "POST":
        quote=request.form.get("symbol").upper()

        if not request.form.get("symbol") or not request.form.get("shares") or int(request.form.get("shares"))<0:
            return apology("must provide information correctly", 400)

        if lookup(quote)==None:
            return apology("Stock symbol not valid, please try again",400)

        else:
            rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
            available = db.execute("SELECT shares FROM buy WHERE :symbol=symbol and :id=id", symbol=request.form.get("symbol"),id=session["user_id"])
            if available[0]['shares']>=int(request.form.get("shares")):
                stock=lookup(quote)
                stockName={
                    'name':stock['name'],
                    'symbol':stock['symbol'],
                    'price':stock['price']}
                cost=int(request.form.get("shares"))*(stockName['price'])
                result = db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])
                db.execute("INSERT INTO sell (id, shares, price, symbol,name) VALUES(?, ?, ?, ?,?)", session["user_id"], request.form.get("shares"),stockName['price'],stockName['symbol'],stockName['name'])
                db.execute("UPDATE users SET cash=cash+:cost WHERE id=:id", cost=cost, id=session["user_id"]);
                db.execute("UPDATE buy SET shares=shares-:x WHERE symbol=:symbol and id=:id", x=int(request.form.get("shares")), symbol=request.form.get("symbol"),id=session["user_id"]);
                sold=-int(request.form.get("shares"))
                db.execute("INSERT INTO transactions (id, symbol, shares, price,transacted) VALUES(?, ?, ?, ?,?)", session["user_id"], stockName['symbol'],sold,stockName['price'],datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                # Redirect user to home page
                return redirect("/")
            else:
                return apology("must provide information correctly", 400)


    else:
        current= db.execute("SELECT symbol FROM buy WHERE id=?",session["user_id"])
        if not current:
            return apology("Nothing to sell",400)
        else:
            owned_stocks=list()
            for i in range(0,len(current)):
                owned_stocks.append(current[i]["symbol"])
            return render_template("sell.html",stocks=current)





def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
