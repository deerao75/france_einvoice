from app import create_app, db
from app.models.company import Company, CompanyAddress
from app.models.user import User, UserCompany
from werkzeug.security import generate_password_hash
import random

app = create_app()

with app.app_context():
    db.create_all()  # Creates tables if they don't exist

    # Check if company exists
    if not Company.query.first():
        print("Creating default company...")

        # 1. Create Company (Basic Info Only)
        comp = Company(
            name="My Tech Corp",
            legal_name="My Tech Corporation Ltd",
            vat_number="FR123456789",
            siret="12345678900012",
            merchant_id=str(random.randint(1000000, 9999999))
        )
        db.session.add(comp)
        db.session.flush() # Get ID

        # 2. Add Default Addresses
        # Bill From
        bill_addr = CompanyAddress(
            company_id=comp.id,
            type='BILLING',
            label='HQ',
            address_line1="10 Rue de Rivoli",
            city="Paris",
            zip_code="75001",
            country="FR"
        )
        db.session.add(bill_addr)

        # Ship From
        ship_addr = CompanyAddress(
            company_id=comp.id,
            type='SHIPPING',
            label='Main Warehouse',
            address_line1="12 Avenue des Champs-Élysées",
            city="Paris",
            zip_code="75008",
            country="FR"
        )
        db.session.add(ship_addr)

        # 3. Create Admin User
        user = User(
            email="admin@test.com",
            password_hash=generate_password_hash("password")
        )
        db.session.add(user)
        db.session.commit()

        # 4. Link them
        link = UserCompany(user_id=user.id, company_id=comp.id, role='admin')
        db.session.add(link)
        db.session.commit()

        print("Database seeded! Login with admin@test.com / password")
    else:
        print("Database already contains data.")
