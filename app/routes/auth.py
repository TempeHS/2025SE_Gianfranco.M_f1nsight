# AUTHENTICATION ROUTES FOR F1NSIGHT 
# HANDLES USER REGISTRATION, LOGIN, AND LOGOUT FUNCTIONALITY

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.models.user import User
from app import db
from app.utils.validators import validate_password, validate_email, validate_username, sanitize_input


# CREATE BLUEPRINT FOR AUTH ROUTES
bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        # SANITIZE USER INPUT
        username = sanitize_input(request.form['username'])
        email = sanitize_input(request.form['email'])
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # VALIDATE USERNAME
        valid_username, username_msg = validate_username(username)
        if not valid_username:
            flash(username_msg)
            return redirect(url_for('auth.register'))

        # VALIDATE EMAIL
        valid_email, email_msg = validate_email(email)
        if not valid_email:
            flash(email_msg)
            return redirect(url_for('auth.register'))

        # VALIDATE PASSWORD
        valid_password, password_msg = validate_password(password)
        if not valid_password:
            flash(password_msg)
            return redirect(url_for('auth.register'))

        # VALIDATE PASSWORD MATCH
        if password != confirm_password:
            flash('passwords do not match')
            return redirect(url_for('auth.register'))

        # CHECK EXISTING USERNAME/EMAIL
        if User.query.filter_by(username=username).first():
            flash('username already exists')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('email already registered')
            return redirect(url_for('auth.register'))
      
        # CREATE NEW USER
        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('registration successful! please login.')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('an error occurred. please try again.')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    # HANDLE LOGIN FORM SUBMISSION
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            # Get remember me preference
            remember = 'remember' in request.form
            login_user(user, remember=remember)
            return redirect(url_for('dashboard.index'))
        flash('invalid username or password')
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    # HANDLE USER LOGOUT
    logout_user()
    return redirect(url_for('home.index'))