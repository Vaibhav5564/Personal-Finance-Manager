from flask import Blueprint, render_template, redirect, url_for, flash
from .models import User, Transaction
from .forms import RegisterForm, LoginForm, TransactionForm
from . import db
from .utils import calculate_totals
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Blueprint setup
main = Blueprint('main', __name__)


# -----------------------------
# HOME
# -----------------------------
@main.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))


# -----------------------------
# REGISTER
# -----------------------------
@main.route('/register', methods=['GET', 'POST'])
def register():
    # if already logged in → go dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegisterForm()

    if form.validate_on_submit():
        # check existing email
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already exists. Please login.')
            return redirect(url_for('main.login'))

        # hash password
        hashed_password = generate_password_hash(form.password.data)

        # create new user
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please login.')
        return redirect(url_for('main.login'))

    return render_template('auth/register.html', form=form)


# -----------------------------
# LOGIN
# -----------------------------
@main.route('/login', methods=['GET', 'POST'])
def login():
    # if already logged in → skip login
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # validate credentials
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password.')

    return render_template('auth/login.html', form=form)


# -----------------------------
# LOGOUT
# -----------------------------
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('main.login'))


# -----------------------------
# DASHBOARD
# -----------------------------
@main.route('/dashboard')
@login_required
def dashboard():
    # fetch user's transactions
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    # calculate totals using utils
    income, expense, balance = calculate_totals(transactions)

    return render_template(
        'dashboard/dashboard.html',
        transactions=transactions,
        income=income,
        expense=expense,
        balance=balance
    )


# -----------------------------
# ADD TRANSACTION
# -----------------------------
@main.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    form = TransactionForm()

    if form.validate_on_submit():
        new_transaction = Transaction(
            type=form.type.data,
            amount=form.amount.data,
            category=form.category.data,
            description=form.description.data,
            user_id=current_user.id
        )

        db.session.add(new_transaction)
        db.session.commit()

        flash('Transaction added successfully!')
        return redirect(url_for('main.dashboard'))

    return render_template('dashboard/add_transaction.html', form=form)


# -----------------------------
# EDIT TRANSACTION
# -----------------------------
@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    transaction = Transaction.query.get_or_404(id)

    # security check (very important)
    if transaction.user_id != current_user.id:
        flash('Unauthorized access!')
        return redirect(url_for('main.dashboard'))

    form = TransactionForm(obj=transaction)

    if form.validate_on_submit():
        transaction.type = form.type.data
        transaction.amount = form.amount.data
        transaction.category = form.category.data
        transaction.description = form.description.data

        db.session.commit()

        flash('Transaction updated successfully!')
        return redirect(url_for('main.dashboard'))

    return render_template('dashboard/edit_transaction.html', form=form)


# -----------------------------
# DELETE TRANSACTION
# -----------------------------
@main.route('/delete/<int:id>')
@login_required
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)

    # security check
    if transaction.user_id != current_user.id:
        flash('Unauthorized action!')
        return redirect(url_for('main.dashboard'))

    db.session.delete(transaction)
    db.session.commit()

    flash('Transaction deleted.')
    return redirect(url_for('main.dashboard'))


# -----------------------------
# ERROR HANDLERS
# -----------------------------
@main.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@main.app_errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500