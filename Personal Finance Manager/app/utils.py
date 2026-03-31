
# -----------------------------
# CALCULATE TOTALS
# -----------------------------
# takes list of transactions and returns income, expense, balance
def calculate_totals(transactions):
    income = sum(t.amount for t in transactions if t.type == 'income')
    expense = sum(t.amount for t in transactions if t.type == 'expense')
    balance = income - expense

    return income, expense, balance




