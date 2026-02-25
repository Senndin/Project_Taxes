import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from tax_service.services import TaxCalculationService
service = TaxCalculationService()
try:
    order = service.process_order(lat=40.6930, lon=-73.7451, subtotal=200.00)
    print(f"Order: subtotal={order.subtotal}, tax={order.tax_amount}, calc={order.breakdown}")
except Exception as e:
    print("Error on order 1:", e)

try:
    order2 = service.process_order(lat=40.7128, lon=-74.0060, subtotal=100.00)
    print(f"Order2: subtotal={order2.subtotal}, tax={order2.tax_amount}, calc={order2.breakdown}")
except Exception as e:
    print("Error on order 2:", e)
