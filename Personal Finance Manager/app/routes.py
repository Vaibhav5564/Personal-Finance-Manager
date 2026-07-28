from flask import Blueprint, render_template, redirect, url_for, flash, Response, request
from .models import User, Transaction
from .forms import RegisterForm, LoginForm, TransactionForm
from . import db
from .utils import calculate_totals
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import csv
from flask import session


# Blueprint
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
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegisterForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()

        if existing_user:
            flash('Email already exists. Please login.')
            return redirect(url_for('main.login'))

        hashed_password = generate_password_hash(form.password.data)

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
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

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
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
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

        # Get current user's transactions
        transactions = Transaction.query.filter_by(user_id=current_user.id).all()

        income = sum(t.amount for t in transactions if t.type == 'income')
        expense = sum(t.amount for t in transactions if t.type == 'expense')

        new_amount = form.amount.data

        #  BLOCK NEGATIVE BALANCE
        if form.type.data == 'expense' and (expense + new_amount > income):
            remaining = income - expense
            flash(f'❌ Insufficient balance! You only have ₹{remaining}', 'danger')
            return render_template('dashboard/add_transaction.html', form=form)

        #  SAVE TRANSACTION
        new_transaction = Transaction(
            type=form.type.data,
            amount=new_amount,
            category=form.category.data,
            description=form.description.data,
            user_id=current_user.id
        )

        db.session.add(new_transaction)
        db.session.commit()

        flash('Transaction added successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('dashboard/add_transaction.html', form=form)


# -----------------------------
# EDIT TRANSACTION
# -----------------------------
@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    transaction = Transaction.query.get_or_404(id)

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

    if transaction.user_id != current_user.id:
        flash('Unauthorized action!')
        return redirect(url_for('main.dashboard'))

    db.session.delete(transaction)
    db.session.commit()

    flash('Transaction deleted.')
    return redirect(url_for('main.dashboard'))

# -----------------------------
# EXPORT CSV
# -----------------------------
@main.route('/export')
@login_required
def export():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    def generate():
        yield 'Date,Type,Category,Amount,Description\n'
        for t in transactions:
            yield f'{t.date.strftime("%Y-%m-%d")},{t.type},{t.category},{t.amount},{t.description}\n'

    return Response(
        generate(),
        mimetype='teTxt/csv',
        headers={"Content-Disposition": "attachment;filename=transactions.csv"}
    )

# -----------------------------
# VISUALIZE
# -----------------------------
@main.route('/visualize')
@login_required
def visualize():

    transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    income = sum(t.amount for t in transactions if t.type == 'income')
    expense = sum(t.amount for t in transactions if t.type == 'expense')

    balance = income - expense

    return render_template(
        'dashboard/visualize.html',
        expense=expense,
        balance=balance
    )

# -----------------------------
# ERROR HANDLERS
# -----------------------------
@main.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main.app_errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500


from flask_login import current_user
from flask import request, redirect, url_for

@main.before_app_request
def restrict_access():
    if not current_user.is_authenticated:

        allowed_routes = [
            'main.login',
            'main.register',
            'main.admin_login',      # Allow admin login page
            'main.admin_dashboard',  # Optional
            'main.admin_logout',     # Optional
            'static'
        ]

        
        if request.endpoint not in allowed_routes:
            return redirect(url_for('main.login'))


@main.route('/monthly', methods=['GET', 'POST'])
@login_required
def monthly_report():

    from datetime import datetime

    income = 0
    expense = 0
    balance = 0

    if request.method == 'POST':
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')

        if from_date and to_date:
            from_date = datetime.strptime(from_date, '%Y-%m-%d')
            to_date = datetime.strptime(to_date, '%Y-%m-%d')

            transactions = Transaction.query.filter(
                Transaction.user_id == current_user.id,
                Transaction.date >= from_date,
                Transaction.date <= to_date
            ).all()

            income = sum(t.amount for t in transactions if t.type == 'income')
            expense = sum(t.amount for t in transactions if t.type == 'expense')
            balance = income - expense

        else:
            flash("Please select both dates!", "warning")

    return render_template(
        'dashboard/monthly.html',
        income=income,
        expense=expense,
        balance=balance
    )

# -----------------------------
# ADMIN DASHBOARD
# -----------------------------



@main.route('/admin/login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        password = request.form.get('password')

        if password == "vaibhav0722":

            session['admin'] = True

            return redirect(url_for('main.admin_dashboard'))

        else:

            flash("Invalid Admin Password", "danger")

    return render_template("admin/admin_login.html")

@main.route('/admin/dashboard')
def admin_dashboard():

    if not session.get("admin"):

        return redirect(url_for('main.admin_login'))

    users = User.query.all()

    transactions = Transaction.query.all()

    return render_template(
        "admin/admin_dashboard.html",
        users=users,
        transactions=transactions
    )


@main.route('/admin/logout')
def admin_logout():

    session.pop("admin", None)

    flash("Admin logged out successfully.")

    return redirect(url_for("main.admin_login"))