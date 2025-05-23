from app import create_app, db
import logging

# LOGGING CONFIGURATION, IF NEEDED (HAD EARLY ISSUES)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    try:
        logger.info("Starting F1nsight application...")
        with app.app_context():
            logger.info("Creating database tables...")
            db.create_all()
        logger.info("Starting Flask development server...")
        app.run(debug=True, port=5000)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")