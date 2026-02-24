from django.contrib import admin
from .models import TaxRateAdmin, Order, ImportJob

# Register your models here.
admin.site.register(TaxRateAdmin)
admin.site.register(Order)
admin.site.register(ImportJob)
