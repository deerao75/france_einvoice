from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required
from datetime import date
import io
import re

from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus
from app.models.customer import Customer
from app.models.product import Product
from app.models.company import Company
from app.extensions import db

bp = Blueprint('invoices', __name__, url_prefix='/invoices')


# ---------- Helpers ----------

def _unique_invoice_number(requested: str) -> str:
    base = (requested or "").strip()
    if not base:
        count = Invoice.query.count()
        return f"INV-{date.today().year}-{1001 + count}"

    if not Invoice.query.filter_by(invoice_number=base).first():
        return base

    m = re.match(r"^(?P<prefix>.+?)-(?P<year>\d{4})-(?P<num>\d+)$", base)
    if m:
        prefix = m.group("prefix")
        year = m.group("year")
        num = int(m.group("num"))
        while True:
            num += 1
            candidate = f"{prefix}-{year}-{num}"
            if not Invoice.query.filter_by(invoice_number=candidate).first():
                return candidate

    suffix = 1
    while True:
        candidate = f"{base}-COPY-{suffix}"
        if not Invoice.query.filter_by(invoice_number=candidate).first():
            return candidate
        suffix += 1


def _unique_invoice_number_excluding(requested: str, exclude_id: int) -> str:
    base = (requested or "").strip()
    if not base:
        count = Invoice.query.count()
        return f"INV-{date.today().year}-{1001 + count}"

    exists = Invoice.query.filter(Invoice.invoice_number == base, Invoice.id != exclude_id).first()
    if not exists:
        return base

    m = re.match(r"^(?P<prefix>.+?)-(?P<year>\d{4})-(?P<num>\d+)$", base)
    if m:
        prefix = m.group("prefix")
        year = m.group("year")
        num = int(m.group("num"))
        while True:
            num += 1
            candidate = f"{prefix}-{year}-{num}"
            if not Invoice.query.filter(Invoice.invoice_number == candidate, Invoice.id != exclude_id).first():
                return candidate

    suffix = 1
    while True:
        candidate = f"{base}-COPY-{suffix}"
        if not Invoice.query.filter(Invoice.invoice_number == candidate, Invoice.id != exclude_id).first():
            return candidate
        suffix += 1


# ---------- Dashboard ----------

@bp.route('/')
@login_required
def index():
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    return render_template('invoices/index.html', invoices=invoices)


