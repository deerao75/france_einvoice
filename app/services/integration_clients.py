import random
import time

class FrancePDPClient:
    """Stub for French Public Billing Portal"""
    def send_invoice(self, invoice_data_xml):
        # SIMULATION:
        print(f"Connecting to Chorus Pro / PDP...")
        time.sleep(1) # Simulate network latency
        return {
            "success": True,
            "external_id": f"FR-PDP-{random.randint(10000,99999)}",
            "message": "Deposited successfully"
        }

class SpainFaceB2BClient:
    """Stub for Spanish FACeB2B"""
    def send_invoice(self, invoice_data_xml):
        # SIMULATION
        print(f"Connecting to FACeB2B...")
        time.sleep(1)
        return {
            "success": True,
            "external_id": f"ES-FACE-{random.randint(10000,99999)}",
            "message": "Registered in FACe"
        }
