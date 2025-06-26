from app import create_app, db
import logging
from dotenv import load_dotenv
import os
load_dotenv()

# LOGGING CONFIGURATION, IF NEEDED (HAD EARLY ISSUES)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Environment variables loaded. NEWS_API_KEY present: {bool(os.environ.get('NEWS_API_KEY'))}")

app = create_app()

if __name__ == '__main__':
    try:
        logger.info("starting f1nsight...")
        with app.app_context():
            logger.info("creating database tables...")
            db.create_all()
        logger.info("starting flask development server...")
        app.run(debug=True, port=5000)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")