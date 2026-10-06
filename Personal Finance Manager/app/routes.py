from flask import Blueprint, render_template, redirect, url_for, flash, Response, request
from .models import User, Transaction
from .forms import RegisterForm, LoginForm, TransactionForm
from . import db
from .utils import calculate_totals
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import csv
from flask import session
from collections import defaultdict

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER

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
    form = RegisterForm()

    if form.validate_on_submit():

        # Check if username OR email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) |
            (User.email == form.email.data)
        ).first()

        if existing_user:
            flash(
                "Username or email already used. Please choose another.",
                "danger"
            )
            return render_template(
                "auth/register.html",
                form=form
            )

        # Create new user
        hashed_password = generate_password_hash(
            form.password.data
        )

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )

        db.session.add(new_user)

        try:
            db.session.commit()

            flash(
                "Registration successful! You can now login.",
                "success"
            )

            return redirect(url_for('main.login'))

        except Exception:
            db.session.rollback()

            flash(
                "Something went wrong while creating your account. Please try again.",
                "danger"
            )

    return render_template(
        "auth/register.html",
        form=form
    )


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

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).all()

    income, expense, balance = calculate_totals(transactions)

    # --------------------------------
    # SMART FINANCIAL INSIGHTS
    # --------------------------------

    insights = []

    # 1. Savings / Financial Status
    if income > 0:
        savings_percentage = (balance / income) * 100
        expense_percentage = (expense / income) * 100

        if balance > 0:
            insights.append(
                f"💰 You have saved ₹{balance:.2f}, "
                f"which is {savings_percentage:.1f}% of your income."
            )
        else:
            insights.append(
                "⚠️ Your expenses are equal to or greater than your income."
            )

        # 2. Expense percentage
        insights.append(
            f"📊 You have spent {expense_percentage:.1f}% "
            f"of your total income."
        )

    # 3. Highest spending category
    category_expenses = defaultdict(float)

    for t in transactions:
        if t.type == 'expense':
            category_expenses[t.category] += t.amount

    if category_expenses:
        highest_category = max(
            category_expenses,
            key=category_expenses.get
        )

        highest_amount = category_expenses[highest_category]

        insights.append(
            f"🏆 Your highest spending category is "
            f"{highest_category} (₹{highest_amount:.2f})."
        )

        # 4. Spending advice
        if expense > 0:
            category_percentage = (
                highest_amount / expense
            ) * 100

            if category_percentage >= 40:
                insights.append(
                    f"💡 {highest_category} accounts for "
                    f"{category_percentage:.1f}% of your expenses. "
                    f"Consider reviewing this category."
                )
            else:
                insights.append(
                    "👍 Your expenses are reasonably distributed "
                    "across different categories."
                )

    return render_template(
        'dashboard/dashboard.html',
        transactions=transactions,
        income=income,
        expense=expense,
        balance=balance,
        insights=insights
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
# VISUALIZATION
# -----------------------------

@main.route('/visualize')
@login_required
def visualize():

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date.asc()).all()

    # -----------------------------
    # BASIC TOTALS
    # -----------------------------

    income = sum(
        t.amount for t in transactions
        if t.type == 'income'
    )

    expense = sum(
        t.amount for t in transactions
        if t.type == 'expense'
    )

    balance = income - expense

    # -----------------------------
    # CATEGORY-WISE EXPENSE
    # -----------------------------

    category_expenses = {}

    for t in transactions:

        if t.type == 'expense':

            category = t.category or "Other"

            if category not in category_expenses:
                category_expenses[category] = 0

            category_expenses[category] += t.amount

    # -----------------------------
    # MONTHLY DATA
    # -----------------------------

    monthly_income = {}
    monthly_expense = {}

    for t in transactions:

        month = t.date.strftime("%b %Y")

        if t.type == 'income':

            monthly_income[month] = (
                monthly_income.get(month, 0) + t.amount
            )

        elif t.type == 'expense':

            monthly_expense[month] = (
                monthly_expense.get(month, 0) + t.amount
            )

    # Keep months in chronological order
    months = sorted(
        set(monthly_income.keys()) |
        set(monthly_expense.keys()),
        key=lambda x: __import__('datetime').datetime.strptime(
            x, "%b %Y"
        )
    )

    income_data = [
        monthly_income.get(month, 0)
        for month in months
    ]

    expense_data = [
        monthly_expense.get(month, 0)
        for month in months
    ]

    return render_template(
        'dashboard/visualize.html',

        income=income,
        expense=expense,
        balance=balance,

        transaction_count=len(transactions),

        category_labels=list(category_expenses.keys()),
        category_values=list(category_expenses.values()),

        months=months,
        income_data=income_data,
        expense_data=expense_data
    )

    balance = income - expense

    return render_template(
        'dashboard/visualize.html',
        income=income,
        expense=expense,
        balance=balance,
        transactions=transactions
    )

# -----------------------------
# RECORDS
# -----------------------------

