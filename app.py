from flask import Flask, render_template, request, flash, redirect, url_for
import requests
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env

app = Flask(__name__)
load_dotenv(dotenv_path="/Users/nilanshu/Desktop/contest_tracker_fallback/.env", override=True)# override=True ensures old env vars are replaced
app.secret_key = os.getenv("SECRET_KEY")
# Your CList API key
API_KEY =os.getenv("CLIST_API_KEY")
USERNAME = os.getenv("CLIST_USERNAME")

# Timezone conversion: UTC → IST
IST = pytz.timezone('Asia/Kolkata')


# Make datetime available in all templates
@app.context_processor
def inject_now():
    now_ist = datetime.now(IST)
    return {
        'datetime': datetime,
        'now_ist': now_ist
    }


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

        # Save contact submission
        try:
            save_contact_to_file(name, email, message)
            flash('Thank you for contacting us! We\'ll get back to you soon.', 'success')

            # Optional: Send email notification
            # Uncomment the line below if you set up email
            # send_email_notification(name, email, message)

        except Exception as e:
            print(f"Error saving contact: {e}")
            flash('There was an error processing your request. Please try again.', 'error')

        return redirect(url_for('contact'))

    # GET request - show the contact form
    return render_template('contact.html')


def save_contact_to_file(name, email, message):
    """
    Save contact form submission to a text file.
    This is a simple method good for small-scale deployments.
    For production, consider using a database.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        with open('contact_submissions.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Name: {name}\n")
            f.write(f"Email: {email}\n")
            f.write(f"Message:\n{message}\n")
            f.write(f"{'=' * 60}\n")
    except Exception as e:
        print(f"Error writing to file: {e}")
        raise

if __name__ == "__main__":
    app.run(debug=True)
