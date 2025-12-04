from flask import Flask, render_template, request, flash, redirect, url_for, session
from functools import wraps
import requests
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from datetime import timezone
import time
import threading
from sqlalchemy import text

# Make IST timezone-aware
IST = pytz.timezone('Asia/Kolkata')
UTC = pytz.UTC
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# API Configuration
API_KEY = os.getenv("CLIST_API_KEY")
USERNAME = os.getenv("CLIST_USERNAME")

# Admin Configuration
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME" )
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

#DataBase Configuration
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///fallback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# OPTIMIZED connection pool for high concurrency + lazy loading
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': False,  # CHANGED: Don't ping eagerly (we do it lazily now)
    'pool_recycle': 280,  # Recycle before Supabase timeout (300s)
    'pool_size': 5,  # INCREASED: More connections for concurrent users
    'max_overflow': 10,  # INCREASED: Allow bursts of traffic
    'pool_timeout': 20,  # INCREASED: Wait longer for connection
    'connect_args': {
        'connect_timeout': 10,  # Reasonable timeout
        'keepalives': 1,
        'keepalives_idle': 30,
        'keepalives_interval': 10,
        'keepalives_count': 3,
        'options': '-c statement_timeout=10000'  # 10s query timeout
    }
}

db = SQLAlchemy(app)

# In-memory fallback cache (for when DB is slow/unavailable)
_cache = {
    'contests': [],
    'last_fetch': None,
    'fetch_in_progress': False
}


# ========================================
# DATABASE MODELS
# ========================================
class Contest(db.Model):
    """Stores contest data from CList API"""
    __tablename__ = 'contests'

    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.String(255), unique=True, nullable=False)
    event = db.Column(db.String(500), nullable=False)
    resource = db.Column(db.String(100), nullable=False)
    href = db.Column(db.String(1000))
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC),
                           onupdate=lambda: datetime.now(UTC))

    def __repr__(self):
        return f'<Contest {self.event} on {self.resource}>'

    def to_dict(self):
        """Convert to dictionary for template rendering"""
        start_utc = self.start if self.start.tzinfo else UTC.localize(self.start)
        end_utc = self.end if self.end.tzinfo else UTC.localize(self.end)
        start_ist = start_utc.astimezone(IST)
        end_ist = end_utc.astimezone(IST)

        return {
            'event': self.event,
            'resource': self.resource,
            'href': self.href,
            'start_date': start_ist.strftime("%d-%m-%Y"),
            'start_time': start_ist.strftime("%H:%M"),
            'end_ist': end_ist.strftime("%H:%M"),
            'start': start_utc,
            'duration': self.duration
        }


class CacheMetadata(db.Model):
    """Tracks when contests were last updated"""
    __tablename__ = 'cache_metadata'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def get_last_update():
        try:
            meta = CacheMetadata.query.filter_by(key='contests_last_update').first()
            if not meta:
                return None
            if meta.last_updated.tzinfo is None:
                return UTC.localize(meta.last_updated)
            return meta.last_updated
        except Exception as e:
            print(f"️ Error getting last update: {e}")
            return None

    @staticmethod
    def set_last_update():
        try:
            meta = CacheMetadata.query.filter_by(key='contests_last_update').first()
            now_utc = datetime.now(UTC)

            if not meta:
                meta = CacheMetadata(key='contests_last_update', last_updated=now_utc)
                db.session.add(meta)
            else:
                meta.last_updated = now_utc
            db.session.commit()
        except Exception as e:
            print(f"️ Error setting last update: {e}")
            db.session.rollback()


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
# ADMIN AUTHENTICATION DECORATOR
# ========================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin panel.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# ========================================
# CONTEXT PROCESSOR
# ========================================
@app.context_processor
def inject_now():
    now_ist = datetime.now(IST)
    return {
        'datetime': datetime,
        'now_ist': now_ist
    }


