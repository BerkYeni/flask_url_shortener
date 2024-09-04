import os
import logging
from flask import Flask, render_template, request, redirect, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import string
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO)

class ShortURL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False)
    short_url = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    clicks = db.Column(db.Integer, default=0)

def generate_short_url():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(6))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            original_url = request.form['url']
            if not original_url:
                return render_template('index.html', error='Please enter a URL', all_urls=all_urls)
            
            existing_url = ShortURL.query.filter_by(original_url=original_url).first()
            if existing_url:
                return render_template('index.html', short_url=request.host_url + existing_url.short_url, all_urls=all_urls)
            
            short_url = generate_short_url()
            while ShortURL.query.filter_by(short_url=short_url).first():
                short_url = generate_short_url()
            
            new_url = ShortURL(original_url=original_url, short_url=short_url)
            db.session.add(new_url)
            db.session.commit()
            
            all_urls = ShortURL.query.order_by(ShortURL.created_at.desc()).all()  # Refresh the list
            return render_template('index.html', short_url=request.host_url + short_url, all_urls=all_urls)
        except Exception as e:
            app.logger.error(f"An error occurred: {str(e)}")
            return render_template('index.html', error='An internal error occurred. Please try again.', all_urls=all_urls)
    
    # Load initial URLs
    page = 1
    per_page = 10
    pagination = ShortURL.query.order_by(ShortURL.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('index.html', urls=pagination.items)

@app.route('/<short_url>')
def redirect_to_url(short_url):
    url_record = ShortURL.query.filter_by(short_url=short_url).first()
    if url_record:
        url_record.clicks += 1
        db.session.commit()
        return redirect(url_record.original_url)
    abort(404)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/load_more/<int:page>')
def load_more(page):
    per_page = 10
    pagination = ShortURL.query.order_by(ShortURL.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    urls = [{
        'short_url': url.short_url,
        'original_url': url.original_url,
        'clicks': url.clicks,
        'created_at': url.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for url in pagination.items]
    return jsonify(urls=urls, has_next=pagination.has_next)

def init_db():
    with app.app_context():
        db.create_all()
        print("Database initialized.")

if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=False)