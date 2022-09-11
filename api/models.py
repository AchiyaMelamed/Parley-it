from django.db import models
import uuid

from datetime import date


# Create your models here.
class BankAccount(models.Model):
    uuid  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account_number = models.CharField(max_length=100)

    def __str__(self):
        return str(self.account_number)

class Transaction(models.Model):
    id = models.AutoField(primary_key=True)
    src_bank_account = models.ForeignKey(BankAccount, related_name="sources", on_delete=models.CASCADE)
    dst_bank_account = models.ForeignKey(BankAccount, related_name="detinations", on_delete=models.CASCADE)
    amount = models.IntegerField()
    direction = models.CharField(max_length=10, choices=(("credit", "credit"), ("debit", "debit")), default="debit")
    schedule = models.DateField(default=date.today())
    result = models.CharField(max_length=10, choices=(("pending", "pending"), ("success", "success"), ("failed", "fail")), default="pending")

    def __str__(self):
        return f"{self.id}"


