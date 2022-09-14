from django.contrib import admin
from .models import BankAccount, Transaction, ScheduledTransaction, SuccessScheduledTransaction, FailScheduledTransaction


# Register your models here.
admin.site.register(BankAccount)
admin.site.register(Transaction)
admin.site.register(ScheduledTransaction)
admin.site.register(SuccessScheduledTransaction)
admin.site.register(FailScheduledTransaction)