@main.route('/records')
@login_required
def records():

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date.desc()).all()

    income, expense, balance = calculate_totals(transactions)

    return render_template(
        'dashboard/records.html',
        transactions=transactions,
        income=income,
        expense=expense,
        balance=balance,
        record_type='all'
    )


# -----------------------------
# INCOME RECORDS
# -----------------------------

@main.route('/records/income')
@login_required
def income_records():

    transactions = Transaction.query.filter_by(
        user_id=current_user.id,
        type='income'
    ).order_by(Transaction.date.desc()).all()

    income = sum(t.amount for t in transactions)
    expense = 0
    balance = income

    return render_template(
        'dashboard/records.html',
        transactions=transactions,
        income=income,
        expense=expense,
        balance=balance,
        record_type='income'
    )


# -----------------------------
# EXPENSE RECORDS
# -----------------------------

@main.route('/records/expense')
@login_required
def expense_records():

    transactions = Transaction.query.filter_by(
        user_id=current_user.id,
        type='expense'
    ).order_by(Transaction.date.desc()).all()

    expense = sum(t.amount for t in transactions)
    income = 0
    balance = -expense

    return render_template(
        'dashboard/records.html',
        transactions=transactions,
        income=income,
        expense=expense,
        balance=balance,
        record_type='expense'
    )


# -----------------------------
# DOWNLOAD RECORDS PDF
# -----------------------------

@main.route('/records/pdf/<record_type>')
@login_required
def records_pdf(record_type):

    if record_type == 'income':

        transactions = Transaction.query.filter_by(
            user_id=current_user.id,
            type='income'
        ).order_by(Transaction.date.desc()).all()

        title = "Income Records"

    elif record_type == 'expense':

        transactions = Transaction.query.filter_by(
            user_id=current_user.id,
            type='expense'
        ).order_by(Transaction.date.desc()).all()

        title = "Expense Records"

    else:

        transactions = Transaction.query.filter_by(
            user_id=current_user.id
        ).order_by(Transaction.date.desc()).all()

        title = "All Transaction Records"

    income, expense, balance = calculate_totals(transactions)

    pdf_buffer = BytesIO()

    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    title_style = styles['Title']
    title_style.alignment = TA_CENTER

    elements = []

    # -----------------------------
    # TITLE
    # -----------------------------

    elements.append(
        Paragraph(
            "PERSONAL FINANCE MANAGER",
            title_style
        )
    )

    elements.append(
        Spacer(1, 5)
    )

    elements.append(
        Paragraph(
            title,
            styles['Heading2']
        )
    )

    elements.append(
        Spacer(1, 15)
    )

    # -----------------------------
    # USER INFORMATION
    # -----------------------------

    elements.append(
        Paragraph(
            f"<b>User:</b> {current_user.username}",
            styles['Normal']
        )
    )

    elements.append(
        Paragraph(
            f"<b>Email:</b> {current_user.email}",
            styles['Normal']
        )
    )

    elements.append(
        Spacer(1, 15)
    )

    # -----------------------------
    # SUMMARY
    # -----------------------------

    summary_data = [
        ["Financial Summary", "Amount"],
        ["Income", f"Rs. {income:.2f}"],
        ["Expense", f"Rs. {expense:.2f}"],
        ["Balance", f"Rs. {balance:.2f}"]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[300, 150]
    )

    summary_table.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ])
    )

    elements.append(summary_table)

    elements.append(
        Spacer(1, 20)
    )

    # -----------------------------
    # TRANSACTIONS
    # -----------------------------

    elements.append(
        Paragraph(
            "Transaction History",
            styles['Heading2']
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    transaction_data = [
        [
            "Date",
            "Type",
            "Category",
            "Amount",
            "Description"
        ]
    ]

    for t in transactions:

        transaction_data.append([
            t.date.strftime("%d-%m-%Y"),
            t.type.title(),
            t.category or "-",
            f"Rs. {t.amount:.2f}",
            t.description or "-"
        ])

    if len(transaction_data) == 1:

        transaction_data.append([
            "-",
            "-",
            "No records",
            "-",
            "-"
        ])

    transaction_table = Table(
        transaction_data,
        colWidths=[65, 55, 75, 75, 180],
        repeatRows=1
    )

    transaction_table.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 5)
        ])
    )

    elements.append(transaction_table)

    elements.append(
        Spacer(1, 15)
    )

    elements.append(
        Paragraph(
            f"<b>Total Records:</b> {len(transactions)}",
            styles['Normal']
        )
    )

    document.build(elements)

    pdf_buffer.seek(0)

    return Response(
        pdf_buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            "Content-Disposition":
            f"attachment; filename={record_type}_records.pdf"
        }
    )

# -----------------------------
# SMART FINANCIAL INSIGHTS
# -----------------------------

