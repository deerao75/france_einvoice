from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.customer import Customer, CustomerAddress
import os
import random
from werkzeug.utils import secure_filename
from flask import current_app
from app.models.company import Company, CompanyAddress, BankAccount  # ADD BankAccount here
from app.models.product import Product

bp = Blueprint('management', __name__)

# --- CUSTOMER LIST ---
@bp.route('/customers')
@login_required
def customers_list():
    customers = Customer.query.all()
    return render_template('management/customers.html', customers=customers)

@bp.route('/customers/create', methods=['GET', 'POST'])
@login_required
def create_customer():
    # Auto-generate ID (Simple Logic: Count + 100001)
    count = Customer.query.count()
    next_id = f"{100001 + count}"

    if request.method == 'POST':
        company = Company.query.first()
        if not company:
            flash('No company found.', 'error')
            return redirect(url_for('public.index'))

        # 1. Create Customer
        new_cust = Customer(
            company_id=company.id,
            customer_ref_id=request.form.get('customer_ref_id', next_id),
            name=request.form['name'],
            vat_treatment=request.form.get('vat_treatment'),
            vat_number=request.form.get('vat_number'),
            siret=request.form.get('siret'),
            siren=request.form.get('siren'),
            buyer_type=request.form.get('buyer_type'),
            delivery_channel=request.form.get('delivery_channel'),
            buyer_pdp_id=request.form.get('buyer_pdp_id'),
            buyer_invoice_email=request.form.get('buyer_invoice_email'),
            po_required=request.form.get('po_required'),
            buyer_reference=request.form.get('buyer_reference'),
            default_po_number=request.form.get('default_po_number'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            currency=request.form.get('currency'),
            payment_terms=request.form.get('payment_terms')
        )
        db.session.add(new_cust)
        db.session.flush()

        # 2. Process Fixed Billing Address (Index 0)
        bill_line1 = request.form.get("addresses[0][line1]")
        if bill_line1:
            bill_addr = CustomerAddress(
                customer_id=new_cust.id,
                type="BILLING",
                label="Main Billing",
                address_line1=bill_line1,
                address_line2=request.form.get("addresses[0][line2]"),
                city=request.form.get("addresses[0][city]"),
                country=request.form.get("addresses[0][country]")
            )
            db.session.add(bill_addr)

        # 3. Process Shipping Address (Index 1 OR Copy Billing)
        if request.form.get('same_as_billing'):
            # Copy Billing Data
            ship_addr = CustomerAddress(
                customer_id=new_cust.id,
                type="SHIPPING",
                label="Main Shipping (Same as Billing)",
                address_line1=bill_line1,  # Use the billing data we just grabbed
                address_line2=request.form.get("addresses[0][line2]"),
                city=request.form.get("addresses[0][city]"),
                country=request.form.get("addresses[0][country]")
            )
            db.session.add(ship_addr)
        else:
            # Use specific inputs
            ship_line1 = request.form.get("addresses[1][line1]")
            if ship_line1:
                ship_addr = CustomerAddress(
                    customer_id=new_cust.id,
                    type="SHIPPING",
                    label="Main Shipping",
                    address_line1=ship_line1,
                    address_line2=request.form.get("addresses[1][line2]"),
                    city=request.form.get("addresses[1][city]"),
                    country=request.form.get("addresses[1][country]")
                )
                db.session.add(ship_addr)

        # 4. Process Extra Dynamic Addresses (Index 2 to 50)
        for i in range(2, 50):
            type_key = f"addresses[{i}][type]"
            if type_key in request.form:
                line1 = request.form.get(f"addresses[{i}][line1]")
                if line1:
                    addr = CustomerAddress(
                        customer_id=new_cust.id,
                        type=request.form.get(type_key),
                        label=request.form.get(f"addresses[{i}][label]"),
                        address_line1=line1,
                        city=request.form.get(f"addresses[{i}][city]")
                    )
                    db.session.add(addr)

        db.session.commit()
        flash('Customer created successfully', 'success')
        return redirect(url_for('management.customers_list'))

    return render_template('management/create_customer.html', next_id=next_id)

# --- LIST ---
@bp.route('/products')
@login_required
def products_list():
    products = Product.query.all()
    return render_template('management/products.html', products=products)

@bp.route('/products/new', methods=['GET', 'POST'])
@login_required
def create_product():
    if request.method == 'POST':
        company = Company.query.first()

        # Helper to safely convert numbers
        def safe_float(val):
            return float(val) if val and val.strip() else 0.0

        new_prod = Product(
            company_id=company.id if company else 1,
            product_ref_id=request.form.get('product_ref_id'),
            name=request.form.get('name'),
            code=request.form.get('code'),
            unit=request.form.get('unit'),
            description=request.form.get('description'),
            # Convert empty strings to 0.0
            unit_price=safe_float(request.form.get('unit_price')),
            vat_rate=safe_float(request.form.get('vat_rate'))
        )
        db.session.add(new_prod)
        db.session.commit()
        flash('Product/Service created successfully', 'success')
        return redirect(url_for('management.products_list'))

    return render_template('management/create_product.html')

@bp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        # Helper to safely convert numbers
        def safe_float(val):
            return float(val) if val and val.strip() else 0.0

        product.product_ref_id = request.form.get('product_ref_id')
        product.name = request.form.get('name')
        product.code = request.form.get('code')
        product.unit = request.form.get('unit')
        product.description = request.form.get('description')

        # Handle number updates safely
        product.unit_price = safe_float(request.form.get('unit_price'))
        product.vat_rate = safe_float(request.form.get('vat_rate'))

        db.session.commit()
        flash('Product updated successfully', 'success')
        return redirect(url_for('management.products_list'))

    return render_template('management/edit_product.html', product=product)

@bp.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def customer_edit(id):
    customer = Customer.query.get_or_404(id)

    if request.method == 'POST':
        # 1. Update Core Info
        customer.name = request.form['name']
        customer.vat_treatment = request.form.get('vat_treatment')
        customer.vat_number = request.form.get('vat_number')
        customer.siret = request.form.get('siret')
        customer.siren = request.form.get('siren')
        customer.buyer_type = request.form.get('buyer_type')
        customer.delivery_channel = request.form.get('delivery_channel')
        customer.buyer_pdp_id = request.form.get('buyer_pdp_id')
        customer.buyer_invoice_email = request.form.get('buyer_invoice_email')
        customer.po_required = request.form.get('po_required')
        customer.buyer_reference = request.form.get('buyer_reference')
        customer.default_po_number = request.form.get('default_po_number')
        customer.email = request.form.get('email')
        customer.phone = request.form.get('phone')
        customer.payment_terms = request.form.get('payment_terms')

        # 2. Update Addresses Loop
        for i in range(50):
            addr_id = request.form.get(f"addresses[{i}][id]")

            if addr_id:
                line1 = request.form.get(f"addresses[{i}][line1]")

                if addr_id == 'new' and line1:
                    # Create NEW
                    new_addr = CustomerAddress(
                        customer_id=customer.id,
                        type=request.form.get(f"addresses[{i}][type]"),
                        label=request.form.get(f"addresses[{i}][label]"),
                        address_line1=line1,
                        address_line2=request.form.get(f"addresses[{i}][line2]"),
                        zip_code=request.form.get(f"addresses[{i}][zip]"),
                        city=request.form.get(f"addresses[{i}][city]"),
                        country=request.form.get(f"addresses[{i}][country]")
                    )
                    db.session.add(new_addr)

                elif addr_id != 'new':
                    existing_addr = next((a for a in customer.addresses if str(a.id) == addr_id), None)
                    if existing_addr:
                        existing_addr.type = request.form.get(f"addresses[{i}][type]")
                        existing_addr.label = request.form.get(f"addresses[{i}][label]")
                        existing_addr.address_line1 = request.form.get(f"addresses[{i}][line1]")
                        existing_addr.address_line2 = request.form.get(f"addresses[{i}][line2]")
                        existing_addr.zip_code = request.form.get(f"addresses[{i}][zip]")
                        existing_addr.city = request.form.get(f"addresses[{i}][city]")
                        existing_addr.country = request.form.get(f"addresses[{i}][country]")

        db.session.commit()
        flash('Customer updated successfully', 'success')
        return redirect(url_for('management.customers_list'))

    return render_template('management/edit_customer.html', customer=customer)

@bp.route('/customers/<int:id>/toggle-status', methods=['POST'])
@login_required
def customer_toggle_status(id):
    customer = Customer.query.get_or_404(id)
    customer.is_suspended = not bool(customer.is_suspended)
    db.session.commit()
    flash('Customer status updated successfully', 'success')
    return redirect(url_for('management.customers_list'))


# --- ORGANIZATION ---

def _maybe_set_attr(obj, attr, value):
    """Set attribute only if the Company model has that column/attr."""
    if hasattr(obj, attr):
        setattr(obj, attr, value)

def _safe_int(val, default=None):
    try:
        if val is None:
            return default
        v = str(val).strip()
        if v == "":
            return default
        return int(v)
    except Exception:
        return default

@bp.route('/organization', methods=['GET', 'POST'])
@login_required
def organization_profile():
    company = Company.query.first()
    if not company:
        company = Company(name="New Org", merchant_id=str(random.randint(1000000, 9999999)))
        db.session.add(company)
        db.session.commit()

    if request.method == 'POST':
        # ---------- PROFILE TAB (Identity/Tax/Contact) ----------
        company.name = (request.form.get('name') or "").strip()
        company.legal_name = (request.form.get('legal_name') or "").strip()
        company.siret = (request.form.get('siret') or "").strip()

        # NEW: Save SIREN + invoice contact details (these were missing earlier)
        _maybe_set_attr(company, "siren", (request.form.get("siren") or "").strip())
        _maybe_set_attr(company, "invoice_email", (request.form.get("invoice_email") or "").strip())
        _maybe_set_attr(company, "invoice_phone", (request.form.get("invoice_phone") or "").strip())
        _maybe_set_attr(company, "industry", (request.form.get("industry") or "").strip())

        # VAT Number is Read-Only in UI; update only if blank in DB
        if (not company.vat_number) and request.form.get('vat_number'):
            company.vat_number = request.form.get('vat_number')

        # ---------- SETTINGS TAB ----------
        # Added numbering_mode which was missing
        _maybe_set_attr(company, "numbering_mode", (request.form.get("numbering_mode") or "AUTO").strip())
        _maybe_set_attr(company, "fiscal_year", _safe_int(request.form.get("fiscal_year")))
        _maybe_set_attr(company, "invoice_prefix", (request.form.get("invoice_prefix") or "").strip())
        _maybe_set_attr(company, "starting_invoice_number", _safe_int(request.form.get("starting_invoice_number")))
        _maybe_set_attr(company, "payment_terms", _safe_int(request.form.get("payment_terms")))
        _maybe_set_attr(company, "currency", (request.form.get("currency") or "").strip())

        _maybe_set_attr(company, "einvoice_channel", (request.form.get("einvoice_channel") or "PDP").strip())
        _maybe_set_attr(company, "einvoice_format", (request.form.get("einvoice_format") or "FACTURX").strip())
        _maybe_set_attr(company, "supplier_pdp_name", (request.form.get("supplier_pdp_name") or "").strip())
        _maybe_set_attr(company, "supplier_pdp_id", (request.form.get("supplier_pdp_id") or "").strip())

        _maybe_set_attr(company, "default_terms", (request.form.get("default_terms") or "").strip())
        _maybe_set_attr(company, "default_notes", (request.form.get("default_notes") or "").strip())

        # ---------- LOGO UPLOAD ----------
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename:
                filename = secure_filename(f"logo_{company.id}_{file.filename}")
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                company.logo_filename = filename

        # ---------- ADDRESSES (create/update/delete) ----------
        posted_ids = set()

        for i in range(50):
            addr_id = request.form.get(f"addresses[{i}][id]")
            if not addr_id:
                continue

            addr_type = (request.form.get(f"addresses[{i}][type]") or "BILLING").strip()
            label = (request.form.get(f"addresses[{i}][label]") or "").strip()
            line1 = (request.form.get(f"addresses[{i}][line1]") or "").strip()
            line2 = (request.form.get(f"addresses[{i}][line2]") or "").strip()
            city = (request.form.get(f"addresses[{i}][city]") or "").strip()
            zip_code = (request.form.get(f"addresses[{i}][zip]") or "").strip()
            country = (request.form.get(f"addresses[{i}][country]") or "FR").strip()

            # Skip empty brand-new rows
            if addr_id == "new" and not line1:
                continue

            if addr_id == 'new':
                new_addr = CompanyAddress(
                    company_id=company.id,
                    type=addr_type,
                    label=label,
                    address_line1=line1,
                    address_line2=line2,
                    city=city,
                    zip_code=zip_code,
                    country=country
                )
                db.session.add(new_addr)
                db.session.flush()  # get id
                posted_ids.add(new_addr.id)
            else:
                curr = CompanyAddress.query.filter_by(id=int(addr_id), company_id=company.id).first()
                if curr:
                    curr.type = addr_type
                    curr.label = label
                    curr.address_line1 = line1
                    curr.address_line2 = line2
                    curr.city = city
                    curr.zip_code = zip_code
                    curr.country = country
                    posted_ids.add(curr.id)

        # Delete addresses that were removed on UI (if any)
        existing_ids = {a.id for a in company.addresses}
        to_delete = existing_ids - posted_ids
        if to_delete:
            CompanyAddress.query.filter(
                CompanyAddress.company_id == company.id,
                CompanyAddress.id.in_(list(to_delete))
            ).delete(synchronize_session=False)

        # ---------- BANK ACCOUNTS (NEW - was missing) ----------
        posted_bank_ids = set()
        bank_index = 0

        while True:
            account_holder = request.form.get(f"accounts[{bank_index}][account_holder]")
            if account_holder is None:
                break

            bank_name = request.form.get(f"accounts[{bank_index}][bank_name]") or ""
            iban = request.form.get(f"accounts[{bank_index}][iban]") or ""
            bic = request.form.get(f"accounts[{bank_index}][bic]") or ""

            # Try to find if this is an existing bank account
            # First check if we have a hidden ID field
            bank_id = request.form.get(f"accounts[{bank_index}][id]")

            if bank_id and bank_id != 'new' and bank_id.isdigit():
                # Update existing bank account by ID
                bank_acc = BankAccount.query.filter_by(id=int(bank_id), company_id=company.id).first()
                if bank_acc:
                    bank_acc.account_holder = account_holder.strip()
                    bank_acc.bank_name = bank_name.strip()
                    bank_acc.iban = iban.strip()
                    bank_acc.bic = bic.strip()
                    posted_bank_ids.add(bank_acc.id)
                else:
                    # ID was provided but not found - create new
                    new_bank = BankAccount(
                        company_id=company.id,
                        account_holder=account_holder.strip(),
                        bank_name=bank_name.strip(),
                        iban=iban.strip(),
                        bic=bic.strip()
                    )
                    db.session.add(new_bank)
                    posted_bank_ids.add(new_bank.id)
            else:
                # Create new bank account
                new_bank = BankAccount(
                    company_id=company.id,
                    account_holder=account_holder.strip(),
                    bank_name=bank_name.strip(),
                    iban=iban.strip(),
                    bic=bic.strip()
                )
                db.session.add(new_bank)
                posted_bank_ids.add(new_bank.id)

            bank_index += 1

        # Delete removed bank accounts (only if we have some posted banks)
        if posted_bank_ids:
            BankAccount.query.filter(
                BankAccount.company_id == company.id,
                BankAccount.id.notin_(list(posted_bank_ids))
            ).delete(synchronize_session=False)
        elif bank_index == 0:
            # If no bank accounts were submitted at all, delete all existing ones
            BankAccount.query.filter_by(company_id=company.id).delete()

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('management.organization_profile'))

    return render_template('management/organization.html', company=company)
