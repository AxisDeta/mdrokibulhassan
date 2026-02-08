# Academic Portfolio - Faiaz Rahat Chowdhury

A premium Flask-based academic portfolio website showcasing research publications, citations, and professional achievements in Business Analytics, Data Science, and Machine Learning.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### Public Features
- **Modern Homepage** with animated statistics and featured publications
- **Publications Page** with advanced search, filtering, and sorting
- **Research Areas** visualization with custom icons and colors
- **About Page** with biography and education timeline
- **Contact Form** with validation and database storage
- **Dark/Light Theme** toggle with localStorage persistence
- **Fully Responsive** design for all devices

### Admin Features
- **Secure Authentication** with Flask-Login
- **Publication Management** (Create, Read, Update, Delete)
- **File Upload** support for PDFs and images
- **Profile Management** for researcher information
- **Message Inbox** for contact form submissions
- **Dashboard** with analytics and recent activity

### Technical Features
- **SQLAlchemy ORM** for database management
- **RESTful API** endpoints for data access
- **Citation Metrics** tracking (h-index, i10-index)
- **Google Scholar** integration
- **Smooth Animations** and micro-interactions
- **SEO Optimized** with meta tags

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
cd Research-Paper-Tool
```

2. **Create a virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
# Copy the example file
copy .env.example .env

# Edit .env and update the values
# Especially change SECRET_KEY and ADMIN_PASSWORD
```

5. **Initialize the database**
```bash
python init_db.py
```

6. **Run the application**
```bash
python app.py
```

7. **Access the website**
- Homepage: http://localhost:5000
- Admin Panel: http://localhost:5000/admin/login

### Default Admin Credentials
- Username: `admin`
- Password: `admin123` (change this in `.env`)

## 📁 Project Structure

```
Research-Paper-Tool/
├── app.py                      # Main Flask application
├── models.py                   # Database models
├── config.py                   # Configuration settings
├── init_db.py                  # Database initialization
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── static/
│   ├── css/
│   │   └── style.css          # Main stylesheet
│   ├── js/
│   │   └── main.js            # JavaScript functionality
│   ├── images/                # Static images
│   └── uploads/               # User-uploaded files
│       ├── pdfs/              # Publication PDFs
│       └── images/            # Thumbnails and profile images
├── templates/
│   ├── base.html              # Base template
│   ├── index.html             # Homepage
│   ├── publications.html      # Publications list
│   ├── about.html             # About page
│   ├── contact.html           # Contact form
│   └── admin/                 # Admin panel templates
│       └── login.html         # Admin login
└── portfolio.db               # SQLite database (created on init)
```

## 🎨 Customization

### Update Profile Information
1. Login to admin panel: http://localhost:5000/admin/login
2. Navigate to Profile settings
3. Update your information, upload profile image
4. Save changes

### Add Publications
1. Login to admin panel
2. Go to Publications → Add New
3. Fill in publication details
4. Upload PDF and thumbnail (optional)
5. Submit

### Customize Theme Colors
Edit `static/css/style.css` and modify the CSS variables:
```css
:root {
    --primary-color: #1e40af;      /* Main blue */
    --secondary-color: #f59e0b;    /* Accent gold */
    /* ... other colors ... */
}
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file with the following:

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///portfolio.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
```

### Production Deployment

For production, update `.env`:
```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@host/dbname
```

And use a production server like Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 📊 Database Schema

### Tables
- **User**: Admin authentication
- **ProfileInfo**: Researcher profile and metrics
- **Publication**: Research papers and articles
- **ResearchArea**: Research topics and interests
- **Message**: Contact form submissions

## 🛠️ Development

### Adding New Features
1. Create new routes in `app.py`
2. Add database models in `models.py`
3. Create templates in `templates/`
4. Add styles in `static/css/style.css`
5. Add JavaScript in `static/js/main.js`

### Database Migrations
```bash
# Create migration
flask db migrate -m "Description"

# Apply migration
flask db upgrade
```

## 📝 API Endpoints

### Public API
- `GET /api/publications` - List all publications
- `GET /api/citation-stats` - Citation statistics by year

### Admin API (requires authentication)
- `POST /admin/publication/add` - Add publication
- `POST /admin/publication/edit/<id>` - Edit publication
- `POST /admin/publication/delete/<id>` - Delete publication

## 🎯 Features Roadmap

- [ ] Export publications to BibTeX
- [ ] Advanced citation analytics
- [ ] Co-author network visualization
- [ ] Blog/News section
- [ ] Multi-language support
- [ ] Google Analytics integration

## 🐛 Troubleshooting

### Database Issues
```bash
# Reset database
rm portfolio.db
python init_db.py
```

### Port Already in Use
Change the port in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

## 📄 License

This project is licensed under the MIT License.

## 👤 Author

**Faiaz Rahat Chowdhury**
- LinkedIn: [faiaz-chowdhury](http://www.linkedin.com/in/faiaz-chowdhury)
- Google Scholar: [Profile](https://scholar.google.com/citations?user=j3B8Dz8AAAAJ&hl=en)

## 🙏 Acknowledgments

- Built with Flask and modern web technologies
- Icons by Font Awesome
- Fonts by Google Fonts
- Designed by Antigravity AI

---

**Note**: This is a premium academic portfolio template. Customize it to match your personal brand and research focus.
