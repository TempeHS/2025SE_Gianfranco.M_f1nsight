# DASHBOARD ROUTES FOR F1NSIGHT
# HANDLES MAIN APPLICATION VIEWS AND FUNCTIONALITY

from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, jsonify
from flask_login import login_required, current_user
from app.services.driverChamp import driverStandings
from app.services.constructorChamp import constructorStandings
from app.services.news import get_news_service
news_service = get_news_service()
from datetime import datetime
import os

# CREATE BLUEPRINT FOR DASHBOARD ROUTES
bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
# ENSURE USER IS AUTHENTICATED TO ACCESS DASHBOARD
@login_required 
def index():
    # GET SELECTED YEAR
    selected_year = request.args.get('year', None)
    if selected_year:
        selected_year = int(selected_year)
    
    # GET SEASONS
    available_seasons = driverStandings.get_available_seasons()
    
    # GET STANDINGS
    driver_standings = driverStandings.get_driver_standings(selected_year)
    constructor_standings = constructorStandings.get_constructor_standings(selected_year)
    
    return render_template('dashboard/index.html', 
                         standings=driver_standings,
                         constructor_standings=constructor_standings,
                         available_seasons=available_seasons,
                         selected_year=selected_year)

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
    
    if not driver1 or not driver2:
        return jsonify({'error': 'Both drivers must be specified'}), 400
    
    try:
        driver1_result = driverStandings.get_driver_points(driver1, year)
        driver2_result = driverStandings.get_driver_points(driver2, year)
        
        print(f"Driver 1 ({driver1}) data:", driver1_result)
        print(f"Driver 2 ({driver2}) data:", driver2_result)
        
        race_names = driver1_result['races'] or driver2_result['races']
        
        return jsonify({
            'status': 'success',
            'data': {
                'races': race_names,
                'driver1_points': driver1_result['points'],
                'driver2_points': driver2_result['points']
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
        
        news_data = news_service.get_f1_news(sources=sources, page_size=page_size, page=page)
        print(f"News data status: {news_data.get('status')} for page {page}") 
        print(f"News data message: {news_data.get('message')}")
        print(f"Number of articles: {len(news_data.get('articles', []))}")  
        
        sources_data = news_service.get_available_sources()
        print(f"Sources data status: {sources_data.get('status')}") 
        
        if news_data.get('status') == 'error':
            flash(f"Error fetching news: {news_data.get('message')}", 'error')
            return render_template('dashboard/news.html', news=[], sources=[], selected_sources=[])
            
        if sources_data.get('status') == 'error':
            flash(f"Error fetching sources: {sources_data.get('message')}", 'error')
            return render_template('dashboard/news.html', 
                                news=news_data.get('articles', []), 
                                sources=[], 
                                selected_sources=[])
        
        return render_template('dashboard/news.html',
                             news=news_data.get('articles', []),
                             sources=sources_data.get('sources', []),
                             selected_sources=sources.split(',') if sources else [])
    except Exception as e:
        print(f"Error in news route: {str(e)}")
        flash(f"Error fetching news: {str(e)}", 'error')
        return render_template('dashboard/news.html', news=[], sources=[], selected_sources=[])