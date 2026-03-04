from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from config import config
from models import db, User, Publication, ResearchArea, Message, ProfileInfo
from sqlalchemy.exc import OperationalError, SQLAlchemyError

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'admin_login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create upload folders
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static/uploads/pdfs', exist_ok=True)
    os.makedirs('static/uploads/images', exist_ok=True)
    
    # Helper function for allowed files
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    # ============ PUBLIC ROUTES ============
    
    @app.route('/')
    def index():
        """Homepage"""
        profile = ProfileInfo.query.first()
        featured_publications = Publication.query.order_by(Publication.citations.desc()).limit(6).all()
        research_areas = ResearchArea.query.all()
        
        # Calculate statistics
        total_pubs = Publication.query.count()
        total_citations = profile.total_citations if profile else 0
        
        return render_template('index.html', 
                             profile=profile,
                             featured_publications=featured_publications,
                             research_areas=research_areas,
                             total_pubs=total_pubs,
                             total_citations=total_citations)
    
    @app.route('/publications')
    def publications():
        """Publications page with filtering"""
        # Get filter parameters
        year_filter = request.args.get('year', type=int)
        area_filter = request.args.get('area', type=int)
        search_query = request.args.get('q', '')
        sort_by = request.args.get('sort', 'year')  # year, citations, title
        
        # Base query
        query = Publication.query
        
        # Apply filters
        if year_filter:
            query = query.filter(Publication.year == year_filter)
        
        if area_filter:
            query = query.join(Publication.research_areas).filter(ResearchArea.id == area_filter)
        
        if search_query:
            search = f"%{search_query}%"
            query = query.filter(
                db.or_(
                    Publication.title.ilike(search),
                    Publication.authors.ilike(search),
                    Publication.abstract.ilike(search)
                )
            )
        
        # Apply sorting
        if sort_by == 'citations':
            query = query.order_by(Publication.citations.desc())
        elif sort_by == 'title':
            query = query.order_by(Publication.title)
        else:  # year
            query = query.order_by(Publication.year.desc())
        
        pubs = query.all()
        
        # Get available years and research areas for filters
        years_query = db.session.query(Publication.year).distinct().order_by(Publication.year.desc()).all()
        years = [y[0] for y in years_query if y[0]]
        
        # Always include current year even if no publications yet
        from datetime import datetime
        current_year_val = datetime.now().year
        if current_year_val not in years:
            years.insert(0, current_year_val)
        
        research_areas = ResearchArea.query.all()
        
        return render_template('publications.html',
                             publications=pubs,
                             years=years,
                             research_areas=research_areas,
                             current_year=year_filter,
                             current_area=area_filter,
                             search_query=search_query,
                             sort_by=sort_by)
    
    @app.route('/publication/<int:pub_id>')
    def publication_detail(pub_id):
        """Individual publication detail page"""
        pub = Publication.query.get_or_404(pub_id)
        related_pubs = Publication.query.filter(
            Publication.id != pub_id,
            Publication.year.between(pub.year - 2, pub.year + 2)
        ).limit(3).all()
        
        return render_template('publication_detail.html', 
                             publication=pub,
                             related_publications=related_pubs)
    
    @app.route('/about')
    def about():
        """About page"""
        profile = ProfileInfo.query.first()
        research_areas = ResearchArea.query.all()
        return render_template('about.html', profile=profile, research_areas=research_areas)
    
    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        """Contact page"""
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            subject = request.form.get('subject')
            message_text = request.form.get('message')
            
            if name and email and message_text:
                message = Message(
                    name=name,
                    email=email,
                    subject=subject,
                    message=message_text
                )
                db.session.add(message)
                db.session.commit()
                flash('Thank you for your message! I will get back to you soon.', 'success')
                return redirect(url_for('contact'))
            else:
                flash('Please fill in all required fields.', 'error')
        
        profile = ProfileInfo.query.first()
        return render_template('contact.html', profile=profile)
    
    # ============ API ROUTES ============
    
    @app.route('/api/publications')
    def api_publications():
        """API endpoint for publications data"""
        pubs = Publication.query.all()
        return jsonify([{
            'id': p.id,
            'title': p.title,
            'year': p.year,
            'citations': p.citations,
            'authors': p.authors
        } for p in pubs])
    
    @app.route('/api/citation-stats')
    def api_citation_stats():
        """API endpoint for citation statistics by year"""
        # Group publications by year and sum citations
        stats = db.session.query(
            Publication.year,
            db.func.count(Publication.id).label('count'),
            db.func.sum(Publication.citations).label('total_citations')
        ).group_by(Publication.year).order_by(Publication.year).all()
        
        return jsonify([{
            'year': s[0],
            'publications': s[1],
            'citations': s[2] or 0
        } for s in stats])
    
    # ============ ADMIN ROUTES ============
    
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Admin login page"""
        if current_user.is_authenticated:
            return redirect(url_for('admin_dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('admin_dashboard'))
            else:
                flash('Invalid username or password', 'error')
        
        return render_template('admin/login.html')
    
    @app.route('/admin/logout')
    @login_required
    def admin_logout():
        """Admin logout"""
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('index'))
    
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        """Admin dashboard"""
        total_publications = Publication.query.count()
        total_messages = Message.query.count()
        unread_messages = Message.query.filter_by(read=False).count()
        profile = ProfileInfo.query.first()
        total_citations = profile.total_citations if profile else 0
        research_areas_count = ResearchArea.query.count()
        
        recent_messages = Message.query.order_by(Message.created_at.desc()).limit(5).all()
        recent_publications = Publication.query.order_by(Publication.created_at.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html',
                             total_publications=total_publications,
                             total_messages=total_messages,
                             unread_messages=unread_messages,
                             total_citations=total_citations,
                             research_areas_count=research_areas_count,
                             recent_messages=recent_messages,
                             recent_publications=recent_publications)
    
    @app.route('/admin/publications')
    @login_required
    def admin_publications():
        """Admin publications management"""
        pubs = Publication.query.order_by(Publication.created_at.desc()).all()
        return render_template('admin/publications.html', publications=pubs)
    
    @app.route('/admin/publication/add', methods=['GET', 'POST'])
    @login_required
    def admin_add_publication():
        """Add new publication"""
        if request.method == 'POST':
            title = request.form.get('title')
            authors = request.form.get('authors')
            venue = request.form.get('venue')
            year = request.form.get('year', type=int)
            citations = request.form.get('citations', type=int, default=0)
            abstract = request.form.get('abstract')
            doi = request.form.get('doi')
            google_scholar_url = request.form.get('google_scholar_url')
            pdf_url = request.form.get('pdf_url')
            
            # Handle thumbnail upload
            thumbnail_file = request.files.get('thumbnail')
            thumbnail_filename = None
            
            if thumbnail_file and allowed_file(thumbnail_file.filename):
                thumbnail_filename = secure_filename(thumbnail_file.filename)
                thumbnail_file.save(os.path.join('static/uploads/images', thumbnail_filename))
            
            pub = Publication(
                title=title,
                authors=authors,
                venue=venue,
                year=year,
                citations=citations,
                abstract=abstract,
                doi=doi,
                google_scholar_url=google_scholar_url,
                pdf_url=pdf_url,
                thumbnail=thumbnail_filename
            )
            
            # Handle research areas
            selected_areas = request.form.getlist('research_areas')
            for area_id in selected_areas:
                area = ResearchArea.query.get(int(area_id))
                if area:
                    pub.research_areas.append(area)
            
            db.session.add(pub)
            db.session.commit()
            
            flash('Publication added successfully!', 'success')
            return redirect(url_for('admin_publications'))
        
        research_areas = ResearchArea.query.all()
        return render_template('admin/publication_form.html', research_areas=research_areas)
    
    @app.route('/admin/publication/edit/<int:pub_id>', methods=['GET', 'POST'])
    @login_required
    def admin_edit_publication(pub_id):
        """Edit publication"""
        pub = Publication.query.get_or_404(pub_id)
        
        if request.method == 'POST':
            pub.title = request.form.get('title')
            pub.authors = request.form.get('authors')
            pub.venue = request.form.get('venue')
            pub.year = request.form.get('year', type=int)
            pub.citations = request.form.get('citations', type=int)
            pub.abstract = request.form.get('abstract')
            pub.doi = request.form.get('doi')
            pub.google_scholar_url = request.form.get('google_scholar_url')
            pub.pdf_url = request.form.get('pdf_url')
            
            # Handle thumbnail upload
            thumbnail_file = request.files.get('thumbnail')
            
            if thumbnail_file and allowed_file(thumbnail_file.filename):
                thumbnail_filename = secure_filename(thumbnail_file.filename)
                thumbnail_file.save(os.path.join('static/uploads/images', thumbnail_filename))
                pub.thumbnail = thumbnail_filename
            
            # Handle research areas
            pub.research_areas = []
            selected_areas = request.form.getlist('research_areas')
            for area_id in selected_areas:
                area = ResearchArea.query.get(int(area_id))
                if area:
                    pub.research_areas.append(area)
            
            db.session.commit()
            flash('Publication updated successfully!', 'success')
            return redirect(url_for('admin_publications'))
        
        research_areas = ResearchArea.query.all()
        return render_template('admin/publication_form.html', publication=pub, research_areas=research_areas)
    
    @app.route('/admin/publication/delete/<int:pub_id>', methods=['POST'])
    @login_required
    def admin_delete_publication(pub_id):
        """Delete publication"""
        pub = Publication.query.get_or_404(pub_id)
        db.session.delete(pub)
        db.session.commit()
        flash('Publication deleted successfully!', 'success')
        return redirect(url_for('admin_publications'))
    
    @app.route('/admin/messages')
    @login_required
    def admin_messages():
        """Admin messages inbox"""
        messages = Message.query.order_by(Message.created_at.desc()).all()
        return render_template('admin/messages.html', messages=messages)
    
    @app.route('/admin/message/<int:msg_id>/mark-read', methods=['POST'])
    @login_required
    def admin_mark_read(msg_id):
        """Mark message as read"""
        message = Message.query.get_or_404(msg_id)
        message.read = True
        db.session.commit()
        return jsonify({'success': True})
    
    @app.route('/admin/profile', methods=['GET', 'POST'])
    @login_required
    def admin_profile():
        """Edit profile information"""
        profile = ProfileInfo.query.first()
        if not profile:
            profile = ProfileInfo(full_name="Researcher Name")
            db.session.add(profile)
            db.session.commit()
        
        if request.method == 'POST':
            profile.full_name = request.form.get('full_name')
            profile.title = request.form.get('title')
            profile.affiliation = request.form.get('affiliation')
            profile.bio = request.form.get('bio')
            profile.email = request.form.get('email')
            profile.phone = request.form.get('phone')
            profile.linkedin_url = request.form.get('linkedin_url')
            profile.google_scholar_url = request.form.get('google_scholar_url')
            profile.github_url = request.form.get('github_url')
            profile.twitter_url = request.form.get('twitter_url')
            profile.total_citations = request.form.get('total_citations', type=int, default=0)
            profile.h_index = request.form.get('h_index', type=int, default=0)
            profile.i10_index = request.form.get('i10_index', type=int, default=0)
            
            # Handle profile image upload
            profile_image = request.files.get('profile_image')
            if profile_image and allowed_file(profile_image.filename):
                image_filename = secure_filename(profile_image.filename)
                profile_image.save(os.path.join('static/uploads/images', image_filename))
                profile.profile_image = image_filename
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('admin_profile'))
        
        return render_template('admin/profile_form.html', profile=profile)
    
    @app.route('/admin/import-scholar', methods=['GET', 'POST'])
    @login_required
    def admin_import_scholar():
        """Import publications from Google Scholar"""
        from scholar_utils import scrape_google_scholar, categorize_publication
        
        results = None
        scholar_url = None
        
        if request.method == 'POST':
            scholar_url = request.form.get('scholar_url', '').strip()
            
            if not scholar_url:
                flash('Please enter a Google Scholar profile URL', 'error')
                return render_template('admin/import_scholar.html', scholar_url=scholar_url)
            
            # Scrape publications
            publications_data = scrape_google_scholar(scholar_url)
            
            # Check for errors
            if isinstance(publications_data, dict) and 'error' in publications_data:
                flash(f'Error scraping Google Scholar: {publications_data["error"]}', 'error')
                return render_template('admin/import_scholar.html', scholar_url=scholar_url)
            
            if not publications_data:
                flash('No publications found at this URL', 'warning')
                return render_template('admin/import_scholar.html', scholar_url=scholar_url)
            
            # Get research areas for categorization
            research_areas = ResearchArea.query.all()
            
            added_count = 0
            skipped_count = 0
            pub_results = []
            
            for pub_data in publications_data:
                # Check if publication already exists
                existing = Publication.query.filter_by(title=pub_data['title']).first()
                
                if existing:
                    skipped_count += 1
                    pub_results.append({
                        'title': pub_data['title'],
                        'year': pub_data['year'],
                        'status': 'skipped'
                    })
                    continue
                
                # Create new publication
                publication = Publication(
                    title=pub_data['title'],
                    authors=pub_data['authors'],
                    venue=pub_data['venue'],
                    year=pub_data['year'],
                    citations=pub_data['citations'],
                    google_scholar_url=pub_data.get('google_scholar_url')
                )
                
                # Auto-assign research areas
                matched_areas = categorize_publication(pub_data, research_areas)
                publication.research_areas.extend(matched_areas)
                
                db.session.add(publication)
                added_count += 1
                pub_results.append({
                    'title': pub_data['title'],
                    'year': pub_data['year'],
                    'status': 'added'
                })
            
            try:
                db.session.commit()
                flash(f'Successfully imported {added_count} publications! ({skipped_count} duplicates skipped)', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving publications: {str(e)}', 'error')
                return render_template('admin/import_scholar.html', scholar_url=scholar_url)
            
            results = {
                'total': len(publications_data),
                'added': added_count,
                'skipped': skipped_count,
                'publications': pub_results
            }
        
        return render_template('admin/import_scholar.html', 
                             scholar_url=scholar_url,
                             results=results)
    
    # ============ ERROR HANDLERS ============
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(OperationalError)
    @app.errorhandler(SQLAlchemyError)
    def db_error(error):
        """Handle Database Errors (e.g. connection refused)"""
        db.session.rollback()
        return render_template('errors/db_error.html'), 503
    
    # Register blueprints
    from demos import demos_bp
    app.register_blueprint(demos_bp)
    
    return app
app = create_app()

if __name__ == '__main__':
    app.run()
    
    with app.app_context():
        try:
            db.create_all()
            
            # Create default admin user if not exists
            if not User.query.filter_by(username=app.config['ADMIN_USERNAME']).first():
                admin = User(username=app.config['ADMIN_USERNAME'])
                admin.set_password(app.config['ADMIN_PASSWORD'])
                db.session.add(admin)
                db.session.commit()
                print(f"Created admin user: {app.config['ADMIN_USERNAME']}")
        except (OperationalError, SQLAlchemyError) as e:
            print(f"WARNING: Database connection failed during startup. The app will start, but database features will return 503 errors.\nError: {e}")
    
    # Configure Flask to exclude site-packages from file watching
    # This prevents TensorFlow imports from triggering infinite restarts
    import sys
    exclude_patterns = [
        '*site-packages*',
        '*tensorflow*',
        '*keras*',
        '*.pyc',
        '*__pycache__*'
    ]
    
    port = int(os.environ.get('PORT', 5000))
    app.run( 
        host='0.0.0.0', 
        port=port,
        extra_files=[],  # Don't watch extra files
        reloader_type='stat'  # Use stat reloader instead of watchdog (more stable)
    )
