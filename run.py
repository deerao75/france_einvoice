from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Auto-create tables for MVP simplicity
        # (In prod, use flask db upgrade)
        db.create_all()
    app.run(debug=True)
