from app.extensions import db
from datetime import datetime

class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)

    # Identity
    name = db.Column(db.String(100), nullable=False)
    legal_name = db.Column(db.String(100))
    merchant_id = db.Column(db.String(20), unique=True)

    # NEW: Mandatory Legal Details for Footer/Header
    legal_form = db.Column(db.String(50))      # e.g., SAS, SARL, EURL
    share_capital = db.Column(db.String(50))   # e.g., 1000.00
    rcs_city = db.Column(db.String(100))       # e.g., Paris

    vat_number = db.Column(db.String(50))

    # France identifiers
    siren = db.Column(db.String(20))
    siret = db.Column(db.String(50))

    # Invoice contact (for e-invoice/PDP payload)
    invoice_email = db.Column(db.String(120))
    invoice_phone = db.Column(db.String(30))

    logo_filename = db.Column(db.String(100))

    # Settings fields
    numbering_mode = db.Column(db.String(20), default='AUTO')
    fiscal_year = db.Column(db.Integer)
    invoice_prefix = db.Column(db.String(10), default='INV')
    starting_invoice_number = db.Column(db.Integer, default=1001)
    payment_terms = db.Column(db.Integer, default=30)
    currency = db.Column(db.String(3), default='EUR')

    # E-invoicing settings
    einvoice_channel = db.Column(db.String(10), default='PDP')
    einvoice_format = db.Column(db.String(20), default='FACTURX')
    supplier_pdp_name = db.Column(db.String(200))
    supplier_pdp_id = db.Column(db.String(100))

    # Terms and notes
    default_terms = db.Column(db.Text)
    default_notes = db.Column(db.Text)

    # Additional fields
    industry = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    addresses = db.relationship('CompanyAddress', backref='company', cascade="all, delete-orphan")
    bank_accounts = db.relationship('BankAccount', backref='company', cascade="all, delete-orphan")
    invoices = db.relationship('Invoice', back_populates='company')
    users = db.relationship('UserCompany', back_populates='company')


class CompanyAddress(db.Model):
    __tablename__ = 'company_addresses'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    type = db.Column(db.String(20), default='BILLING')
    label = db.Column(db.String(50))

    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
    country = db.Column(db.String(2), default='FR')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CompanyAddress {self.id} {self.type}>'


class BankAccount(db.Model):
    __tablename__ = 'bank_accounts'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    account_holder = db.Column(db.String(200))
    bank_name = db.Column(db.String(200))
    iban = db.Column(db.String(50))
    bic = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BankAccount {self.id} {self.bank_name}>'
