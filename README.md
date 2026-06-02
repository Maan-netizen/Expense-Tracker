# 💸 Spendr — Advanced Expense Tracker

A full-stack expense tracker built with **Python Flask** + **vanilla JS**, featuring a sleek dark UI, real-time charts, budget management, and CSV export.

## ✨ Features

| Feature | Details |
|---|---|
| 📊 Dashboard | Live stats, 30-day trend, category doughnut, monthly bar chart |
| 📋 Transactions | Add / Edit / Delete, search, filter by month · category · type |
| 🎯 Budgets | Set per-category limits with live progress bars |
| ⬇ CSV Export | One-click full export of all transactions |
| ⚡ Demo Data | Seed 90 days of realistic sample data instantly |
| 🌑 Dark UI | Minimal dark theme with Chart.js visualizations |

## 🚀 Quick Start

```bash
# 1. Clone & enter
git clone https://github.com/<your-username>/expense-tracker.git
cd expense-tracker

# 2. Install dependencies  (Python 3.8+)
pip install -r requirements.txt

# 3. Run
python app.py

# 4. Open in browser
#    http://localhost:5000
```

> **Tip:** Click **⚡ Load Demo Data** in the sidebar to instantly populate 90 days of sample transactions.

## 📁 Project Structure

```
expense-tracker/
├── app.py              ← Flask backend (REST API + SQLite)
├── requirements.txt    ← pip dependencies
├── expenses.db         ← auto-created SQLite database
└── templates/
    └── index.html      ← single-page UI (HTML + CSS + JS)
```

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/expenses` | List expenses (filter: month, category, type, search) |
| POST | `/api/expenses` | Create expense |
| PUT | `/api/expenses/<id>` | Update expense |
| DELETE | `/api/expenses/<id>` | Delete expense |
| GET | `/api/analytics` | Dashboard stats & chart data |
| GET | `/api/budgets` | Get all budgets |
| POST | `/api/budgets` | Set/update a budget |
| GET | `/api/export` | Download expenses as CSV |
| POST | `/api/seed` | Load demo data |

## 🛠 Tech Stack

- **Backend:** Python 3 · Flask · SQLite3
- **Frontend:** Vanilla JS · Chart.js 4 · Google Fonts (Syne + DM Mono)
- **Storage:** SQLite (auto-created, zero config)

## 📸 Pages

- **Dashboard** — KPI cards + 3 interactive charts
- **Transactions** — Full CRUD table with search & filters
- **Budgets** — Set limits, see colour-coded progress bars

---
Made with 💜 — MIT License
