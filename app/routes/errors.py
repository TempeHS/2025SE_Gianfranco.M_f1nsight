from flask import render_template, Blueprint

bp = Blueprint('errors', __name__)

@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    return render_template('errors/error.html',
                         code=500,
                         message="Internal Server Error",
                         details="Something went wrong on our end. Please try again later.",
                         back_allowed=True), 500

@bp.app_errorhandler(429)
def too_many_requests(error):
    return render_template('errors/error.html',
                         code=429,
                         message="Too Many Requests",
                         details="Please wait a moment before trying again.",
                         back_allowed=True), 429
