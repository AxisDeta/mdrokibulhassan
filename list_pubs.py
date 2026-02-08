from app import create_app
from models import Publication

app = create_app()

with app.app_context():
    pubs = Publication.query.order_by(Publication.id).all()
    print(f"{'ID':<5} | {'Year':<6} | {'Title'}")
    print("-" * 100)
    for p in pubs:
        print(f"{p.id:<5} | {p.year:<6} | {p.title}")
