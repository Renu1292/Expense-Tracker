from extensions import db
from flask_login import UserMixin



class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    monthly_budget = db.Column(db.Float, default=0.0)

    expenses = db.relationship('Expense', backref="user", lazy=True)

# STEP 3: CREATE THE DATABASE TABLE
class Expense(db.Model):
    __tablename__ = 'Expense_List'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(200), nullable=False)
    user_id =db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

