# AlgoRadar 🎯

A clean, fast competitive programming contest tracker. Never miss a coding competition again.

**Live Demo** • **[Report Bug](https://github.com/nilanshucodes/algoradar/issues)** • **[Request Feature](https://github.com/nilanshucodes/algoradar/issues)**

---

## Features

- **Multi-Platform**: Codeforces, CodeChef, AtCoder, LeetCode in one place
- **Smart Caching**: 10-minute cache handles API rate limits (10 req/min) for unlimited users
- **Dual Views**: Table view (desktop) and card view (mobile)
- **Filters**: By platform and time (today/week/month)
- **Dark Mode**: Toggle with persistent preference
- **IST Timezone**: All times converted automatically
- **Contact Form**: PostgreSQL-backed message storage

---

## Why AlgoRadar vs CList?

| Feature | AlgoRadar | CList.by |
|---------|-----------|----------|
| UI | Minimal, fast | Feature-rich, complex |
| Platforms | 4 major ones | 300+ (overwhelming) |
| Speed | Cached, instant filters | Real-time API (slower) |
| Mobile | Optimized card view | Desktop-first |
| Setup | Zero config | Requires account |

**TL;DR**: AlgoRadar is simpler, faster, and focused on what matters.

---

## Quick Start

```bash
# Clone
git clone https://github.com/nilanshucodes/algoradar.git
cd algoradar

# Install
pip install -r requirements.txt

# Configure .env
CLIST_API_KEY=your_key
CLIST_USERNAME=your_username
SECRET_KEY=your_secret
DATABASE_URL=postgresql://user:pass@localhost/algoradar

# Initialize DB
flask init-db

# Run
python app.py
```

Get CList API key: https://clist.by/api/v2/doc/

---

## How It Works

### Caching System
```
Request → Cache Check → Hit? Serve instantly
                      ↓ Miss? Call API → Cache 10min → Serve
```

**Result**: 1 API call serves all users for 10 minutes. No rate limit issues.

### Tech Stack
- Flask + PostgreSQL + SQLAlchemy
- Flask-Caching (upgradeable to Redis)
- CList API v2
- Vanilla JS (no frameworks)

---

## Deployment

### Render (Recommended)
1. Create PostgreSQL database (free tier)
2. Create Web Service from GitHub
3. Add env vars: `DATABASE_URL`, `SECRET_KEY`, `CLIST_API_KEY`, `CLIST_USERNAME`
4. Deploy

### Railway
1. New Project → GitHub
2. Add PostgreSQL plugin
3. Set env vars
4. Deploy

Both platforms have free tiers.

---

## Project Structure

```
algoradar/
├── app.py                # Main application
├── templates/
│   ├── base.html        # Header/footer/dark mode
│   ├── index.html       # Contest listing
│   ├── contact.html     # Contact form
│   └── admin_messages.html
├── static/
│   ├── style.css
│   └── images/          # Platform logos
└── requirements.txt
```

---

## Key Features Explained

**1. Shared Cache**
- All users share one cached dataset
- Refreshes every 10 minutes automatically
- Filtering happens on cached data (instant)

**2. Dual View System**
- Desktop: Sortable table with all details
- Mobile: Platform-colored cards (auto-switches)
- Manual toggle available

**3. Smart Filtering**
- Platform: Checkbox selection
- Time: Today/Week/Month/All
- Zero latency (works on cached data)

**4. Contact System**
- Form validation (name, email, message)
- Stores in PostgreSQL
- View at `/admin/messages` (add auth before production!)

---

## Configuration

**Cache duration** (app.py):
```python
'CACHE_DEFAULT_TIMEOUT': 600  # Change to desired seconds
```

**Contests per platform** (app.py):
```python
if count_per_platform[c['resource']] < 20:  # Change limit
```

**Upgrade to Redis**:
```python
cache = Cache(app, config={
    'CACHE_TYPE': 'RedisCache',
    'CACHE_REDIS_URL': os.getenv('REDIS_URL')
})
```

---

## Contributing

PRs welcome! Focus areas:
- More platforms
- User accounts (save favorites)
- Email notifications
- Admin authentication
- Calendar export

---

## Roadmap

- [ ] User authentication
- [ ] Contest reminders
- [ ] Email notifications
- [ ] Multi-timezone support
- [ ] Visit analytics
- [ ] Mobile app

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Author

**Nilanshu Sharma**  
[GitHub](https://github.com/nilanshucodes) • [LinkedIn](https://linkedin.com/in/nilanshusharma) • [Email](mailto:nilanshucodes@gmail.com)

---

**Made with ❤️ for the CP community**
