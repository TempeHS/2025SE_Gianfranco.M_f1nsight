from flask import Blueprint, render_template, redirect, url_for

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route("/")
def index():
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")
