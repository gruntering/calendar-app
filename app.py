import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime, timedelta
from models import db, User, Holiday, UserDay
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'replace-this-with-a-long-random-string')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def easter_sunday(year):
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime(year, month, day).date()

with app.app_context():
    db.create_all()
    if not Holiday.query.first():
        print("Populating holidays...")
        holidays = []
        for year in range(2025, 2031):
            easter = easter_sunday(year)
            holidays.extend([
                Holiday(date=datetime(year, 1, 1).date(), name="Neujahr"),
                Holiday(date=datetime(year, 1, 6).date(), name="Heilige Drei Könige"),
                Holiday(date=(easter - timedelta(days=2)), name="Karfreitag"),
                Holiday(date=(easter + timedelta(days=1)), name="Ostermontag"),
                Holiday(date=datetime(year, 5, 1).date(), name="Tag der Arbeit"),
                Holiday(date=(easter + timedelta(days=39)), name="Christi Himmelfahrt"),
                Holiday(date=(easter + timedelta(days=50)), name="Pfingstmontag"),
                Holiday(date=(easter + timedelta(days=60)), name="Fronleichnam"),
                Holiday(date=datetime(year, 8, 8).date(), name="Augsburger Friedensfest"),
                Holiday(date=datetime(year, 8, 15).date(), name="Mariä Himmelfahrt"),
                Holiday(date=datetime(year, 10, 3).date(), name="Tag der Deutschen Einheit"),
                Holiday(date=datetime(year, 11, 1).date(), name="Allerheiligen"),
                Holiday(date=datetime(year, 12, 25).date(), name="1. Weihnachtstag"),
                Holiday(date=datetime(year, 12, 26).date(), name="2. Weihnachtstag"),
            ])
        db.session.bulk_save_objects(holidays)
        db.session.commit()
        print(f"Added {len(holidays)} holidays.")

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64), Regexp(r'^[a-zA-Z0-9_]+$')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class ChangeEmailForm(FlaskForm):
    new_email = StringField('New Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Change Email')

class EditVacationForm(FlaskForm):
    vacation_days = IntegerField('Remaining Vacation Days', validators=[DataRequired()])
    submit = SubmitField('Update')

def reset_counters_if_new_year(user):
    current_year = datetime.now().year
    if user.last_updated_year != current_year:
        user.remaining_vacation_days = 30
        user.remaining_sick_days = 0
        user.last_updated_year = current_year
        db.session.commit()