# ---------- Create ----------

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    company = Company.query.first()
    customers = Customer.query.all()
    products = Product.query.all()

    # Supplier address defaults
    supp_bill_addr = ""
    supp_ship_addr = ""
    if company:
        bill_obj = next((a for a in getattr(company, 'addresses', []) if a.type == 'BILLING'), None)
        ship_obj = next((a for a in getattr(company, 'addresses', []) if a.type == 'SHIPPING'), None)

        if bill_obj:
            supp_bill_addr = f"{company.name}\n{bill_obj.address_line1}\n{bill_obj.city} {bill_obj.zip_code}\n{bill_obj.country}"
        else:
            supp_bill_addr = f"{company.name}"

        if ship_obj:
            supp_ship_addr = f"{company.name}\n{ship_obj.address_line1}\n{ship_obj.city} {ship_obj.zip_code}\n{ship_obj.country}"
        else:
            supp_ship_addr = supp_bill_addr

    if request.method == 'POST':
        save_type = request.form.get('save_type', 'draft')
        status = InvoiceStatus.DRAFT if save_type == 'draft' else InvoiceStatus.SENT

        cust_id_raw = request.form.get('customer_id')
        if not cust_id_raw:
            flash('Please select a customer before saving the invoice.', 'warning')
            return redirect(url_for('invoices.create'))
        try:
            customer_id = int(cust_id_raw)
        except ValueError:
            flash('Invalid customer selected.', 'danger')
            return redirect(url_for('invoices.create'))

        requested_number = request.form.get('invoice_number')
        invoice_number = _unique_invoice_number(requested_number)

        invoice_date = date.fromisoformat(request.form['invoice_date']) if request.form.get('invoice_date') else date.today()
        due_date = date.fromisoformat(request.form['due_date']) if request.form.get('due_date') else None

        total_net = float(request.form.get('computed_subtotal', 0) or 0)
        total_tax = float(request.form.get('computed_tax', 0) or 0)
        total_gross = float(request.form.get('computed_total', 0) or 0)

        new_inv = Invoice(
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            status=status,

            company_id=company.id if company else None,
            customer_id=customer_id,

            branch_name=request.form.get('branch_name', 'Head Office'),
            supplier_vat=company.vat_number if company else '',
            customer_vat=request.form.get('customer_vat', ''),
            place_of_supply=request.form.get('place_of_supply', ''),
            kind_attention=request.form.get('kind_attention', ''),

            bill_from_address=request.form.get('bill_from', ''),
            ship_from_address=request.form.get('ship_from', ''),
            bill_to_address=request.form.get('bill_to', ''),
            ship_to_address=request.form.get('ship_to', ''),

            customer_notes=request.form.get('notes', ''),
            terms_conditions=request.form.get('terms', ''),
            bank_details_snapshot=request.form.get('bank_details', ''),

            # -------- France e-invoicing (NEW) --------
            fr_document_type=request.form.get('fr_document_type', 'INVOICE'),
            fr_transaction_category=request.form.get('fr_transaction_category', 'DOMESTIC'),
            fr_payment_means=request.form.get('fr_payment_means', ''),
            fr_payment_terms_text=request.form.get('fr_payment_terms_text', ''),

            total_net=total_net,
            total_tax=total_tax,
            total_gross=total_gross
        )

        db.session.add(new_inv)
        db.session.flush()

        for i in range(200):
            desc = request.form.get(f"lines[{i}][desc]")
            prod_id_raw = request.form.get(f"lines[{i}][product_id]")
            has_line = (desc and desc.strip()) or prod_id_raw
            if not has_line:
                continue

            qty = float(request.form.get(f"lines[{i}][qty]", 1) or 1)
            rate = float(request.form.get(f"lines[{i}][rate]", 0) or 0)
            tax_pct = float(request.form.get(f"lines[{i}][tax]", 0) or 0)

            line_net = qty * rate
            vat_amount = line_net * (tax_pct / 100)
            line_total = line_net + vat_amount

            item = InvoiceLine(
                invoice_id=new_inv.id,
                description=desc or '',
                hsn_sac_code=request.form.get(f"lines[{i}][hsn]", ''),
                quantity=qty,
                unit_price=rate,
                vat_rate=tax_pct,
                vat_amount=vat_amount,
                line_total=line_total
            )
            db.session.add(item)

        db.session.commit()

        flash('Invoice saved as Draft.' if save_type == 'draft' else 'Invoice finalized successfully!', 'success')
        return redirect(url_for('invoices.index'))

    count = Invoice.query.count()
    next_inv = f"INV-{date.today().year}-{1001 + count}"

    return render_template(
        'invoices/create.html',
        customers=customers,
        products=products,
        company=company,
        supplier_bill_default=supp_bill_addr,
        supplier_ship_default=supp_ship_addr,
        today=date.today().isoformat(),
        next_inv_number=next_inv,
        invoice=None,
        is_edit=False
    )


