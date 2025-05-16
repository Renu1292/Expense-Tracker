# INSTALL PACKAGES
from flask import Flask, render_template, redirect, url_for,flash,request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Float, func
from flask_wtf import FlaskForm
from unicodedata import category
from wtforms import StringField, SubmitField, FloatField, PasswordField, DecimalField
from wtforms.fields.datetime import DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from datetime import datetime, timedelta
from flask_login import LoginManager, login_user, logout_user, login_required,current_user
from collections import defaultdict
from flask_migrate import Migrate, migrate
from flask_bcrypt import Bcrypt, check_password_hash, generate_password_hash
from extensions import db, bcrypt, migrate
from models_expense import db, User, Expense

#  INITIALISE THE APP
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'

# INITIALIZE EXTENSIONS WITH APP
db.init_app(app)
bcrypt.init_app(app)
migrate.init_app(app, db)

# Initialize LoginManager:
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# STEP 4: CREATE THE DATABASE
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template("welcome.html")

#  SET HOME ROUTE - DISPLAY ALL THE LIST
@app.route("/home")
@login_required
def home():
    # Fetch the expenses for the current user
    lists = Expense.query.filter_by(user_id=current_user.id).all() # Fetch all the list from the data

    # Debugging: Print the fetched expenses
    print("Fetched Expenses:", lists)

    # Check if the lists are not empty and print the date of the first expense
    if lists:
        print(f"First expense date: {lists[0].date}")
    else:
        print("No expenses found for this user")

    # Create a welcome message
    welcome_message = f"Welcome back,{current_user.username}!"

    # Render the template with the fetched data
    return render_template("index.html", lists=lists, welcome_message=welcome_message )