# ========================================
# CACHED API CALL FUNCTION
# ========================================
def fetch_and_update_contests():
    """
    Fetches contests from CList API and updates database using BULK operations.
    OPTIMIZED: 25s → 3s for 150 contests
    """
    global _cache

    # Prevent multiple simultaneous fetches
    if _cache['fetch_in_progress']:
        print("⏳ Fetch already in progress, skipping...")
        return False

    _cache['fetch_in_progress'] = True

    url = f"https://clist.by/api/v2/contest/?username={USERNAME}&api_key={API_KEY}&upcoming=true&limit=500&order_by=start"

    try:
        print("🔄 Fetching fresh data from CList API...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        contests_data = response.json().get("objects", [])

        fetch_time = time.time() - start_time
        print(f"✅ Fetched {len(contests_data)} contests in {fetch_time:.2f}s")

        # Update in-memory cache immediately
        _cache['contests'] = contests_data
        _cache['last_fetch'] = datetime.now(UTC)

        # BULK DATABASE UPDATE
        db_start = time.time()

        # Step 1: Clean up old contests
        cutoff_date = datetime.now(UTC) - timedelta(days=30)
        deleted = Contest.query.filter(Contest.start < cutoff_date).delete()
        db.session.commit()

        if deleted > 0:
            print(f"🗑️ Deleted {deleted} old contests")

        # Step 2: Fetch all existing contest IDs in ONE query
        existing_ids = {c.contest_id for c in Contest.query.with_entities(Contest.contest_id).all()}

        # Step 3: Separate new vs existing contests
        new_contests = []
        update_mappings = []

        for c in contests_data:
            contest_id = str(c.get('id', ''))

            # Parse dates
            start_dt = datetime.fromisoformat(c['start'].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(c['end'].replace('Z', '+00:00'))

            if start_dt.tzinfo is None:
                start_dt = UTC.localize(start_dt)
            if end_dt.tzinfo is None:
                end_dt = UTC.localize(end_dt)

            contest_data = {
                'contest_id': contest_id,
                'event': c.get('event', ''),
                'resource': c.get('resource', ''),
                'href': c.get('href', ''),
                'start': start_dt,
                'end': end_dt,
                'duration': c.get('duration', 0)
            }

            if contest_id in existing_ids:
                # For update: need to include the ID for SQLAlchemy to know which row
                update_mappings.append(contest_data)
            else:
                # For insert: create new Contest object
                new_contests.append(Contest(**contest_data))

        # Step 4: BULK INSERT new contests (all at once)
        if new_contests:
            db.session.bulk_save_objects(new_contests)
            print(f"➕ Bulk inserted {len(new_contests)} new contests")

        # Step 5: BULK UPDATE existing contests (all at once)
        if update_mappings:
            # For bulk update, we need to fetch existing objects first
            # But we'll do it more efficiently
            existing_contests = Contest.query.filter(
                Contest.contest_id.in_([c['contest_id'] for c in update_mappings])
            ).all()

            # Create a mapping for quick lookup
            contest_map = {c.contest_id: c for c in existing_contests}

            # Update each object
            for update_data in update_mappings:
                cid = update_data['contest_id']
                if cid in contest_map:
                    contest = contest_map[cid]
                    contest.event = update_data['event']
                    contest.resource = update_data['resource']
                    contest.href = update_data['href']
                    contest.start = update_data['start']
                    contest.end = update_data['end']
                    contest.duration = update_data['duration']

            print(f"🔄 Updated {len(update_mappings)} existing contests")

        # Commit everything in ONE transaction
        db.session.commit()
        CacheMetadata.set_last_update()

        db_time = time.time() - db_start
        print(f"💾 DB updated in {db_time:.2f}s: {len(update_mappings)} updated, {len(new_contests)} new")

        return True

    except Exception as e:
        print(f"❌ Error fetching contests: {e}")
        db.session.rollback()
        return False
    finally:
        _cache['fetch_in_progress'] = False


def safe_db_query(query_func, *args, **kwargs):
    """
    Execute database query with automatic reconnection on failure.
    Only pings database when actually needed.
    """
    max_retries = 2

    for attempt in range(max_retries):
        try:
            return query_func(*args, **kwargs)
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Database query failed (attempt {attempt + 1}), reconnecting...")
                try:
                    db.session.rollback()
                    db.session.remove()
                    # Quick ping to re-establish connection
                    db.session.execute(db.text('SELECT 1'))
                except:
                    pass
            else:
                print(f"❌ Database query failed after {max_retries} attempts: {e}")
                raise

def should_refresh_contests():
    """
    Check if contests need to be refreshed.
    More lenient to avoid re-fetching on DB reconnects.
    """
    try:
        # Check in-memory cache first (instant)
        if _cache['last_fetch']:
            time_since = (datetime.now(UTC) - _cache['last_fetch']).total_seconds() / 60
            if time_since < 10:
                print(f" In-memory cache fresh ({time_since:.1f} min old)")
                return False

        # Then check database (might be slow after reconnect)
        last_update = CacheMetadata.get_last_update()

        if not last_update:
            # Check if database actually has contests
            contest_count = Contest.query.count()
            if contest_count > 0:
                print(f"ℹ Database has {contest_count} contests but no metadata, assuming fresh")
                # Set metadata for next time
                CacheMetadata.set_last_update()
                return False
            else:
                print(" Database empty, need to fetch")
                return True

        now_utc = datetime.now(UTC)
        time_since_update = now_utc - last_update
        minutes_ago = time_since_update.total_seconds() / 60

        print(f" Last DB update was {minutes_ago:.1f} minutes ago")
        return time_since_update > timedelta(minutes=10)

    except Exception as e:
        print(f" Error checking cache: {e}")
        # If database fails, check in-memory cache
        if _cache['last_fetch']:
            time_since = (datetime.now(UTC) - _cache['last_fetch']).total_seconds() / 60
            if time_since < 15:  # More lenient
                print(f" Using in-memory fallback ({time_since:.1f} min old)")
                return False
        return True


def get_contests_from_db(platform_filter=None, time_filter=None):
    """Fetch contests from database with filters - with automatic reconnection"""

    def _query():
        now_utc = datetime.now(UTC)
        query = Contest.query.filter(Contest.start >= now_utc)

        if platform_filter:
            query = query.filter(Contest.resource.in_(platform_filter))

        if time_filter:
            now_ist = now_utc.astimezone(IST)

            if time_filter == 'today':
                start_of_today = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_today = now_ist.replace(hour=23, minute=59, second=59, microsecond=999999)
                start_utc = start_of_today.astimezone(UTC)
                end_utc = end_of_today.astimezone(UTC)
                query = query.filter(Contest.start >= start_utc, Contest.start <= end_utc)

            elif time_filter == 'week':
                end_of_week = now_ist + timedelta(days=7)
                end_of_week_utc = end_of_week.astimezone(UTC)
                query = query.filter(Contest.start <= end_of_week_utc)

            elif time_filter == 'month':
                end_of_month = now_ist + timedelta(days=30)
                end_of_month_utc = end_of_month.astimezone(UTC)
                query = query.filter(Contest.start <= end_of_month_utc)

        query = query.order_by(Contest.start.asc())
        all_contests = query.all()

        if not all_contests:
            print(f"ℹ️ No contests found with filters: platform={platform_filter}, time={time_filter}")
        else:
            print(f"✅ Found {len(all_contests)} contests from database")

        limited = []
        count_per_platform = defaultdict(int)

        for contest in all_contests:
            if count_per_platform[contest.resource] < 20:
                limited.append(contest.to_dict())
                count_per_platform[contest.resource] += 1

        return limited

    try:
        return safe_db_query(_query)
    except Exception as e:
        print(f"❌ Database query completely failed: {e}")
        return get_contests_from_memory_cache(platform_filter, time_filter)

def get_contests_from_memory_cache(platform_filter=None, time_filter=None):
    """Fallback: Get contests from in-memory cache"""
    print(" Using in-memory cache fallback")

    if not _cache['contests']:
        return []


# ========================================
# MAIN ROUTES
# ========================================
@app.route("/", methods=["GET"])
def index():
    platform_filter = request.args.getlist("platform")
    time_filter = request.args.get("time")

    # Use cached API call
    contests = fetch_contests_from_api()

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

        c['start_date'] = start_ist.strftime("%d-%m-%Y")
        c['start_time'] = start_ist.strftime("%H:%M")
        c['end_ist'] = end_ist.strftime("%H:%M")
        filtered.append(c)

    filtered.sort(key=lambda x: datetime.strptime(x['start_date'] + ' ' + x['start_time'], "%d-%m-%Y %H:%M"))

    # Limit to next 20 contests per platform
    limited = []
    count_per_platform = defaultdict(int)
    for c in filtered:
        if count_per_platform[c['resource']] < 20:
            limited.append(c)
            count_per_platform[c['resource']] += 1

    return render_template("index.html", contests=limited, platforms=platform_filter, time_filter=time_filter)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
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

    return render_template('contact.html')


# ========================================
# ADMIN ROUTES
# ========================================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('view_messages'))
        else:
            flash('Invalid credentials. Please try again.', 'error')

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/admin/messages')
@admin_required
def view_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin_messages.html', messages=messages)


@app.route('/admin/messages/<int:message_id>/mark-read', methods=['POST'])
@admin_required
def mark_message_read(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.read = True
    db.session.commit()
    flash('Message marked as read.', 'success')
    return redirect(url_for('view_messages'))


@app.route('/admin/messages/<int:message_id>/delete', methods=['POST'])
@admin_required
def delete_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted successfully.', 'success')
    return redirect(url_for('view_messages'))


# ========================================
# DATABASE CLI COMMANDS
# ========================================
@app.cli.command('init-db')
def init_db():
    db.create_all()
    print("✅ Database tables created successfully!")


@app.cli.command('drop-db')
def drop_db():
    db.drop_all()
    print("🗑️ Database tables dropped!")

@app.cli.command('seed-contests')
def seed_contests():
    """Manually fetch and seed contests from CList API"""
    print(" Seeding contests from CList API...")
    success = fetch_and_update_contests()
    if success:
        print(" Contests seeded successfully!")
    else:
        print(" Failed to seed contests!")


