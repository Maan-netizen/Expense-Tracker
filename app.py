from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import json
import csv
import io
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)
DB = "expenses.db"

# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS expenses (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT    NOT NULL,
                amount    REAL    NOT NULL,
                category  TEXT    NOT NULL,
                date      TEXT    NOT NULL,
                note      TEXT    DEFAULT '',
                type      TEXT    NOT NULL DEFAULT 'expense'
            );
            CREATE TABLE IF NOT EXISTS budgets (
                category  TEXT PRIMARY KEY,
                amount    REAL NOT NULL
            );
        """)

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

# ── Expenses CRUD ─────────────────────────────────────────────────────────────

@app.route("/api/expenses", methods=["GET"])
def get_expenses():
    month  = request.args.get("month")   # YYYY-MM
    cat    = request.args.get("category")
    type_  = request.args.get("type")
    search = request.args.get("search", "")

    query  = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if month:
        query += " AND strftime('%Y-%m', date) = ?"
        params.append(month)
    if cat and cat != "All":
        query += " AND category = ?"
        params.append(cat)
    if type_ and type_ != "All":
        query += " AND type = ?"
        params.append(type_)
    if search:
        query += " AND (title LIKE ? OR note LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    query += " ORDER BY date DESC, id DESC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/expenses", methods=["POST"])
def add_expense():
    d = request.json
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO expenses (title, amount, category, date, note, type) VALUES (?,?,?,?,?,?)",
            (d["title"], float(d["amount"]), d["category"], d["date"], d.get("note", ""), d.get("type", "expense"))
        )
        row = conn.execute("SELECT * FROM expenses WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.route("/api/expenses/<int:eid>", methods=["PUT"])
def update_expense(eid):
    d = request.json
    with get_db() as conn:
        conn.execute(
            "UPDATE expenses SET title=?, amount=?, category=?, date=?, note=?, type=? WHERE id=?",
            (d["title"], float(d["amount"]), d["category"], d["date"], d.get("note", ""), d.get("type", "expense"), eid)
        )
        row = conn.execute("SELECT * FROM expenses WHERE id=?", (eid,)).fetchone()
    return jsonify(dict(row))

@app.route("/api/expenses/<int:eid>", methods=["DELETE"])
def delete_expense(eid):
    with get_db() as conn:
        conn.execute("DELETE FROM expenses WHERE id=?", (eid,))
    return jsonify({"deleted": eid})

# ── Analytics ─────────────────────────────────────────────────────────────────

@app.route("/api/analytics")
def analytics():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))

    with get_db() as conn:
        # totals
        totals = conn.execute("""
            SELECT type, SUM(amount) as total FROM expenses
            WHERE strftime('%Y-%m', date) = ? GROUP BY type
        """, (month,)).fetchall()

        # by category (expenses only)
        by_cat = conn.execute("""
            SELECT category, SUM(amount) as total FROM expenses
            WHERE strftime('%Y-%m', date) = ? AND type='expense'
            GROUP BY category ORDER BY total DESC
        """, (month,)).fetchall()

        # daily trend (last 30 days)
        trend = conn.execute("""
            SELECT date, SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense,
                          SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) as income
            FROM expenses
            WHERE date >= date('now','-29 days')
            GROUP BY date ORDER BY date
        """).fetchall()

        # monthly summary (last 6 months)
        monthly = conn.execute("""
            SELECT strftime('%Y-%m', date) as month,
                   SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense,
                   SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) as income
            FROM expenses
            WHERE date >= date('now','-180 days')
            GROUP BY month ORDER BY month
        """).fetchall()

        # budgets vs actuals
        budgets = conn.execute("SELECT * FROM budgets").fetchall()
        actuals = conn.execute("""
            SELECT category, SUM(amount) as total FROM expenses
            WHERE strftime('%Y-%m', date) = ? AND type='expense'
            GROUP BY category
        """, (month,)).fetchall()

    act_map = {r["category"]: r["total"] for r in actuals}
    budget_data = [{"category": b["category"], "budget": b["amount"],
                    "actual": act_map.get(b["category"], 0)} for b in budgets]

    totals_map = {r["type"]: r["total"] for r in totals}

    return jsonify({
        "totals":  totals_map,
        "by_cat":  [dict(r) for r in by_cat],
        "trend":   [dict(r) for r in trend],
        "monthly": [dict(r) for r in monthly],
        "budgets": budget_data,
    })

# ── Budgets ───────────────────────────────────────────────────────────────────

@app.route("/api/budgets", methods=["GET"])
def get_budgets():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM budgets").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/budgets", methods=["POST"])
def set_budget():
    d = request.json
    with get_db() as conn:
        conn.execute(
            "INSERT INTO budgets (category, amount) VALUES (?,?) ON CONFLICT(category) DO UPDATE SET amount=excluded.amount",
            (d["category"], float(d["amount"]))
        )
    return jsonify({"ok": True})

# ── Export CSV ────────────────────────────────────────────────────────────────

@app.route("/api/export")
def export_csv():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM expenses ORDER BY date DESC").fetchall()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ID", "Title", "Amount", "Category", "Date", "Note", "Type"])
    for r in rows:
        writer.writerow([r["id"], r["title"], r["amount"], r["category"], r["date"], r["note"], r["type"]])

    buf.seek(0)
    return send_file(
        io.BytesIO(buf.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="expenses.csv"
    )

# ── Seed demo data ─────────────────────────────────────────────────────────────

@app.route("/api/seed", methods=["POST"])
def seed():
    import random
    categories = ["Food", "Transport", "Shopping", "Health", "Entertainment", "Utilities", "Rent"]
    titles = {
        "Food": ["Grocery Store", "Restaurant", "Coffee Shop", "Food Delivery"],
        "Transport": ["Uber", "Bus Pass", "Fuel", "Parking"],
        "Shopping": ["Amazon", "Clothing", "Electronics", "Books"],
        "Health": ["Pharmacy", "Gym", "Doctor Visit", "Vitamins"],
        "Entertainment": ["Netflix", "Movie Tickets", "Concert", "Games"],
        "Utilities": ["Electricity Bill", "Internet Bill", "Water Bill", "Gas"],
        "Rent": ["Monthly Rent", "Maintenance"],
    }
    income_titles = ["Salary", "Freelance", "Bonus", "Investment Return"]
    today = datetime.now()
    records = []
    with get_db() as conn:
        for i in range(90):
            d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            for _ in range(random.randint(1, 4)):
                cat = random.choice(categories)
                title = random.choice(titles[cat])
                amount = round(random.uniform(10, 500), 2)
                conn.execute(
                    "INSERT INTO expenses (title, amount, category, date, note, type) VALUES (?,?,?,?,?,?)",
                    (title, amount, cat, d, "", "expense")
                )
            if i % 30 < 2:
                conn.execute(
                    "INSERT INTO expenses (title, amount, category, date, note, type) VALUES (?,?,?,?,?,?)",
                    (random.choice(income_titles), round(random.uniform(2000, 5000), 2), "Income", d, "", "income")
                )
        # default budgets
        for cat in categories:
            conn.execute(
                "INSERT INTO budgets (category, amount) VALUES (?,?) ON CONFLICT(category) DO NOTHING",
                (cat, round(random.uniform(300, 1500), 2))
            )
    return jsonify({"ok": True})

# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("\n✅  Expense Tracker running → http://localhost:5000\n")
    app.run(debug=True, port=5000)
