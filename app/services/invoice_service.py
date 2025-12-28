import os
from app.extensions import db
from app.models.invoice import Invoice, InvoiceStatus, InvoiceLine
from app.services.france_xml_generator import FranceXMLGenerator
from app.services.spain_xml_generator import SpainXMLGenerator
# Note: Integration client calls would typically be moved to async tasks

class InvoiceService:

    @staticmethod
    def create_invoice(data, company_id):
        # Create Invoice Object
        new_inv = Invoice(
            company_id=company_id,
            customer_id=data['customer_id'],
            invoice_number=data['invoice_number'], # In real app, auto-generate this
            invoice_date=data['invoice_date'],
            country_of_supply=data['country_of_supply'],
            status=InvoiceStatus.DRAFT
        )

        # Add Lines and Calculate Totals (simplified logic)
        total_net = 0
        total_vat = 0

        for line_data in data['lines']:
            qty = float(line_data['quantity'])
            price = float(line_data['unit_price'])
            rate = float(line_data['vat_rate'])

            line_net = qty * price
            line_vat = line_net * (rate / 100)

            total_net += line_net
            total_vat += line_vat

            new_line = InvoiceLine(
                description=line_data['description'],
                quantity=qty,
                unit_price=price,
                vat_rate=rate,
                line_gross=line_net + line_vat
            )
            new_inv.lines.append(new_line)

        new_inv.total_net = total_net
        new_inv.total_vat = total_vat
        new_inv.total_gross = total_net + total_vat

        db.session.add(new_inv)
        db.session.commit()
        return new_inv

    @staticmethod
    def prepare_for_sending(invoice_id):
        invoice = Invoice.query.get_or_404(invoice_id)

        # 1. Generate XML
        xml_content = ""
        if invoice.country_of_supply == 'FR':
            xml_content = FranceXMLGenerator.build_invoice_xml(invoice)
        elif invoice.country_of_supply == 'ES':
            xml_content = SpainXMLGenerator.build_invoice_xml(invoice)

        # 2. Save XML to disk (stub path)
        filename = f"invoice_{invoice.id}.xml"
        path = os.path.join('storage', filename)
        os.makedirs('storage', exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(xml_content)

        invoice.xml_path = path
        invoice.status = InvoiceStatus.READY_TO_SEND
        db.session.commit()

        # 3. Trigger Async Task here (omitted for brevity, would call rq/celery)
        # tasks.send_invoice.delay(invoice.id)
        return invoice
