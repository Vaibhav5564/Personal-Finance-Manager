from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo


# -----------------------------
# REGISTER FORM
# -----------------------------
# used when a new user signs up
class RegisterForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=100)]
    )

    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6)]
    )

    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password')]
    )

    submit = SubmitField('Register')


# -----------------------------
# LOGIN FORM
# -----------------------------
# used for existing users
class LoginForm(FlaskForm):
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )

    submit = SubmitField('Login')


# -----------------------------
# TRANSACTION FORM
# -----------------------------
# used to add income or expense
class TransactionForm(FlaskForm):

    # dropdown for selecting type
    type = SelectField(
        'Type',
        choices=[('income', 'Income'), ('expense', 'Expense')],
        validators=[DataRequired()]
    )

    amount = FloatField(
        'Amount',
        validators=[DataRequired()]
    )

    category = StringField(
        'Category',
        validators=[DataRequired()]
    )

    description = TextAreaField(
        'Description (optional)'
    )

    submit = SubmitField('Add Transaction')