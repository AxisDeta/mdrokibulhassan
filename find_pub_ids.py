from app import create_app
from models import Publication

app = create_app()

keywords = ["Blockchain", "Carbon", "Sustainable", "Forecasting", "Inventory", "Supplier"]

with app.app_context():
    for kw in keywords:
        print(f"\nSearching for '{kw}':")
        pubs = Publication.query.filter(Publication.title.ilike(f"%{kw}%")).all()
        for p in pubs:
            print(f"ID: {p.id} | Title: {p.title}")
