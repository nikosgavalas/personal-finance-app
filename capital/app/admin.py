from django.contrib import admin

from .models import *

admin.site.register(Account)
admin.site.register(IncomeCategory)
admin.site.register(ExpenseCategory)
admin.site.register(IncomeSubcategory)
admin.site.register(ExpenseSubcategory)
admin.site.register(IncomeTransaction)
admin.site.register(ExpenseTransaction)
admin.site.register(TransferTransaction)
