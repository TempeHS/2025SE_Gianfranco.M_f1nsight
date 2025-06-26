from flask import Blueprint, render_template, request
from flask_login import login_required
from ..services.driverChamp import driverStandings
from ..services.constructorChamp import constructorStandings as constructorStandings_service

bp = Blueprint('standings', __name__)

@bp.route('/')
@login_required
def index():
    from datetime import datetime
    year = request.args.get('year', str(datetime.now().year))
    
    standings = driverStandings.get_driver_standings(year)
    constructor_standings = constructorStandings_service.get_constructor_standings(year)
    available_seasons = driverStandings.get_available_seasons()
    
    return render_template('dashboard/standings.html',
                         standings=standings,
                         constructor_standings=constructor_standings,
                         available_seasons=available_seasons,
                         selected_year=year)
