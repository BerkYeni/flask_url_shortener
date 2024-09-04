from waitress import serve
from app import app, init_db
import logging

if __name__ == "__main__":
    logging.basicConfig(filename='app.log', level=logging.INFO)
    logger = logging.getLogger('waitress')
    logger.setLevel(logging.INFO)
    
    init_db()  # Initialize the database
    
    serve(app, host="0.0.0.0", port=8000, _quiet=False)