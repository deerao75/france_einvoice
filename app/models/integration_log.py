from app.extensions import db
from datetime import datetime

class IntegrationLog(db.Model):
    __tablename__ = 'integration_logs'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    direction = db.Column(db.String(20)) # OUTBOUND, INBOUND
    payload_type = db.Column(db.String(20))
    payload_snippet = db.Column(db.Text)
    status_code = db.Column(db.String(50))
    error_code = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
