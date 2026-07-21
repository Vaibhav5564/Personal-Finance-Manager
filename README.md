# 💰 Personal Finance Manager

A web-based Personal Finance Manager built using **Python Flask** that helps users track their income, expenses, and financial transactions in one place.

The application provides a secure authentication system, transaction management, and an easy-to-use dashboard for monitoring personal finances.

---

## 🚀 Features

- 🔐 User Registration & Login Authentication
- 👤 Secure Password Hashing
- 💵 Add Income & Expense Transactions
- 📋 View Transaction History
- ✏️ Edit Existing Transactions
- 🗑️ Delete Transactions
- 📊 Dashboard with Financial Summary
- 💾 SQLite Database Integration
- 🔒 Session Management
- 🚫 Protected Routes (Login Required)
- ⚡ Flash Messages for User Feedback

---

## 🛠️ Tech Stack

### Frontend
- HTML5
- CSS3
- Bootstrap 5
- Jinja2 Templates

### Backend
- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Werkzeug Security

### Database
- SQLite

---

## 📂 Project Structure

```
Personal-Finance-Manager/
│
├── app/
│   ├── static/
│   ├── templates/
│   ├── models.py
│   ├── forms.py
│   ├── routes.py
│   └── __init__.py
│
├── instance/
│   └── finance.db
│
├── config.py
├── main.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### Clone the repository

```bash
git clone https://github.com/vaibhav5564/Personal-Finance-Manager.git
```

### Move into project directory

```bash
cd Personal-Finance-Manager
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
python main.py
```

Open:

```
http://127.0.0.1:5000
```

---

## 🔒 Security Features

- Passwords are securely hashed before storage.
- User sessions are protected using Flask-Login.
- Unauthorized users cannot access protected pages.
- Duplicate usernames and email addresses are prevented.
- Cache-Control headers are configured to prevent browser back-button access after logout.

---



## 📌 Future Enhancements

- 📈 Expense Analytics with Charts
- 📊 Monthly Budget Planning
- 💳 Multiple Account Support
- 📅 Export Transactions to PDF/Excel
- 🔍 Search & Filter Transactions
- 🌙 Dark Mode
- 📱 Responsive Mobile Dashboard

---

## 👨‍💻 Author

**Vaibhav Adsul**

GitHub: https://github.com/Vaibhav5564

---

## 📄 License

This project is developed for educational and learning purposes.