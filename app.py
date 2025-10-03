from flask import Flask, render_template, request, flash, redirect, url_for
import requests
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

load_dotenv()  # Load from .env

app = Flask(__name__)
load_dotenv(dotenv_path="/Users/nilanshu/Desktop/contest_tracker_fallback/.env", override=True)# override=True ensures old env vars are replaced
app.secret_key = os.getenv("SECRET_KEY")
# Your CList API key
API_KEY =os.getenv("CLIST_API_KEY")
USERNAME = os.getenv("CLIST_USERNAME")

# Database Configuration
# For local development with PostgreSQL:
# DATABASE_URL=postgresql://username:password@localhost:5432/algoradar
# For production, your hosting platform will provide this
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///fallback.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Handle PostgreSQL URL format (some platforms use postgres:// instead of postgresql://)
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

# Initialize Database
db = SQLAlchemy(app)

# Cache Configuration
cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',  # Use SimpleCache for now, upgrade to Redis later
    'CACHE_DEFAULT_TIMEOUT': 600  # 10 minutes (600 seconds)
})

# Timezone conversion: UTC → IST
IST = pytz.timezone('Asia/Kolkata')


# ========================================
# DATABASE MODELS
# ========================================
class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(IST))
    read = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<ContactMessage {self.name} - {self.email}>'


# ========================================
# CONTEXT PROCESSOR
# ========================================
@app.context_processor
def inject_now():
    """Make datetime and current IST time available in all templates"""
    now_ist = datetime.now(IST)
    return {
        'datetime': datetime,
        'now_ist': now_ist
    }


# ========================================
# CACHED API CALL FUNCTION
# ========================================
@cache.cached(timeout=600, key_prefix='all_contests')
def fetch_contests_from_api():
    """
    Fetch contests from CList API and cache for 10 minutes.
    This function is called once every 10 minutes, regardless of number of users.
    """
    url = f"https://clist.by/api/v2/contest/?username={USERNAME}&api_key={API_KEY}&upcoming=true&limit=500&order_by=start"

    try:
        print("🔄 Fetching fresh data from CList API...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        contests = response.json().get("objects", [])
        print(f"✅ Fetched {len(contests)} contests from API")  # Debug log
        return contests
    except requests.RequestException as e:
        print(f"❌ Error fetching contests: {e}")
        return []




@app.route("/", methods=["GET"])
def index():
    platform_filter = request.args.getlist("platform")  # e.g., ['codeforces.com', 'atcoder.jp']
    time_filter = request.args.get("time")  # 'today', 'week', 'month', or None

    # Fetch upcoming contests from CList
    url = f"https://clist.by/api/v2/contest/?username={USERNAME}&api_key={API_KEY}&upcoming=true&limit=500&order_by=start"
    response = requests.get(url)
    contests = response.json().get("objects", [])

    filtered = []
    for c in contests:
        resource = c['resource'].lower() if isinstance(c['resource'], str) else str(c['resource']).lower()

        # Platform filter
        if platform_filter and resource not in [p.lower() for p in platform_filter]:
            continue

        # Time filter
        start_utc = datetime.fromisoformat(c['start'])
        start_ist = start_utc.astimezone(IST)
        end_ist = datetime.fromisoformat(c['end']).astimezone(IST)

        if time_filter:
            now = datetime.now(IST)
            if time_filter == 'today' and start_ist.date() != now.date():
                continue
            elif time_filter == 'week' and (
                    start_ist.date() > (now + timedelta(days=7)).date() or start_ist.date() < now.date()):
                continue
            elif time_filter == 'month' and (
                    start_ist.date() > (now + timedelta(days=30)).date() or start_ist.date() < now.date()):
                continue

        # Add formatted date & time
        c['start_date'] = start_ist.strftime("%d-%m-%Y")
        c['start_time'] = start_ist.strftime("%H:%M")
        c['end_ist'] = end_ist.strftime("%H:%M")
        filtered.append(c)

    # Sort by start date-time
    filtered.sort(key=lambda x: datetime.strptime(x['start_date'] + ' ' + x['start_time'], "%d-%m-%Y %H:%M"))

    # Limit to next 20 contests per platform
    limited = []
    count_per_platform = defaultdict(int)
    for c in filtered:
        if count_per_platform[c['resource']] < 20:
            limited.append(c)
            count_per_platform[c['resource']] += 1

    return render_template("index.html", contests=limited, platforms=platform_filter, time_filter=time_filter)


# ========================================
# CONTACT PAGE ROUTE
# ========================================
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        # Validate input
        if not name or not email or not message:
            flash('All fields are required!', 'error')
            return redirect(url_for('contact'))

        if len(name) < 2:
            flash('Name must be at least 2 characters long.', 'error')
            return redirect(url_for('contact'))

        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('contact'))

        if len(message) < 10:
            flash('Message must be at least 10 characters long.', 'error')
            return redirect(url_for('contact'))

            # Save to database
        try:
            new_message = ContactMessage(
                name=name,
                email=email,
                message=message
            )
            db.session.add(new_message)
            db.session.commit()

            flash('Thank you for contacting us! We\'ll get back to you soon.', 'success')
            print(f"📧 New contact message from {name} ({email})")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error saving contact message: {e}")
            flash('There was an error processing your request. Please try again.', 'error')

        return redirect(url_for('contact'))

    # GET request - show the contact form
    return render_template('contact.html')

# ========================================
# DATABASE INITIALIZATION
# ========================================
@app.cli.command('init-db')
def init_db():
    """Initialize the database."""
    db.create_all()
    print("✅ Database tables created successfully!")


@app.cli.command('drop-db')
def drop_db():
    """Drop all database tables."""
    db.drop_all()
    print("🗑️ Database tables dropped!")


# ========================================
# OPTIONAL: View messages (for testing)
# ========================================
@app.route('/admin/messages')
def view_messages():
    """
    Simple admin view to see contact messages.
    TODO: Add authentication before deploying to production!
    """
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin_messages.html', messages=messages)


if __name__ == "__main__":
    app.run(debug=True)
