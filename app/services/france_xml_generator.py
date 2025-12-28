from xml.etree.ElementTree import Element, SubElement, tostring
from app.models.invoice import Invoice

class FranceXMLGenerator:
    """Generates Factur-X / UBL style XML for France"""

    @staticmethod
    def build_invoice_xml(invoice: Invoice) -> str:
        # Root Element (simplified UBL structure)
        root = Element('rsm:CrossIndustryInvoice', {
            'xmlns:rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
            'xmlns:udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100'
        })

        # Header / Context
        context = SubElement(root, 'rsm:ExchangedDocumentContext')
        guideline = SubElement(context, 'ram:GuidelineSpecifiedDocumentContextParameter')
        SubElement(guideline, 'ram:ID').text = "urn:cen.eu:en16931:2017" # Standard ID

        # Document Header
        header = SubElement(root, 'rsm:ExchangedDocument')
        SubElement(header, 'ram:ID').text = invoice.invoice_number
        SubElement(header, 'ram:TypeCode').text = "380" # Commercial Invoice

        # Trade Transaction
        trade = SubElement(root, 'rsm:SupplyChainTradeTransaction')

        # Line Items
        for line in invoice.lines:
            line_item = SubElement(trade, 'ram:IncludedSupplyChainTradeLineItem')
            prod = SubElement(line_item, 'ram:SpecifiedTradeProduct')
            SubElement(prod, 'ram:Name').text = line.description

            price = SubElement(line_item, 'ram:NetPriceProductTradePrice')
            SubElement(price, 'ram:ChargeAmount').text = str(line.unit_price)

        # Totals
        settlement = SubElement(trade, 'ram:ApplicableHeaderTradeSettlement')
        totals = SubElement(settlement, 'ram:SpecifiedTradeSettlementHeaderMonetarySummation')
        SubElement(totals, 'ram:TaxBasisTotalAmount').text = str(invoice.total_net)
        SubElement(totals, 'ram:GrandTotalAmount').text = str(invoice.total_gross)

        return tostring(root, encoding='unicode')
