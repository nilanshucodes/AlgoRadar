from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta
import pytz
from collections import defaultdict

app = Flask(__name__)

# Your CList API key
API_KEY = "b9e571e435c1f386872b651fc683c0bbf80ecc1a"
USERNAME = "nilanshucodes"

# Timezone conversion: UTC → IST
IST = pytz.timezone('Asia/Kolkata')


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

    # Limit to next 20 contests  per platform
    limited = []
    count_per_platform = defaultdict(int)
    for c in filtered:
        if count_per_platform[c['resource']] < 20:
            limited.append(c)
            count_per_platform[c['resource']] += 1

    return render_template("index.html", contests=limited, platforms=platform_filter, time_filter=time_filter)


if __name__ == "__main__":
    app.run(debug=True)