# ---------- Edit ----------

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    invoice = Invoice.query.get_or_404(id)
    company = Company.query.first()
    customers = Customer.query.all()
    products = Product.query.all()

    supp_bill_addr = ""
    supp_ship_addr = ""
    if company:
        bill_obj = next((a for a in getattr(company, 'addresses', []) if a.type == 'BILLING'), None)
        ship_obj = next((a for a in getattr(company, 'addresses', []) if a.type == 'SHIPPING'), None)

        if bill_obj:
            supp_bill_addr = f"{company.name}\n{bill_obj.address_line1}\n{bill_obj.city} {bill_obj.zip_code}\n{bill_obj.country}"
        else:
            supp_bill_addr = f"{company.name}"

        if ship_obj:
            supp_ship_addr = f"{company.name}\n{ship_obj.address_line1}\n{ship_obj.city} {ship_obj.zip_code}\n{ship_obj.country}"
        else:
            supp_ship_addr = supp_bill_addr

    if request.method == 'POST':
        save_type = request.form.get('save_type', 'draft')
        invoice.status = InvoiceStatus.DRAFT if save_type == 'draft' else InvoiceStatus.SENT

        requested_number = request.form.get('invoice_number')
        invoice.invoice_number = _unique_invoice_number_excluding(requested_number, invoice.id)

        invoice.invoice_date = date.fromisoformat(request.form['invoice_date']) if request.form.get('invoice_date') else date.today()
        invoice.due_date = date.fromisoformat(request.form['due_date']) if request.form.get('due_date') else None
        invoice.customer_id = int(request.form['customer_id']) if request.form.get('customer_id') else None

        invoice.branch_name = request.form.get('branch_name', 'Head Office')
        invoice.customer_vat = request.form.get('customer_vat', '')
        invoice.place_of_supply = request.form.get('place_of_supply', '')
        invoice.kind_attention = request.form.get('kind_attention', '')

        invoice.bill_from_address = request.form.get('bill_from', '')
        invoice.ship_from_address = request.form.get('ship_from', '')
        invoice.bill_to_address = request.form.get('bill_to', '')
        invoice.ship_to_address = request.form.get('ship_to', '')

        invoice.customer_notes = request.form.get('notes', '')
        invoice.terms_conditions = request.form.get('terms', '')
        invoice.bank_details_snapshot = request.form.get('bank_details', '')

        # -------- France e-invoicing (NEW) --------
        invoice.fr_document_type = request.form.get('fr_document_type', 'INVOICE')
        invoice.fr_transaction_category = request.form.get('fr_transaction_category', 'DOMESTIC')
        invoice.fr_payment_means = request.form.get('fr_payment_means', '')
        invoice.fr_payment_terms_text = request.form.get('fr_payment_terms_text', '')

        invoice.total_net = float(request.form.get('computed_subtotal', 0) or 0)
        invoice.total_tax = float(request.form.get('computed_tax', 0) or 0)
        invoice.total_gross = float(request.form.get('computed_total', 0) or 0)

        InvoiceLine.query.filter_by(invoice_id=invoice.id).delete()
        for i in range(200):
            desc = request.form.get(f"lines[{i}][desc]")
            prod_id_raw = request.form.get(f"lines[{i}][product_id]")
            has_line = (desc and desc.strip()) or prod_id_raw
            if not has_line:
                continue

            qty = float(request.form.get(f"lines[{i}][qty]", 1) or 1)
            rate = float(request.form.get(f"lines[{i}][rate]", 0) or 0)
            tax_pct = float(request.form.get(f"lines[{i}][tax]", 0) or 0)

            line_net = qty * rate
            vat_amount = line_net * (tax_pct / 100)
            line_total = line_net + vat_amount

            item = InvoiceLine(
                invoice_id=invoice.id,
                description=desc or '',
                hsn_sac_code=request.form.get(f"lines[{i}][hsn]", ''),
                quantity=qty,
                unit_price=rate,
                vat_rate=tax_pct,
                vat_amount=vat_amount,
                line_total=line_total
            )
            db.session.add(item)

        db.session.commit()

        flash('Draft updated successfully.' if save_type == 'draft' else 'Invoice finalized successfully!', 'success')
        return redirect(url_for('invoices.index'))

    return render_template(
        'invoices/create.html',
        customers=customers,
        products=products,
        company=company,
        supplier_bill_default=invoice.bill_from_address or supp_bill_addr,
        supplier_ship_default=invoice.ship_from_address or supp_ship_addr,
        today=date.today().isoformat(),
        next_inv_number=invoice.invoice_number,
        invoice=invoice,
        is_edit=True
    )


# ---------- View / Print / PDF ----------

@bp.route('/view/<int:id>')
@login_required
def view(id):
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    invoice = Invoice.query.get_or_404(id)
    company = Company.query.first()

    customer = None
    if getattr(invoice, "customer_id", None):
        customer = Customer.query.get(invoice.customer_id)

    return render_template(
        'invoices/view.html',
        invoices=invoices,
        invoice=invoice,
        company=company,
        customer=customer
    )


@bp.route('/print/<int:id>')
@login_required
def print_invoice(id):
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
    invoice = Invoice.query.get_or_404(id)
    company = Company.query.first()
    return render_template('invoices/view.html', invoices=invoices, invoice=invoice, company=company, auto_print=True)


@bp.route('/pdf/<int:id>')
@login_required
def pdf(id):
    invoice = Invoice.query.get_or_404(id)
    company = Company.query.first()
    html = render_template('invoices/partials/invoice_render.html', invoice=invoice, company=company, pdf_mode=True)
    pdf_bytes = None
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html).write_pdf()
    except Exception:
        try:
            import pdfkit
            pdf_bytes = pdfkit.from_string(html, False)
        except Exception:
            pdf_bytes = None

    if pdf_bytes:
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{invoice.invoice_number}.pdf"
        )

    return render_template('invoices/partials/invoice_render.html', invoice=invoice, company=company, pdf_mode=True)


# ---------- AJAX ----------

