from app.extensions import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)

    # Foreign Key (Relationship is managed by Company model's backref)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # Fields Requested
    product_ref_id = db.Column(db.String(50)) # Product/Service ID
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50)) # SKU / Code
    unit = db.Column(db.String(20)) # NOS, Kgs, Service, etc.
    description = db.Column(db.Text)
    unit_price = db.Column(db.Numeric(10, 2), default=0.0)
    vat_rate = db.Column(db.Numeric(5, 2), default=20.0) # Optional tax default

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Note: Do NOT add 'company = db.relationship(...)' here.
    # It is already defined in Company as backref='company'.
