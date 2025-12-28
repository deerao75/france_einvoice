from xml.etree.ElementTree import Element, SubElement, tostring
from app.models.invoice import Invoice

class SpainXMLGenerator:
    """Generates FacturaE style XML for Spain"""

    @staticmethod
    def build_invoice_xml(invoice: Invoice) -> str:
        root = Element('fe:Facturae', {'xmlns:fe': 'http://www.facturae.gob.es/formato/Versiones/Facturae/3_2_1.xml'})

        header = SubElement(root, 'FileHeader')
        SubElement(header, 'SchemaVersion').text = "3.2.1"
        SubElement(header, 'Modality').text = "I" # Individual
        SubElement(header, 'InvoiceIssuerType').text = "EM"

        parties = SubElement(root, 'Parties')
        # ... Mapping Seller/Buyer would go here ...

        invoices_node = SubElement(root, 'Invoices')
        inv = SubElement(invoices_node, 'Invoice')

        inv_header = SubElement(inv, 'InvoiceHeader')
        SubElement(inv_header, 'InvoiceNumber').text = invoice.invoice_number
        SubElement(inv_header, 'InvoiceDate').text = str(invoice.invoice_date)

        inv_totals = SubElement(inv, 'InvoiceTotals')
        SubElement(inv_totals, 'TotalGrossAmount').text = str(invoice.total_gross)

        items = SubElement(inv, 'Items')
        for line in invoice.lines:
            item = SubElement(items, 'InvoiceLine')
            SubElement(item, 'ItemDescription').text = line.description
            SubElement(item, 'TotalCost').text = str(line.line_gross)

        return tostring(root, encoding='unicode')