@app.route('/')
def index():
    if current_user.is_authenticated:
        print("User authenticated, redirecting to /calendar")
        return redirect(url_for('calendar'))
    flash('Please log in to access the calendar.')
    print("User not authenticated, redirecting to /login")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password,
                    remaining_vacation_days=30, remaining_sick_days=0, last_updated_year=datetime.now().year)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already taken.')
            elif User.query.filter_by(email=form.email.data).first():
                flash('Email already registered.')
            else:
                flash('Registration failed. Please try again.')
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print("User authenticated, redirecting to /calendar from /login")
        return redirect(url_for('calendar'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            reset_counters_if_new_year(user)
            print("User logged in, redirecting to /calendar")
            return redirect(url_for('calendar'))
        flash('Invalid username or password.')
    response = make_response(render_template('login.html', form=form))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/calendar')
@login_required
def calendar():
    reset_counters_if_new_year(current_user)
    return render_template('calendar.html', username=current_user.username)

@app.route('/get_entries')
@login_required
def get_entries():
    reset_counters_if_new_year(current_user)
    start = request.args.get('start')
    end = request.args.get('end')
    print(f"Fetching events from {start} to {end}")
    user_days = UserDay.query.filter_by(user_id=current_user.id).filter(UserDay.date.between(start, end)).all()
    holidays = Holiday.query.filter(Holiday.date.between(start, end)).all()
    events = [
        {
            'title': day.day_type.capitalize() + (f": {day.hours_worked}h" if day.hours_worked else ""),
            'start': day.date.isoformat(),
            'type': day.day_type,
            'backgroundColor': {'Work': 'orange', 'Vacation': '#ffeb3b', 'Sick': 'red', 'Absence': 'gray'}.get(day.day_type, 'gray')
        } for day in user_days
    ] + [
        {
            'title': holiday.name,
            'start': holiday.date.isoformat(),
            'type': 'Holiday',
            'backgroundColor': 'green'
        } for holiday in holidays
    ]
    print(f"Events fetched: {len(events)} (User days: {len(user_days)}, Holidays: {len(holidays)})")
    return jsonify({
        'events': events,
        'remaining_vacation_days': current_user.remaining_vacation_days,
        'remaining_sick_days': current_user.remaining_sick_days
    })

@app.route('/add_entry', methods=['POST'])
@login_required
def add_entry():
    reset_counters_if_new_year(current_user)
    data = request.get_json()
    date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    entry_type = data['entry_type']
    hours = data.get('hours', None)

    if Holiday.query.filter_by(date=date).first():
        return jsonify({'error': 'Cannot modify a holiday'}), 400

    day = UserDay.query.filter_by(user_id=current_user.id, date=date).first()
    if day:
        if day.day_type == 'Vacation':
            current_user.remaining_vacation_days += 1
        elif day.day_type == 'Sick':
            current_user.remaining_sick_days -= 1
        day.day_type = entry_type
        day.hours_worked = float(hours) if hours and entry_type == 'Work' else None
    else:
        day = UserDay(user_id=current_user.id, date=date, day_type=entry_type,
                      hours_worked=float(hours) if hours and entry_type == 'Work' else None)
        db.session.add(day)

    if entry_type == 'Vacation':
        if current_user.remaining_vacation_days <= 0:
            db.session.rollback()
            return jsonify({'error': 'No vacation days remaining'}), 400
        current_user.remaining_vacation_days -= 1
    elif entry_type == 'Sick':
        current_user.remaining_sick_days += 1

    db.session.commit()
    print(f"Added {entry_type} on {date}")
    return jsonify({
        'message': 'Entry added successfully',
        'remaining_vacation_days': current_user.remaining_vacation_days,
        'remaining_sick_days': current_user.remaining_sick_days
    })

@app.route('/delete_entry', methods=['POST'])
@login_required
def delete_entry():
    reset_counters_if_new_year(current_user)
    date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    day = UserDay.query.filter_by(user_id=current_user.id, date=date).first()
    if day:
        if day.day_type == 'Vacation':
            current_user.remaining_vacation_days += 1
        elif day.day_type == 'Sick':
            current_user.remaining_sick_days -= 1
        db.session.delete(day)
        db.session.commit()
    return jsonify({
        'message': 'Entry deleted successfully',
        'remaining_vacation_days': current_user.remaining_vacation_days,
        'remaining_sick_days': current_user.remaining_sick_days
    })

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if check_password_hash(current_user.password_hash, form.current_password.data):
            current_user.password_hash = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!')
            return redirect(url_for('calendar'))
        flash('Current password is incorrect.')
    return render_template('change_password.html', form=form)

@app.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if check_password_hash(current_user.password_hash, form.password.data):
            if User.query.filter_by(email=form.new_email.data).first():
                flash('This email is already registered.')
            else:
                current_user.email = form.new_email.data
                db.session.commit()
                flash('Email changed successfully!')
                return redirect(url_for('calendar'))
        flash('Password is incorrect.')
    return render_template('change_email.html', form=form)

@app.route('/edit_vacation', methods=['GET', 'POST'])
@login_required
def edit_vacation():
    reset_counters_if_new_year(current_user)
    form = EditVacationForm(vacation_days=current_user.remaining_vacation_days)
    if form.validate_on_submit():
        current_user.remaining_vacation_days = form.vacation_days.data
        db.session.commit()
        flash('Vacation days updated successfully!')
        return redirect(url_for('calendar'))
    return render_template('edit_vacation.html', form=form)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)