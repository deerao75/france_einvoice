from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        with db.engine.connect() as conn:
            # Add the missing column for Credit Note linking
            conn.execute(text("ALTER TABLE invoices ADD COLUMN original_invoice_id INTEGER"))
            conn.commit()
            print("SUCCESS: Added 'original_invoice_id' column to 'invoices' table.")
    except Exception as e:
        print(f"Error (column might already exist): {e}")
