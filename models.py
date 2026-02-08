from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Admin user model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Publication(db.Model):
    """Research publication model"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    authors = db.Column(db.Text, nullable=False)
    venue = db.Column(db.String(300))  # Journal/Conference name
    year = db.Column(db.Integer, nullable=False)
    citations = db.Column(db.Integer, default=0)
    abstract = db.Column(db.Text)
    pdf_url = db.Column(db.String(500))
    pdf_filename = db.Column(db.String(255))
    doi = db.Column(db.String(200))
    google_scholar_url = db.Column(db.String(500))
    thumbnail = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    research_areas = db.relationship('ResearchArea', secondary='publication_research_area', back_populates='publications')
    
    def __repr__(self):
        return f'<Publication {self.title[:50]}>'

class ResearchArea(db.Model):
    """Research area/topic model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100))  # Font Awesome icon class
    color = db.Column(db.String(20))  # Hex color code
    
    # Relationships
    publications = db.relationship('Publication', secondary='publication_research_area', back_populates='research_areas')
    
    def __repr__(self):
        return f'<ResearchArea {self.name}>'

# Association table for many-to-many relationship
publication_research_area = db.Table('publication_research_area',
    db.Column('publication_id', db.Integer, db.ForeignKey('publication.id'), primary_key=True),
    db.Column('research_area_id', db.Integer, db.ForeignKey('research_area.id'), primary_key=True)
)

class Message(db.Model):
    """Contact form message model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message from {self.name}>'

class ProfileInfo(db.Model):
    """Researcher profile information (singleton)"""
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(200))  # e.g., "MBA - Business Analytics"
    affiliation = db.Column(db.String(300))
    bio = db.Column(db.Text)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    linkedin_url = db.Column(db.String(300))
    google_scholar_url = db.Column(db.String(300))
    github_url = db.Column(db.String(300))
    twitter_url = db.Column(db.String(300))
    profile_image = db.Column(db.String(255))
    cv_filename = db.Column(db.String(255))
    
    # Citation metrics
    total_citations = db.Column(db.Integer, default=0)
    h_index = db.Column(db.Integer, default=0)
    i10_index = db.Column(db.Integer, default=0)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProfileInfo {self.full_name}>'
