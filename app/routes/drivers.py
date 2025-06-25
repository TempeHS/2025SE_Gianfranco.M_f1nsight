from flask import Blueprint, render_template, request, jsonify
from app.services.jolpica import search_drivers, get_driver_profile, get_available_years
from datetime import datetime

bp = Blueprint('drivers', __name__)

@bp.route('/search')
def search():
    year = request.args.get('year', str(datetime.now().year))
    query = request.args.get('q', '')
    
    years = get_available_years()
    if not years:
        years = [str(datetime.now().year)]
    
    drivers = search_drivers(year, query) if year else []
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(drivers)
    
    return render_template('drivers/search.html', 
                         drivers=drivers,
                         years=years,
                         selected_year=year,
                         query=query)

@bp.route('/drivers/<driver_id>')
def profile(driver_id):
    year = request.args.get('year')
    profile = get_driver_profile(driver_id, year)
    if not profile:
        return render_template('errors/404.html'), 404
    return render_template('drivers/profile.html', profile=profile)
