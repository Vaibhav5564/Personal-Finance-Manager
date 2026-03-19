# this file is for helper functions
# anything reusable should come here


# -----------------------------
# CALCULATE TOTALS
# -----------------------------
# takes list of transactions and returns income, expense, balance
def calculate_totals(transactions):
    income = sum(t.amount for t in transactions if t.type == 'income')
    expense = sum(t.amount for t in transactions if t.type == 'expense')
    balance = income - expense

    return income, expense, balance


# -----------------------------
# FORMAT CURRENCY
# -----------------------------
# just to display amount nicely (₹ symbol + 2 decimal places)
def format_currency(amount):
    return f"₹{amount:,.2f}"


# -----------------------------
# FILTER BY CATEGORY
# -----------------------------
# useful if later you add filters in dashboard
def filter_by_category(transactions, category):
    return [t for t in transactions if t.category.lower() == category.lower()]


# -----------------------------
# GET RECENT TRANSACTIONS
# -----------------------------
# return latest N transactions (default 5)
def get_recent_transactions(transactions, limit=5):
    sorted_transactions = sorted(transactions, key=lambda x: x.date, reverse=True)
    return sorted_transactions[:limit]