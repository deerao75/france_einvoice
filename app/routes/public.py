from flask import Blueprint, render_template
from datetime import datetime

bp = Blueprint(
    'public',
    __name__,
    template_folder='templates'
)

# -------------------------------------------------
# Common context for all public pages
# -------------------------------------------------
def public_context(**kwargs):
    base_context = {
        "brand_name": "Invoicer",
        "current_year": datetime.now().year
    }
    base_context.update(kwargs)
    return base_context


# -------------------------------------------------
# Home / Landing Page
# -------------------------------------------------
@bp.route('/')
def index():
    return render_template(
        'index.html',
        **public_context(
            page_title="Invoicer – Professional E-Invoicing Made Simple",
            page_description="Compliant e-invoicing for France & EU. Create, manage, and send invoices effortlessly."
        )
    )


# -------------------------------------------------
# Subscription / Pricing Page
# -------------------------------------------------
@bp.route('/subscription')
def subscription():
    return render_template(
        'public/subscription.html',
        **public_context(
            page_title="Pricing & Plans – Invoicer",
            page_description="Flexible pricing plans for SMEs and professionals."
        )
    )


# -------------------------------------------------
# Contact Page
# -------------------------------------------------
@bp.route('/contact')
def contact():
    return render_template(
        'public/contact.html',
        **public_context(
            page_title="Contact Us – Invoicer",
            page_description="Get in touch with our sales or support team."
        )
    )
