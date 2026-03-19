from . import db
from flask_login import UserMixin
from datetime import datetime


# -----------------------------
# USER TABLE
# -----------------------------
# This table stores all user-related data like login info
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    # basic user info
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # relationship with transactions (one user → many transactions)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


# -----------------------------
# TRANSACTION TABLE
# -----------------------------
# This table stores income and expense records
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # what type → income or expense
    type = db.Column(db.String(10), nullable=False)

    # amount of money
    amount = db.Column(db.Float, nullable=False)

    # category like food, travel, salary etc
    category = db.Column(db.String(100), nullable=False)

    # optional note for better tracking
    description = db.Column(db.String(200))

    # auto timestamp when entry is created
    date = db.Column(db.DateTime, default=datetime.utcnow)

    # linking transaction to a specific user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Transaction {self.type} - {self.amount}>"