from app.extensions import db
from datetime import datetime

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    customer_ref_id = db.Column(db.String(20), unique=True, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    vat_number = db.Column(db.String(50))
    siret = db.Column(db.String(50))
    siren = db.Column(db.String(50))  # ← you are already using this

    vat_treatment = db.Column(db.String(50), default='registered')

    # ✅ FR e-Invoicing – Buyer fields
    buyer_type = db.Column(db.String(50))                 # Domestic B2B, Export, etc.
    delivery_channel = db.Column(db.String(20))           # PDP / PPF
    buyer_pdp_id = db.Column(db.String(100))
    buyer_invoice_email = db.Column(db.String(120))

    po_required = db.Column(db.String(10))                # Yes / No
    buyer_reference = db.Column(db.String(100))
    default_po_number = db.Column(db.String(50))

    currency = db.Column(db.String(3), default='EUR')
    payment_terms = db.Column(db.String(50))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    addresses = db.relationship('CustomerAddress', backref='customer', cascade="all, delete-orphan")
    invoices = db.relationship('Invoice', backref='customer')



class CustomerAddress(db.Model):
    __tablename__ = 'customer_addresses'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)

    type = db.Column(db.String(20), default='BILLING')  # BILLING or SHIPPING
    label = db.Column(db.String(50))

    address_line1 = db.Column(db.String(200), nullable=False)
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
    country = db.Column(db.String(2), default='FR')
