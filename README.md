
# AlgoRadar 🎯

A modern, lightweight competitive programming contest tracker that aggregates upcoming contests from multiple platforms in one clean interface.

## Why AlgoRadar?

While platforms like CList exist, AlgoRadar offers a focused, streamlined experience for competitive programmers who want quick access to contest information without the clutter.

### AlgoRadar vs CList

| Feature | AlgoRadar | CList |
|---------|-----------|-------|
| **Interface** | Clean, minimalist design | Feature-rich but complex |
| **Speed** | Fast loading with caching | Can be slower |
| **Focus** | Contests only | Contests + ratings + statistics |
| **Mobile Experience** | Fully responsive, card view | Mobile-friendly but dense |
| **Dark Mode** | Built-in toggle | Available |
| **Filters** | Simple platform & time filters | Advanced filtering options |
| **User Accounts** | Not required | Required for full features |
| **Ads** | None | Present |
| **Setup** | Self-hostable, free | Hosted service |
| **Customization** | Full control (open source) | Limited |
| **Data Privacy** | Your own instance | Third-party service |

**Use AlgoRadar if you want:**
- Quick contest lookups without account creation
- Clean, distraction-free interface
- Self-hosted solution
- Privacy-focused tracking

**Use CList if you need:**
- Historical rating data
- Detailed statistics
- Social features
- Profile tracking across platforms

## Features

- **Multi-Platform Support**: Codeforces, CodeChef, AtCoder, LeetCode, and more
- **Smart Filtering**: Filter by platform and timeframe (today/week/month)
- **Caching System**: Reduces API calls, faster load times
- **Dark Mode**: Easy on the eyes during late-night coding sessions
- **Responsive Design**: Seamless experience on desktop and mobile
- **Admin Panel**: Manage contact form submissions
- **Contact Form**: Persistent storage for user messages

## Screenshots

*(Add screenshots here)*

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy (PostgreSQL/SQLite)
- **Caching**: Flask-Caching
- **Frontend**: Vanilla JavaScript, CSS3
- **API**: CList API v2

## Installation

### Prerequisites
- Python 3.9+
- pip
- Git

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/algoradar.git
cd algoradar
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key-here
CLIST_API_KEY=your-clist-api-key
CLIST_USERNAME=your-clist-username
DATABASE_URL=sqlite:///fallback.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
```

**Get CList API credentials:**
- Register at [clist.by](https://clist.by/)
- Go to Settings → API
- Generate your API key

5. **Initialize database**
```bash
flask init-db
```

6. **Run the application**
```bash
python app.py
```

Visit `http://localhost:5000`

## Deployment

### Deploy on Render

1. **Prepare `requirements.txt`** (already included)

2. **Push to GitHub** (with `.gitignore` configured)

3. **Create Web Service on Render**
   - Connect your GitHub repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

4. **Add PostgreSQL Database**
   - Create new PostgreSQL instance
   - Link to web service

5. **Configure Environment Variables**
   - Add all variables from `.env`
   - `DATABASE_URL` is auto-configured

6. **Initialize Database** (one-time)
```bash
# In Render Shell
flask init-db
```

**Detailed deployment guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)

## Project Structure

```
algoradar/
├── app.py                      # Main application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── static/
│   ├── style.css              # Styles
│   ├── script.js              # Client-side logic
│   └── images/                # Logo and assets
├── templates/
│   ├── base.html              # Base template
│   ├── index.html             # Contest listing
│   ├── contact.html           # Contact form
│   ├── admin_login.html       # Admin authentication
│   └── admin_messages.html    # Message management
└── instance/
    └── fallback.db            # SQLite database (local)
```

## Usage

### For Users

1. **View Contests**: Homepage shows upcoming contests
2. **Filter**: Use platform checkboxes and time dropdown
3. **Dark Mode**: Toggle with sun/moon button
4. **Contact**: Use contact form for feedback

### For Admins

1. **Access Admin Panel**: Navigate to `/admin/login`
2. **View Messages**: See all contact form submissions
3. **Manage**: Mark as read or delete messages
4. **Logout**: Secure session management

## API Rate Limiting

AlgoRadar implements caching to respect CList API limits:
- Cache TTL: 10 minutes
- Reduces redundant API calls
- Improves response times

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Contest data provided by [CList API](https://clist.by/)
- Built for competitive programming community

## Contact

**Project Maintainer**: Nilanshu
- GitHub: [@nilanshucodes](https://github.com/nilanshucodes)


**Live Demo**: [https://algoradar.onrender.com](https://algoradar.onrender.com)

---

Made with ❤️ for competitive programmers
```
