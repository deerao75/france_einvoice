from app.extensions import db
from datetime import datetime
import enum

class InvoiceStatus(enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"

class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)

    # 1. Invoice Basics
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date)
    status = db.Column(db.Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)

    # 2. Company Link (Supplier)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    company = db.relationship('Company', back_populates='invoices')

    # 3. Customer Link (Buyer)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)

    # 4. Detailed Fields
    branch_name = db.Column(db.String(100))
    supplier_vat = db.Column(db.String(50))
    customer_vat = db.Column(db.String(50))

    place_of_supply = db.Column(db.String(100))
    kind_attention = db.Column(db.String(100))

    # 5. Address Snapshots
    bill_from_address = db.Column(db.Text)
    ship_from_address = db.Column(db.Text)
    bill_to_address = db.Column(db.Text)
    ship_to_address = db.Column(db.Text)

    # 6. Additional Info
    customer_notes = db.Column(db.Text)
    terms_conditions = db.Column(db.Text)
    bank_details_snapshot = db.Column(db.Text)

    # ============================
    # France e-Invoicing (PDP) NEW
    # ============================
    fr_document_type = db.Column(db.String(30))            # INVOICE / CREDIT_NOTE
    fr_transaction_category = db.Column(db.String(30))     # DOMESTIC / INTRA_EU / EXPORT
    fr_payment_means = db.Column(db.String(30))            # TRANSFER / CARD / DIRECT_DEBIT / CASH / CHEQUE
    fr_payment_terms_text = db.Column(db.String(255))      # free text

    # 7. Totals
    total_net = db.Column(db.Numeric(10, 2), default=0.0)
    total_tax = db.Column(db.Numeric(10, 2), default=0.0)
    total_gross = db.Column(db.Numeric(10, 2), default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    lines = db.relationship('InvoiceLine', backref='invoice', cascade='all, delete-orphan')


class InvoiceLine(db.Model):
    __tablename__ = 'invoice_lines'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)

    description = db.Column(db.String(255), nullable=False)
    hsn_sac_code = db.Column(db.String(20))

    quantity = db.Column(db.Numeric(10, 2), default=1.0)
    unit_price = db.Column(db.Numeric(10, 2), default=0.0)

    vat_rate = db.Column(db.Numeric(5, 2), default=0.0)
    vat_amount = db.Column(db.Numeric(10, 2), default=0.0)

    line_total = db.Column(db.Numeric(10, 2), default=0.0)
