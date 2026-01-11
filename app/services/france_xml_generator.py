from xml.etree.ElementTree import Element, SubElement, tostring
from app.models.invoice import Invoice
from datetime import datetime

class FranceXMLGenerator:
    """
    Generates Factur-X / UBL style XML for France (EN16931).
    Maps new mandatory fields (Legal Form, Capital, RCS, PO, Tax Point).
    """

    @staticmethod
    def build_invoice_xml(invoice: Invoice) -> str:
        # Root Element
        root = Element('rsm:CrossIndustryInvoice', {
            'xmlns:rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
            'xmlns:ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
            'xmlns:udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100',
            'xmlns:qdt': 'urn:un:unece:uncefact:data:standard:QualifiedDataType:100'
        })

        # 1. ExchangedDocumentContext (Standard Profile)
        context = SubElement(root, 'rsm:ExchangedDocumentContext')
        guideline = SubElement(context, 'ram:GuidelineSpecifiedDocumentContextParameter')
        # "Basic" profile for broad compatibility (urn:cen.eu:en16931:2017#compliant#urn:factur-x.eu:1p0:basic)
        SubElement(guideline, 'ram:ID').text = "urn:cen.eu:en16931:2017"

        # 2. ExchangedDocument (Header)
        header = SubElement(root, 'rsm:ExchangedDocument')
        SubElement(header, 'ram:ID').text = invoice.invoice_number
        # Type Code: 380 (Invoice), 381 (Credit Note)
        type_code = "381" if invoice.fr_document_type == "CREDIT_NOTE" else "380"
        SubElement(header, 'ram:TypeCode').text = type_code

        # Issue Date
        issue_date = SubElement(header, 'ram:IssueDateTime')
        SubElement(issue_date, 'udt:DateTimeString', format='102').text = invoice.invoice_date.strftime('%Y%m%d')

        # Included Note (Legal Footer Fallback)
        # We place the legal string (Form, Capital, RCS) here to ensure it is readable in the data
        if invoice.company:
            c = invoice.company
            legal_text = f"{c.name}"
            if c.legal_form: legal_text += f", {c.legal_form}"
            if c.share_capital: legal_text += f" au capital de {c.share_capital}"
            if c.rcs_city: legal_text += f", RCS {c.rcs_city}"
            if c.siret: legal_text += f", SIRET {c.siret}"

            note = SubElement(header, 'ram:IncludedNote')
            SubElement(note, 'ram:Content').text = legal_text
            SubElement(note, 'ram:SubjectCode').text = "ADU" # General Note

        # 3. SupplyChainTradeTransaction
        trade = SubElement(root, 'rsm:SupplyChainTradeTransaction')

        # --- A. IncludedSupplyChainTradeLineItem (Lines) ---
        for line in invoice.lines:
            line_item = SubElement(trade, 'ram:IncludedSupplyChainTradeLineItem')

            # AssociatedDocumentLineDocument (Line ID)
            line_doc = SubElement(line_item, 'ram:AssociatedDocumentLineDocument')
            SubElement(line_doc, 'ram:LineID').text = str(line.id)

            # SpecifiedTradeProduct (Product Name/Code)
            prod = SubElement(line_item, 'ram:SpecifiedTradeProduct')
            if line.hsn_sac_code:
                SubElement(prod, 'ram:GlobalID', schemeID='0001').text = line.hsn_sac_code
            SubElement(prod, 'ram:Name').text = line.description

            # SpecifiedLineTradeAgreement (Price)
            line_agree = SubElement(line_item, 'ram:SpecifiedLineTradeAgreement')
            net_price = SubElement(line_agree, 'ram:NetPriceProductTradePrice')
            SubElement(net_price, 'ram:ChargeAmount').text = str(line.unit_price)

            # SpecifiedLineTradeDelivery (Qty)
            line_deliv = SubElement(line_item, 'ram:SpecifiedLineTradeDelivery')
            SubElement(line_deliv, 'ram:BilledQuantity', unitCode='C62').text = str(line.quantity)

            # SpecifiedLineTradeSettlement (Tax)
            line_settle = SubElement(line_item, 'ram:SpecifiedLineTradeSettlement')
            line_tax = SubElement(line_settle, 'ram:ApplicableTradeTax')
            SubElement(line_tax, 'ram:TypeCode').text = "VAT"
            SubElement(line_tax, 'ram:CategoryCode').text = "S" # S=Standard, Z=Zero, E=Exempt (simplified)
            SubElement(line_tax, 'ram:RateApplicablePercent').text = str(line.vat_rate)

        # --- B. ApplicableHeaderTradeAgreement (Seller/Buyer/PO) ---
        agreement = SubElement(trade, 'ram:ApplicableHeaderTradeAgreement')

        # PO Number (Buyer Reference) - MANDATORY if exists
        if invoice.purchase_order_number:
            SubElement(agreement, 'ram:BuyerReference').text = invoice.purchase_order_number

        # Seller
        seller = SubElement(agreement, 'ram:SellerTradeParty')
        if invoice.company:
            SubElement(seller, 'ram:Name').text = invoice.company.name

            # Legal Org (Registration)
            if invoice.company.siren:
                legal_org = SubElement(seller, 'ram:SpecifiedLegalOrganization')
                SubElement(legal_org, 'ram:ID', schemeID='0002').text = invoice.company.siren # 0002=SIRENE

            # Address
            # (Assuming first billing address or defaults)
            s_addr = SubElement(seller, 'ram:PostalTradeAddress')
            SubElement(s_addr, 'ram:PostcodeCode').text = "75000" # Placeholder/Dynamic
            SubElement(s_addr, 'ram:LineOne').text = "Address Line" # Placeholder/Dynamic
            SubElement(s_addr, 'ram:CountryID').text = "FR"

            # VAT
            if invoice.company.vat_number:
                s_tax = SubElement(seller, 'ram:SpecifiedTaxRegistration')
                SubElement(s_tax, 'ram:ID', schemeID='VA').text = invoice.company.vat_number

        # Buyer
        buyer = SubElement(agreement, 'ram:BuyerTradeParty')
        # We fetch customer via invoice.customer if accessible
        # For this snippet, using basic Placeholders or direct access if lazy loading works
        SubElement(buyer, 'ram:Name').text = invoice.customer_name if hasattr(invoice, 'customer_name') else "Customer"
        if invoice.customer_vat:
            b_tax = SubElement(buyer, 'ram:SpecifiedTaxRegistration')
            SubElement(b_tax, 'ram:ID', schemeID='VA').text = invoice.customer_vat

        # PO Number specific doc reference (Double mapping often recommended)
        if invoice.purchase_order_number:
            ord_ref = SubElement(agreement, 'ram:BuyerOrderReferencedDocument')
            SubElement(ord_ref, 'ram:IssuerAssignedID').text = invoice.purchase_order_number

        # --- C. ApplicableHeaderTradeDelivery (Date of Supply) ---
        delivery = SubElement(trade, 'ram:ApplicableHeaderTradeDelivery')

        # Tax Point Date / Date of Supply
        # Used if different from IssueDate, but good practice to include always for "Livraison"
        event_date = invoice.tax_point_date or invoice.invoice_date
        chain_event = SubElement(delivery, 'ram:ActualDeliverySupplyChainEvent')
        SubElement(chain_event, 'ram:OccurrenceDateTime').SubElement('udt:DateTimeString', format='102').text = event_date.strftime('%Y%m%d')

        # --- D. ApplicableHeaderTradeSettlement (Payment/Totals) ---
        settlement = SubElement(trade, 'ram:ApplicableHeaderTradeSettlement')

        # Payment Means
        if invoice.fr_payment_means:
            pay_means = SubElement(settlement, 'ram:SpecifiedTradeSettlementPaymentMeans')
            # Map codes: 30=Transfer, 58=Direct Debit, 48=Card, 10=Cash, 20=Cheque
            code_map = {'TRANSFER': '30', 'DIRECT_DEBIT': '58', 'CARD': '48', 'CASH': '10', 'CHEQUE': '20'}
            SubElement(pay_means, 'ram:TypeCode').text = code_map.get(invoice.fr_payment_means, '30')

        # Totals
        totals = SubElement(settlement, 'ram:SpecifiedTradeSettlementHeaderMonetarySummation')
        SubElement(totals, 'ram:LineTotalAmount').text = str(invoice.total_net)
        SubElement(totals, 'ram:TaxBasisTotalAmount').text = str(invoice.total_net)
        SubElement(totals, 'ram:TaxTotalAmount', currencyID='EUR').text = str(invoice.total_tax)
        SubElement(totals, 'ram:GrandTotalAmount', currencyID='EUR').text = str(invoice.total_gross)
        SubElement(totals, 'ram:DuePayableAmount', currencyID='EUR').text = str(invoice.total_gross)

        return tostring(root, encoding='unicode')
