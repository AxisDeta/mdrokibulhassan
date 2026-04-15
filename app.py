from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from config import config
from models import db, User, Publication, ResearchArea, Message, ProfileInfo
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from scholar_utils import (
    ScholarSyncError,
    attempt_cached_profile_image_refresh,
    get_scholar_sync_status,
    is_sync_stale,
    sync_profile_and_publications,
    update_scholar_sync_status,
)

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

    def resolve_profile_image(profile_image):
        # Always prefer a local override if it exists to avoid stale remote URLs.
        override_path = os.path.join('static', 'uploads', 'images', 'profile.jpg')
        if os.path.exists(override_path):
            cache_buster = int(os.path.getmtime(override_path))
            return url_for('static', filename='uploads/images/profile.jpg', v=cache_buster)

        if not profile_image:
            return None
        if profile_image.startswith('http://') or profile_image.startswith('https://'):
            return profile_image
        static_path = os.path.join('static', 'uploads', 'images', profile_image)
        cache_buster = None
        try:
            cache_buster = int(os.path.getmtime(static_path))
        except OSError:
            cache_buster = None
        return url_for('static', filename=f'uploads/images/{profile_image}', v=cache_buster)

    def maybe_sync_scholar_profile(force=False):
        profile = ProfileInfo.query.first()
        if not profile or not profile.google_scholar_url:
            return None

        if not force and not is_sync_stale():
            return get_scholar_sync_status()

        try:
            result = sync_profile_and_publications(
                profile=profile,
                db=db,
                Publication=Publication,
                ResearchArea=ResearchArea,
                force=force,
            )
            return result
        except ScholarSyncError as exc:
            app.logger.warning('Google Scholar sync skipped: %s', exc)
            update_scholar_sync_status(last_attempt_at=None, last_status='error', last_error=str(exc))
            return {'status': 'error', 'message': str(exc), 'stats': get_scholar_sync_status().get('stats', {})}
        except Exception as exc:
            app.logger.exception('Unexpected Google Scholar sync failure')
            update_scholar_sync_status(last_attempt_at=None, last_status='error', last_error=str(exc))
            return {'status': 'error', 'message': str(exc), 'stats': get_scholar_sync_status().get('stats', {})}

    @app.context_processor
    def inject_profile_helpers():
        profile = ProfileInfo.query.first()
        return {
            'site_profile': profile,
            'profile_image_src': resolve_profile_image(profile.profile_image) if profile else None,
            'scholar_sync_status': get_scholar_sync_status(),
        }

    @app.before_request
    def auto_sync_google_scholar():
        if request.method != 'GET':
            return None

        public_endpoints = {'index', 'about', 'publications', 'publication_detail', 'contact'}
        if request.endpoint in public_endpoints:
            profile = ProfileInfo.query.first()
            if profile:
                attempt_cached_profile_image_refresh(profile)
                if db.session.is_modified(profile):
                    db.session.commit()
            maybe_sync_scholar_profile(force=False)

        return None
    
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
                             recent_publications=recent_publications,
                             profile=profile,
                             scholar_sync_status=get_scholar_sync_status())
    
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
            attempt_cached_profile_image_refresh(profile)
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
        """Sync publications and profile data from Google Scholar."""
        results = None
        profile = ProfileInfo.query.first()
        scholar_url = profile.google_scholar_url if profile else None

        if request.method == 'POST':
            submitted_url = request.form.get('scholar_url', '').strip()
            if not submitted_url:
                flash('Please enter a Google Scholar profile URL', 'error')
                return render_template('admin/import_scholar.html', scholar_url=scholar_url, results=results)

            if not profile:
                profile = ProfileInfo(full_name='MD ROKIBUL HASAN')
                db.session.add(profile)

            profile.google_scholar_url = submitted_url
            attempt_cached_profile_image_refresh(profile)
            db.session.commit()
            scholar_url = submitted_url

            sync_result = maybe_sync_scholar_profile(force=True)
            if sync_result and sync_result.get('status') == 'success':
                stats = sync_result.get('stats', {})
                flash('Google Scholar data updated successfully.', 'success')
                results = {
                    'total': stats.get('publications_found', 0),
                    'added': stats.get('publications_added', 0),
                    'updated': stats.get('publications_updated', 0),
                    'skipped': stats.get('publications_unchanged', 0),
                }
            else:
                flash(f"Error syncing Google Scholar: {(sync_result or {}).get('message', 'Unknown error')}", 'error')

        return render_template('admin/import_scholar.html', scholar_url=scholar_url, results=results)

    @app.route('/admin/sync-scholar', methods=['POST'])
    @login_required
    def admin_sync_scholar():
        """Trigger a full Google Scholar sync from the dashboard."""
        result = maybe_sync_scholar_profile(force=True)
        if result and result.get('status') == 'success':
            stats = result.get('stats', {})
            flash(
                f"Scholar sync complete: {stats.get('publications_added', 0)} added, "
                f"{stats.get('publications_updated', 0)} updated, and "
                f"{stats.get('publications_unchanged', 0)} unchanged.",
                'success'
            )
        else:
            flash(f"Scholar sync failed: {(result or {}).get('message', 'Unknown error')}", 'error')
        return redirect(request.referrer or url_for('admin_dashboard'))

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

# Initialize database on app startup (works for both local and production)
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        extra_files=[],  # Don't watch extra files
        reloader_type='stat'  # Use stat reloader instead of watchdog (more stable)
    )
