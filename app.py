from flask import Flask, render_template, request, flash, redirect, url_for, session
from functools import wraps
import requests
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
API_KEY = os.getenv("CLIST_API_KEY")
USERNAME = os.getenv("CLIST_USERNAME")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://','postgresql://',1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///fallback.db'
db = SQLAlchemy(app)

cache = Cache(app,config={'CACHE_TYPE':'SimpleCache','CACHE_DEFAULT_TIMEOUT':600})
IST = pytz.timezone('Asia/Kolkata')

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(120),nullable=False)
    message = db.Column(db.Text,nullable=False)
    created_at = db.Column(db.DateTime,nullable=False,default=lambda: datetime.now(IST))
    read = db.Column(db.Boolean,default=False,nullable=False)

    def __repr__(self):
        return f'<ContactMessage {self.name}  - {self.email}>'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin panel.','error')
            return redirect(url_for('admin_login'))
        return f(*args,**kwargs)
    return decorated_function

@app.context_processor
def inject_now():
    now_ist = datetime.now(IST)
    return {'datetime': datetime,'now_ist': now_ist}

@cache.cached(timeout=600,key_prefix='all_contests')
def fetch_contests_from_api():
    url = f"https://clist.by/api/v2/contest/?username={USERNAME}&api_key={API_KEY}&upcoming=true&limit=500&order_by=start"
    try:
        print("Fetching fresh data from CList API")
        response = requests.get(url,timeout=10)
        response.raise_for_status()
        contests = response.json().get("objects",[])
        print(f"Fetched {len(contests)}contests from API")
        return contests
    except requests.RequestException as e:
        print(f"Error fetching contests:{e}")
        return []

@app.route("/", methods=["GET"])
def index():
    platform_filter = request.args.getlist("platform")
    time_filter = request.args.get("time")

    #usin cached api call
    contests = fetch_contests_from_api()

    filtered = []
    for c in contests:
        resource = c['resource'].lower() if isinstance(c['resource'], str) else str(c['resource']).lower()
        if platform_filter and resource not in [p.lower() for p in platform_filter]:
            continue
            
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

    filtered.sort(key=lambda x: datetime.strptime(x['start_date']+' '+x['start_time'],"%d-%m-%Y %H:%M"))

    #limitin to next 20 contest/platform
    limited = []
    count_per_platform = defaultdict(int)
    for c in filtered:
        if count_per_platform[c['resource']] <20:
            limited.append(c)
            count_per_platform[c['resource']]+= 1

    return render_template("index.html",contests=limited,platforms=platform_filter,time_filter=time_filter)

@app.route('/contact',methods=['GET','POST'])
def contact():
    if request.method =='POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip()
        message = request.form.get('message','').strip()
        
        if not name or not email or not message:
            flash('All fields are required!','error')
            return redirect(url_for('contact'))
        if len(name) <2:
            flash('Name must be at least 2 characters long.','error')
            return redirect(url_for('contact'))
        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address.','error')
            return redirect(url_for('contact'))
        if len(message) <10:
            flash('Message must be at least 10 characters long.','error')
            return redirect(url_for('contact'))
        try:
            new_message = ContactMessage(name=name,email=email,message=message)
            db.session.add(new_message)
            db.session.commit()
            flash('Thank you for contacting us! We\'ll get back to you soon.','success')
            print(f"New contact message from {name} ({email})")
        except Exception as e:
            db.session.rollback()
            print(f"Error saving contact message: {e}")
            flash('There was error processing your request. Please try again.','error')
            
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username','')
        password = request.form.get('password','')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Successfully logged in!','success')
            return redirect(url_for('view_messages'))
        else:
            flash('Invalid credentials. Please try again.','error')

    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in',None)
    flash('You have been logged out.','success')
    return redirect(url_for('index'))

@app.route('/admin/messages')
@admin_required
def view_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin_messages.html', messages=messages)

@app.route('/admin/messages/<int:message_id>/mark-read',methods=['POST'])
@admin_required
def mark_message_read(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.read = True
    db.session.commit()
    flash('Message marked as read.','success')
    return redirect(url_for('view_messages'))

@app.route('/admin/messages/<int:message_id>/delete',methods=['POST'])
@admin_required
def delete_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted successfully.','success')
    return redirect(url_for('view_messages'))

@app.cli.command('init-db')
def init_db():
    db.create_all()
    print("Database tables created successfully!")
    
@app.cli.command('drop-db')
def drop_db():
    db.drop_all()
    print("Database tables dropped!")
