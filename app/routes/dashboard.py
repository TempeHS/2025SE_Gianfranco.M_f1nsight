# DASHBOARD ROUTES FOR F1NSIGHT
# HANDLES MAIN APPLICATION VIEWS AND FUNCTIONALITY

from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, jsonify, make_response
from flask_login import login_required, current_user
from app.services.driverChamp import driverStandings
from app.services.constructorChamp import constructorStandings
from app.services.news import get_news_service
news_service = get_news_service()
from datetime import datetime
import os
import random
from werkzeug.security import check_password_hash, generate_password_hash
from app.models.user import User
from app import db

# CREATE BLUEPRINT FOR DASHBOARD ROUTES
bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
# ENSURE USER IS AUTHENTICATED TO ACCESS DASHBOARD
@login_required 
def index():
    from flask import make_response
    
    # GET SELECTED YEAR
    try:
        selected_year = int(request.args.get('year', datetime.now().year))
    except ValueError:
        selected_year = datetime.now().year
    
    # GET SEASONS (cached)
    available_seasons = driverStandings.get_available_seasons()
    
    # GET STANDINGS (cached)
    driver_standings = driverStandings.get_driver_standings(selected_year)
    constructor_standings = constructorStandings.get_constructor_standings(selected_year)
    
    # Get a random driver profile for the fun section
    random_driver = None
    if driver_standings:
        random_driver = random.choice(driver_standings)
        if random_driver and 'driverId' in random_driver:
            from app.services.jolpica import get_driver_profile
            detailed_profile = get_driver_profile(random_driver['driverId'], selected_year)
            if detailed_profile:
                random_driver.update(detailed_profile)
    
    response = make_response(render_template('dashboard/index.html',
                                          standings=driver_standings,
                                          constructor_standings=constructor_standings,
                                          available_seasons=available_seasons,
                                          selected_year=selected_year,
                                          random_driver=random_driver,
                                          current_user=current_user))
    
    # Set cache-control headers for proper back/forward navigation
    response.headers['Cache-Control'] = 'private, no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    response.headers['Vary'] = '*'
    
    return response

@bp.route('/profile')
@login_required
def profile():
    return render_template('dashboard/profile.html')

@bp.route('/driver-number/<driver_name>/number.avif')
def driver_number_icon(driver_name):
    # SERVE NUMBER.AVIF
    icon_path = os.path.join('static', 'icons', 'drivers', driver_name)
    return send_from_directory(icon_path, 'number.avif')

@bp.route('/compare')
@login_required
def compare():
    drivers = driverStandings.get_driver_list()
    return render_template('dashboard/compare.html', drivers=drivers)

