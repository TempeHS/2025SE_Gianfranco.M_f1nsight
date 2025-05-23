# DASHBOARD ROUTES FOR F1NSIGHT
# HANDLES MAIN APPLICATION VIEWS AND FUNCTIONALITY

from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory
from flask_login import login_required
from app.services.driverChamp import driverStandings
import os

# CREATE BLUEPRINT FOR DASHBOARD ROUTES
bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
# ENSURE USER IS AUTHENTICATED TO ACCESS DASHBOARD
@login_required 
def index():
    # Get selected year from query parameters, default to current year
    selected_year = request.args.get('year', None)
    if selected_year:
        selected_year = int(selected_year)
    
    # Get available seasons for dropdown
    available_seasons = driverStandings.get_available_seasons()
    
    # Get standings for selected year
    standings = driverStandings.get_driver_standings(selected_year)
    
    return render_template('dashboard/index.html', 
                         standings=standings, 
                         available_seasons=available_seasons,
                         selected_year=selected_year)

@bp.route('/driver-number/<driver_name>/number.avif')
def driver_number_icon(driver_name):
    # Serve the number.avif file for a given driver
    icon_path = os.path.join('static', 'icons', 'drivers', driver_name)
    return send_from_directory(icon_path, 'number.avif')