from flask import Blueprint, render_template

# CREATE BLUEPRINT FOR HOME ROUTES
bp = Blueprint('home', __name__)

@bp.route('/')
def index():
    return render_template('home.html')