@bp.route('/compare/data')
@login_required
def compare_data():
    driver1 = request.args.get('driver1')
    driver2 = request.args.get('driver2')
    year = request.args.get('year', datetime.now().year)
    
    if not driver1:
        return jsonify({'error': 'at least one driver must be specified'}), 400
    
    try:
        # Clear cached data to get fresh results
        from app import cache
        cache.delete_memoized(driverStandings.get_driver_points)
        
        # Get fresh driver points data
        driver1_result = driverStandings.get_driver_points(driver1, year)
        driver2_result = {'points': [], 'races': []}
        
        if driver2:
            driver2_result = driverStandings.get_driver_points(driver2, year)
        
        # Debug information
        print(f"Driver 1 ({driver1}) data: {len(driver1_result['races'])} races, {len(driver1_result['points'])} points")
        if driver2:
            print(f"Driver 2 ({driver2}) data: {len(driver2_result['races'])} races, {len(driver2_result['points'])} points")
        
        # Validate data integrity
        if len(driver1_result['races']) != len(driver1_result['points']):
            print(f"Warning: Mismatch in driver1 data lengths - races: {len(driver1_result['races'])}, points: {len(driver1_result['points'])}")
            
        if driver2 and len(driver2_result['races']) != len(driver2_result['points']):
            print(f"Warning: Mismatch in driver2 data lengths - races: {len(driver2_result['races'])}, points: {len(driver2_result['points'])}")
        
        # Use the race names from whichever driver has more data
        race_names = driver1_result['races']
        if len(driver2_result['races']) > len(race_names):
            race_names = driver2_result['races']
        
        # Make sure points arrays match the race names array length
        driver1_points = driver1_result['points']
        driver2_points = driver2_result['points']
        
        # If one driver has fewer races, pad their points with zeros
        if len(driver1_points) < len(race_names):
            driver1_points = driver1_points + [driver1_points[-1] if driver1_points else 0] * (len(race_names) - len(driver1_points))
            
        if len(driver2_points) < len(race_names):
            driver2_points = driver2_points + [driver2_points[-1] if driver2_points else 0] * (len(race_names) - len(driver2_points))
        
        return jsonify({
            'status': 'success',
            'data': {
                'races': race_names,
                'driver1_points': driver1_points,
                'driver2_points': driver2_points
            }
        })
    except Exception as e:
        print(f"Error processing driver data: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/news')
@login_required
def news():
    try:
        sources = request.args.get('sources', None)
        page = request.args.get('page', '1')
        page_size = int(request.args.get('page_size', 30))

        # FETCH NEWS DATA
        news_data = news_service.get_f1_news(sources=sources, page_size=page_size, page=page)

        # FETCH AVAILABLE SOURCES
        sources_data = news_service.get_available_sources()

        if news_data.get('status') == 'error':
            flash(f"Error fetching news: {news_data.get('message')}", 'error')
            return render_template('dashboard/news.html', news=[], sources=[], selected_sources=[])

        if sources_data.get('status') == 'error':
            flash(f"Error fetching sources: {sources_data.get('message')}", 'error')
            return render_template('dashboard/news.html', news=news_data.get('articles', []), sources=[], selected_sources=[])

        return render_template('dashboard/news.html',
                               news=news_data.get('articles', []),
                               sources=sources_data.get('sources', []),
                               selected_sources=sources.split(',') if sources else [])
    except Exception as e:
        print(f"Error in news route: {str(e)}")
        flash(f"Error fetching news: {str(e)}", 'error')
        return render_template('dashboard/news.html', news=[], sources=[], selected_sources=[])

@bp.route('/races')
@login_required
def races():
    # Get parameters from request
    from app.services.jolpica import get_available_years, get_races_by_season, get_race_results
    
    selected_year = request.args.get('year', datetime.now().year)
    selected_round = request.args.get('round', None)
    
    # Get available seasons
    available_seasons = get_available_years()
    
    # Get races for the selected season
    races = get_races_by_season(selected_year)
    
    # Get detailed results if a race is selected
    race_results = None
    prev_race = None
    next_race = None
    
    if selected_round:
        race_results = get_race_results(selected_year, selected_round)
        
        # Get previous and next race information
        try:
            # Convert selected_round to int for comparison
            selected_round_int = int(selected_round)
            
            # Sort races by round number
            sorted_races = sorted(races, key=lambda x: int(x['round']))
            
            # Get current race index
            current_race_index = None
            for i, race in enumerate(sorted_races):
                if int(race['round']) == selected_round_int:
                    current_race_index = i
                    break
            
            # If we found the current race, get prev/next
            if current_race_index is not None:
                # Add previous race if not the first race
                if current_race_index > 0:
                    prev_race = sorted_races[current_race_index - 1]
                
                # Add next race if not the last race
                if current_race_index < len(sorted_races) - 1:
                    next_race = sorted_races[current_race_index + 1]
        except (ValueError, TypeError) as e:
            print(f"Error determining next/previous race: {e}")
    
    return render_template('dashboard/races.html',
                          available_seasons=available_seasons,
                          selected_year=selected_year,
                          races=races,
                          selected_round=selected_round,
                          race_results=race_results,
                          prev_race=prev_race,
                          next_race=next_race)

@bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    new_username = request.form.get('new_username')
    password = request.form.get('password')

    if not new_username or not password:
        flash('All fields are required.', 'error')
        return redirect(url_for('dashboard.edit_profile'))

    user = User.query.get(current_user.id)

    if not user or not user.check_password(password):
        flash('Invalid password.', 'error')
        return redirect(url_for('dashboard.edit_profile'))
        
    # Check if username already exists (for another user)
    existing_user = User.query.filter(User.username == new_username, User.id != current_user.id).first()
    if existing_user:
        flash('Username already taken.', 'error')
        return redirect(url_for('dashboard.edit_profile'))

    user.username = new_username
    db.session.commit()

    flash('Profile updated successfully.', 'success')
    return redirect(url_for('dashboard.profile'))

@bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_password or not new_password or not confirm_password:
        flash('All fields are required.', 'error')
        return redirect(url_for('dashboard.change_password_page'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('dashboard.change_password_page'))
        
    # Import password validation from utils
    from app.utils.validators import validate_password
    
    # Validate the new password
    valid_password, password_msg = validate_password(new_password)
    if not valid_password:
        flash(password_msg, 'error')
        return redirect(url_for('dashboard.change_password_page'))

    user = User.query.get(current_user.id)

    if not user or not user.check_password(current_password):
        flash('Invalid current password.', 'error')
        return redirect(url_for('dashboard.change_password_page'))

    # Set the new password using the User model method
    user.set_password(new_password)
    db.session.commit()

    flash('Password changed successfully.', 'success')
    return redirect(url_for('dashboard.profile'))

@bp.route('/edit-profile')
@login_required
def edit_profile():
    return render_template('dashboard/edit_profile.html')

@bp.route('/change-password')
@login_required
def change_password_page():
    return render_template('dashboard/change_password.html')