#  DEFINE THE ADD FORM
class MyForm(FlaskForm):
    date  = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    title = StringField('Task', validators=[DataRequired()])
    amount = FloatField('Total Amount', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    submit = SubmitField('Add Expenses')

#  ADD THE TASK ROUTE
@app.route("/add", methods=['GET', 'POST'])
@login_required
def add():
    form = MyForm()
    if form.validate_on_submit():
        new_list = Expense(
            date = form.date.data,
            title = form.title.data,
            amount = form.amount.data,
            category = form.category.data,
            user_id = current_user.id
        )
        db.session.add(new_list)
        db.session.commit()
        flash("Expense added successfully!", "success")
        return redirect(url_for("home")) # Redirect to homepage
    return render_template("add.html", form=form, edit_expense=None)

# ADD THE EDIT ROUTE
@app.route("/edit/<int:id>", methods=['GET','POST'])
@login_required
def edit(id):

    edit_expense = Expense.query.get(id) # Get the title by ID

    # Check if the expense belongs to the current user
    if edit_expense.user_id != current_user.id:
        flash("You are not authorized to edit this expense.","danger")
        return redirect(url_for("home"))


    # Pre-fill the form with the current data
    form = MyForm(
        date = edit_expense.date,
        title = edit_expense.title,
        amount = edit_expense.amount,
        category = edit_expense.category
    )
    if form.validate_on_submit():
        # Update the expense with the new data from the form
        edit_expense.date = form.date.data
        edit_expense.title = form.title.data
        edit_expense.amount = form.amount.data
        edit_expense.category = form.category.data

        # Commit the changes to the database:
        db.session.commit()

        flash("Expense updated successfully!", "info")

        # Redirect to homepage after update.
        return redirect(url_for("home", id=edit_expense.id ))

    return render_template("add.html", form=form, edit_expense=edit_expense)

# ADD DELETE TASK ROUTE
@app.route("/delete/<int:id>", methods=['GET', 'POST'])
@login_required
def delete(id):
    delete_title = Expense.query.get(id) # Get the title by ID

    if delete_title:
        db.session.delete(delete_title) # Delete the title
        db.session.commit() # Save the changes
        flash("Expense deleted successfully!", "warning")
    else:
        flash("Expense not found!", "danger")
    return redirect(url_for('home')) # Redirect to homepage

# ADD DASHBOARD ROUTE
@app.route("/dashboard")
@login_required
def dashboard():
    # Get the total of all expenses from the database
    total = db.session.query(func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or 0

    # Group expenses by category and sum their amounts
    category_totals = (
        db.session.query(Expense.category, func.sum(Expense.amount))
        .filter_by(user_id=current_user.id)
        .group_by(Expense.category)
        .all()
    )

    # Prepare labels and values for the pie chart
    labels = [cat for cat, _ in category_totals]
    values = [float(amount) for _, amount in category_totals]

    return render_template("dashboard.html", total=total, labels=labels, values=values)

# Define the register form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

# Define the login form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Add the register route
@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if email or username already exists
        existing_user = User.query.filter(
            (User.email == form.email.data) | (User.username == form.username.data)
        ).first()
        if existing_user:
            flash('Username or email already exists.Please try again.', 'danger')
            return redirect(url_for('register'))

        # Create a new user
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Your account has been created! You can now log in.','success')
        return redirect(url_for('home'))
    return render_template('register.html', form=form)

# Add the login route
@app.route("/login", methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check email and password','danger')
    return render_template('login.html', form=form)

# Add the logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.','info')
    return redirect(url_for('index'))

@app.route('/analytics')
@login_required
def analytics():
    # Get selected month from query string
    selected_month = request.args.get('month')

    if selected_month:
        # Parse selected month
        selected_date = datetime.strptime(selected_month,"%Y-%m")
    else:
        selected_date = datetime.today()

    # Calculate current and previous month ranges
    current_month_start = selected_date.replace(day=1)
    next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    current_month_end = next_month_start

    # Monthly Totals (filtered by user)
    months = []
    monthly_totals = []

    monthly_results = (db.session.query(
        func.strftime('%Y-%m', Expense.date),
        func.sum(Expense.amount)
    ).filter(Expense.user_id == current_user.id)\
        .group_by(func.strftime('%Y-%m', Expense.date))\
        .order_by(func.strftime('%Y-%m', Expense.date)).all())

    for month, total in monthly_results:
        months.append(month)
        monthly_totals.append(float(total)) # Ensure it's serializable

    # Filtered Category Totals (for selected month)
    category_results = db.session.query(
        Expense.category,
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= current_month_start,
        Expense.date < current_month_end
    ).group_by(Expense.category).all()

    previous_category_results = db.session.query(
        Expense.category,
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= previous_month_start,
        Expense.date < current_month_start
    ).group_by(Expense.category).all()

    categories = []
    categories_total = []

    for category, total in category_results:
        categories.append(category)
        categories_total.append(float(total))

    # Calculate trend from previous month
    current_total = db.session.query(
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= current_month_start,
        Expense.date < current_month_end
    ).scalar() or 0

    previous_total = db.session.query(
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == current_user.id,
        Expense.date >= previous_month_start,
        Expense.date < current_month_start
    ).scalar() or 0

    trend_change = current_total - previous_total
    trend_percentage = ((trend_change / previous_total) * 100) if previous_total else 0

    # Set up sidebar chart to compare:
    current_category_dict = dict(category_results)
    previous_category_dict = dict(previous_category_results)

    # Collect all unique categories from both months
    all_categories = set(current_category_dict.keys()) | set(previous_category_dict.keys())

    # Build data lists for bar chart comparison
    category_bar_labels = []
    category_current_totals = []
    category_previous_totals = []

    for cat in sorted(all_categories):
        category_bar_labels.append(cat)
        category_current_totals.append(float(current_category_dict.get(cat, 0)))
        category_previous_totals.append(float(previous_category_dict.get(cat, 0)))

    # Colour palette for categories
    category_colors = [
        "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0",
        "#9966FF", "#FF9F40", "#8AFFC1", "#FF6F61"
    ]

    # Ensure colors match category count
    category_colors = category_colors[:len(categories)]

    return render_template(
        'analysis.html',
        months=months,
        monthly_totals=monthly_totals,
        category_labels=categories,
        category_totals=categories_total,  # Pie
        category_colors=category_colors,
        trend_percentage=round(trend_percentage, 1),
        current_total=current_total,  # Scalar value
        previous_total=previous_total,  # Scalar value
        category_bar_labels=category_bar_labels,  # For bar
        category_current_totals=category_current_totals,
        category_previous_totals=category_previous_totals
    )

# ADD PROFILE FORM
class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    monthly_budget = DecimalField('Monthly Budget', validators=[Optional()])
    submit = SubmitField('Update Profile')

# ADD PROFILE ROUTE
@app.route("/profile", methods=['GET','POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user) # Prefill form with current user

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.monthly_budget = form.monthly_budget.data or None # In case it's empty

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', form=form)

# ADD SETTING FORM
class SettingsForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm New Password", validators=[
        DataRequired(), EqualTo('new_password', message='Passwords must match.')
    ])
    change_password_submit = SubmitField("Change Password")
    delete_account_submit = SubmitField("Delete Account")

# ADD SETTING ROUTE
@app.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()

    # Handle password change
    if form.change_password_submit.data and form.validate_on_submit():
        if not check_password_hash(current_user.password, form.current_password.data):
            flash("Current password is incorrect", "danger")
        else:
            current_user.password = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash("Password changed successfully!", "success")
            return redirect(url_for('settings'))

    # Handle account deletion
    if form.delete_account_submit.data:
        user_id = current_user.id
        logout_user()
        user = db.session.get(User,user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            flash("Your account has been deleted.","info")
            return redirect(url_for('register'))
    return render_template("settings.html", form=form)

if __name__ == '__main__':
    app.run(debug=True)