@main.route('/insights')
@login_required
def insights():

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).all()

    income, expense, balance = calculate_totals(transactions)

    insights = []

    # --------------------------------
    # NO TRANSACTIONS
    # --------------------------------

    if not transactions:

        insights.append(
            "💡 Add some income and expense transactions "
            "to start receiving personalized financial insights."
        )

        return render_template(
            'insights.html',
            insights=insights
        )


    # --------------------------------
    # INCOME ANALYSIS
    # --------------------------------

    if income > 0:

        savings_percentage = (balance / income) * 100
        expense_percentage = (expense / income) * 100

        # Savings
        if balance > 0:

            insights.append(
                f"💰 You have saved ₹{balance:.2f}, "
                f"which is {savings_percentage:.1f}% "
                f"of your total income."
            )

        else:

            insights.append(
                "⚠️ Your expenses are equal to or greater "
                "than your income. Try reducing unnecessary expenses."
            )


        # Expense percentage
        insights.append(
            f"📊 You have spent {expense_percentage:.1f}% "
            f"of your total income."
        )


        # --------------------------------
        # SAVINGS HEALTH
        # --------------------------------

        if savings_percentage >= 50:

            insights.append(
                "🌟 Excellent! You are maintaining a strong "
                "savings rate. Keep up the good financial discipline."
            )

        elif savings_percentage >= 20:

            insights.append(
                "👍 Your savings rate is healthy. "
                "Continue maintaining your current spending habits."
            )

        elif savings_percentage > 0:

            insights.append(
                "⚠️ Your savings rate is relatively low. "
                "Consider reducing unnecessary expenses."
            )

        else:

            insights.append(
                "🚨 You currently have no positive savings. "
                "Try to keep your expenses below your income."
            )


    # --------------------------------
    # CATEGORY ANALYSIS
    # --------------------------------

    category_expenses = defaultdict(float)

    for t in transactions:

        if t.type == 'expense':

            category = t.category or "Other"

            category_expenses[category] += t.amount


    if category_expenses:

        highest_category = max(
            category_expenses,
            key=category_expenses.get
        )

        highest_amount = category_expenses[
            highest_category
        ]


        # Highest spending category
        insights.append(
            f"🏆 Your highest spending category is "
            f"{highest_category}, with total expenses of "
            f"₹{highest_amount:.2f}."
        )


        # Category percentage
        if expense > 0:

            category_percentage = (
                highest_amount / expense
            ) * 100


            if category_percentage >= 40:

                insights.append(
                    f"💡 {highest_category} represents "
                    f"{category_percentage:.1f}% of your total "
                    f"expenses. Consider reviewing your spending "
                    f"in this category."
                )

            elif category_percentage >= 25:

                insights.append(
                    f"📌 {highest_category} represents "
                    f"{category_percentage:.1f}% of your expenses. "
                    f"Keep an eye on this category."
                )

            else:

                insights.append(
                    "👍 Your expenses are reasonably distributed "
                    "across different categories."
                )


    # --------------------------------
    # TRANSACTION ANALYSIS
    # --------------------------------

    total_transactions = len(transactions)

    insights.append(
        f"🧾 You currently have "
        f"{total_transactions} recorded transaction"
        f"{'s' if total_transactions != 1 else ''}."
    )


    # --------------------------------
    # FINANCIAL RECOMMENDATION
    # --------------------------------

    if income > 0:

        recommended_saving = income * 0.20

        if balance < recommended_saving:

            insights.append(
                f"🎯 A useful target could be saving at least "
                f"₹{recommended_saving:.2f}, which is 20% of "
                f"your income."
            )

        else:

            insights.append(
                "🎯 You are currently saving at least 20% "
                "of your income. Keep maintaining this habit."
            )


    # --------------------------------
    # RENDER PAGE
    # --------------------------------

    return render_template(
        'insights.html',
        insights=insights
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

    # Get all users and transactions
    users = User.query.all()
    transactions = Transaction.query.all()

    # -----------------------------
    # DASHBOARD STATISTICS
    # -----------------------------

    total_users = User.query.count()
    total_transactions = Transaction.query.count()

    # Total income
    total_income = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.type == 'income'
    ).scalar() or 0

    # Total expenses
    total_expense = db.session.query(
        db.func.sum(Transaction.amount)
    ).filter(
        Transaction.type == 'expense'
    ).scalar() or 0

    # Balance
    total_balance = total_income - total_expense

    # Income transaction count
    income_transactions = Transaction.query.filter_by(
        type='income'
    ).count()

    # Expense transaction count
    expense_transactions = Transaction.query.filter_by(
        type='expense'
    ).count()

    # Recent users
    recent_users = User.query.order_by(
        User.id.desc()
    ).limit(5).all()

    # Recent transactions
    recent_transactions = Transaction.query.order_by(
        Transaction.date.desc()
    ).limit(10).all()

    return render_template(
        "admin/admin_dashboard.html",
        users=users,
        transactions=transactions,

        total_users=total_users,
        total_transactions=total_transactions,
        total_income=total_income,
        total_expense=total_expense,
        total_balance=total_balance,

        income_transactions=income_transactions,
        expense_transactions=expense_transactions,

        recent_users=recent_users,
        recent_transactions=recent_transactions
    )


@main.route('/admin/logout')
def admin_logout():

    session.pop("admin", None)

    flash("Admin logged out successfully.")

    return redirect(url_for("main.admin_login"))