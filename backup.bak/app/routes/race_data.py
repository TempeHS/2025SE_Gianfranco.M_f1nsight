from flask import Blueprint, render_template
from ..models.race import RaceResult

race_data_bp = Blueprint('race_data', __name__, url_prefix='/race-data')

@race_data_bp.route('/')
def show_race_data():
    races = RaceResult.query.all()
    return render_template('race_data.html', races=races)
