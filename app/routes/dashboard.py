# DASHBOARD ROUTES FOR F1NSIGHT
# HANDLES MAIN APPLICATION VIEWS AND FUNCTIONALITY

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.services.driverChamp import driverStandings

# CREATE BLUEPRINT FOR DASHBOARD ROUTES
bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
# ENSURE USER IS AUTHENTICATED TO ACCESS DASHBOARD
@login_required 
def index():
    standings = driverStandings.get_driver_standings()
    return render_template('dashboard/index.html', standings=standings)