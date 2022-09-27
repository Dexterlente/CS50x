import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    symbol = db.execute("SELECT symbol FROM portfolio WHERE user_id = ? AND shares <> 0", session.get("user_id"))
    portfolio = []

    for row in symbol:
        quote = lookup(row["symbol"])
        shares = db.execute("SELECT shares FROM portfolio WHERE symbol = ?", row["symbol"])
        quote["shares"] = shares[0]["shares"]
        quote["total"] = shares[0]["shares"] * quote["price"]
        portfolio.append(quote)

    total = sum([item['total'] for item in portfolio])

    cash = db.execute("SELECT cash FROM users WHERE id = ?", session.get("user_id"))

    return render_template("index.html", portfolio=portfolio, cash=cash, total=total)

@app.route("/addcash", methods=["GET", "POST"])
@login_required
def addcash():

    user_id = session["user_id"]
    row = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    cash_in_hand = float(row[0]["cash"])

    if request.method == "GET":
        return render_template("addcash.html", cash_in_hand=cash_in_hand)

    else:
        amount = float(request.form.get("cash"))
        updated_cash = cash_in_hand + amount

        db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_cash, user_id)
        flash("Cash Added!")
        return redirect("/")

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":

        if not request.form.get("symbol"):
            return apology("Must provide symbol")

        if not request.form.get("shares"):
            return apology("Must provide number of shares")

        if not request.form.get("shares").isdigit():
            return apology("Must provide valid number of shares")

        quote = lookup(request.form.get("symbol"))

        if quote:
            shares = request.form.get("shares")
            total = int(shares) * quote["price"]
            cash = db.execute("SELECT cash FROM users WHERE id = ?", session.get("user_id", None))

            if cash[0]["cash"] >= total:

                db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", total, session.get("user_id", None))

                db.execute("INSERT INTO transactions(user_id, symbol, shares, price) VALUES (?, ?, ?, ?)",
                           session.get("user_id", None), quote["symbol"], shares, quote["price"])

                port_symbol = db.execute("SELECT symbol FROM portfolio WHERE user_id = ?", session.get("user_id", None))
                form_symbol = {"symbol": (request.form.get("symbol")).upper()}

                if form_symbol in port_symbol:
                    db.execute("UPDATE portfolio SET shares = shares + ? WHERE symbol = ?",
                               request.form.get("shares"), (request.form.get("symbol")).upper())

                else:
                    db.execute("INSERT INTO portfolio(user_id, symbol, shares) VALUES (?, ?, ?)",
                               session.get("user_id", None), quote["symbol"], shares)

                flash("Bought!")
                return redirect("/")

            else:
                return apology("Not enough balance")

        else:
            return apology("Symbol does not exist")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ?", session.get("user_id", None))

    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username")

        elif not request.form.get("password"):
            return apology("must provide password")

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password")

        session["user_id"] = rows[0]["id"]

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Must provide symbol")

        quote = lookup(request.form.get("symbol"))

        if quote:
            # Store information and send it to webpage
            name = quote["name"]
            symbol = quote["symbol"]
            price = quote["price"]

            return render_template("quoted.html", name=name, symbol=symbol, price=price)

        else:
            return apology("Symbol does not exist")

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method =="GET":
        return render_template("register.html")

    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("You Must Give a Username")

        if not password:
            return apology("You Must Give a Password")

        if not confirmation:
            return apology("You Must Confirm Your Password")

        if password != confirmation:
            return apology("Passwords Do Not Match")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) == 1:
            return apology("Username already in use")

        hash = generate_password_hash(request.form.get("password"))

        db.execute("INSERT INTO users(username, hash) VALUES (?, ?)", username, hash)

        user = db.execute("SELECT * FROM users WHERE username = ?", username)
        session["user_id"] = user[0]["id"]

        flash("Registered!")
        return redirect("/")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Must provide symbol")

        if not request.form.get("shares"):
            return apology("Must provide number of shares")

        quote = lookup(request.form.get("symbol"))
        total = int(request.form.get("shares")) * quote["price"]

        port_shares = db.execute("SELECT shares FROM portfolio WHERE user_id = ? AND symbol = ?",
                                 session.get("user_id"), (request.form.get("symbol")).upper())

        if port_shares[0]["shares"] >= int(request.form.get("shares")):

            db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", total, session.get("user_id", None))

            db.execute("INSERT INTO transactions(user_id, symbol, shares, price) VALUES (?, ?, -?, ?)",
                       session.get("user_id", None), quote["symbol"], request.form.get("shares"), quote["price"])

            db.execute("UPDATE portfolio SET shares = shares - ? WHERE symbol = ?",
                       request.form.get("shares"), (request.form.get("symbol")).upper())

            flash("Sold!")
            return redirect("/")

        else:
            return apology("Not enough shares in portfolio")

    else:
        symbols = db.execute("SELECT symbol FROM portfolio WHERE user_id = ? AND shares <> 0", session.get("user_id"))
        return render_template("sell.html", symbols=symbols)