@bp.route('/get_customer_addresses/<int:id>')
@login_required
def get_customer_addresses(id):
    cust = Customer.query.get_or_404(id)

    billing_addresses = []
    shipping_addresses = []

    for addr in getattr(cust, 'addresses', []):
        addr_data = {
            'id': addr.id,
            'label': addr.label or ('Billing' if addr.type == 'BILLING' else 'Shipping'),
            'line1': addr.address_line1,
            'line2': addr.address_line2 or '',
            'city': addr.city or '',
            'zip': addr.zip_code or '',
            'country': addr.country or ''
        }
        if addr.type == 'BILLING':
            billing_addresses.append(addr_data)
        else:
            shipping_addresses.append(addr_data)

    default_bill = ""
    default_ship = ""
    if billing_addresses:
        a = billing_addresses[0]
        default_bill = f"{cust.name}\n{a['line1']}\n{a['city']} {a['zip']}\n{a['country']}"
    if shipping_addresses:
        a = shipping_addresses[0]
        default_ship = f"{cust.name}\n{a['line1']}\n{a['city']} {a['zip']}\n{a['country']}"
    else:
        default_ship = default_bill

    return jsonify({
        'billing_addresses': billing_addresses,
        'shipping_addresses': shipping_addresses,
        'default_bill_to': default_bill,
        'default_ship_to': default_ship,
        'vat_number': cust.vat_number
    })

@bp.route('/debit-note/create', methods=['GET', 'POST'])
@login_required
def create_debit_note():
    flash('Debit Note feature coming soon!', 'info')
    return redirect(url_for('invoices.index'))


@bp.route('/credit-note/create', methods=['GET', 'POST'])
@login_required
def create_credit_note():
    flash('Credit Note feature coming soon!', 'info')
    return redirect(url_for('invoices.index'))

@bp.route('/duplicate/<int:id>')
@login_required
def duplicate(id):
    """Clone an invoice and open in create form with prefilled data"""
    inv = Invoice.query.get_or_404(id)

    company = Company.query.first()
    customers = Customer.query.all()
    products = Product.query.all()

    prefill = {
        'invoice_number': _unique_invoice_number(f"{inv.invoice_number}-COPY"),
        'invoice_date': inv.invoice_date.isoformat() if inv.invoice_date else date.today().isoformat(),
        'due_date': inv.due_date.isoformat() if inv.due_date else '',
        'branch_name': inv.branch_name or 'Head Office',
        'customer_id': inv.customer_id,
        'customer_vat': inv.customer_vat or '',
        'place_of_supply': inv.place_of_supply or 'FR',
        'kind_attention': inv.kind_attention or '',
        'bill_from': inv.bill_from_address or '',
        'ship_from': inv.ship_from_address or '',
        'bill_to': inv.bill_to_address or '',
        'ship_to': inv.ship_to_address or '',
        'notes': inv.customer_notes or '',
        'terms': inv.terms_conditions or '',
        'bank_details': inv.bank_details_snapshot or '',
        # France e-invoice fields
        'fr_document_type': getattr(inv, 'fr_document_type', 'INVOICE') or 'INVOICE',
        'fr_transaction_category': getattr(inv, 'fr_transaction_category', 'DOMESTIC') or 'DOMESTIC',
        'fr_payment_means': getattr(inv, 'fr_payment_means', '') or '',
        'fr_payment_terms_text': getattr(inv, 'fr_payment_terms_text', '') or '',
    }

    prefill_lines = []
    for idx, line in enumerate(getattr(inv, 'lines', []) or []):
        prefill_lines.append({
            'index': idx,
            'desc': line.description or '',
            'hsn': line.hsn_sac_code or '',
            'qty': float(line.quantity or 1),
            'rate': float(line.unit_price or 0),
            'tax': float(line.vat_rate or 0),
        })

    return render_template(
        'invoices/create.html',
        company=company,
        customers=customers,
        products=products,
        today=date.today().isoformat(),
        next_inv_number=prefill['invoice_number'],
        invoice=None,
        is_edit=False,
        prefill=prefill,
        prefill_lines=prefill_lines,
    )

@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    """Delete an invoice (recommended: only allow delete for DRAFT)"""
    invoice = Invoice.query.get_or_404(id)

    # Safety: only drafts can be deleted
    if invoice.status != InvoiceStatus.DRAFT:
        flash('Only draft invoices can be deleted.', 'warning')
        return redirect(url_for('invoices.index'))

    # Delete lines + invoice
    InvoiceLine.query.filter_by(invoice_id=invoice.id).delete()
    db.session.delete(invoice)
    db.session.commit()

    flash('Draft invoice deleted successfully.', 'success')
    return redirect(url_for('invoices.index'))



