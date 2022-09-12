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
    amount = models.FloatField()
    direction = models.CharField(max_length=10, choices=(("credit", "credit"), ("debit", "debit")), default="debit")
    result = models.CharField(max_length=10, choices=(("success", "success"), ("fail", "fail")), null=True, blank=True)
    date = models.DateField(default=date.today)

    def __str__(self):
        return f"{self.id}"

class ScheduledTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    src_bank_account = models.ForeignKey(BankAccount, related_name="scheduled_sources", on_delete=models.CASCADE)
    dst_bank_account = models.ForeignKey(BankAccount, related_name="scheduled_detinations", on_delete=models.CASCADE)
    started_at = models.DateField(default=date.today)
    amount = models.FloatField()
    direction = models.CharField(max_length=10, choices=(("credit", "credit"), ("debit", "debit")), default="debit")
    success = models.IntegerField(default=0)
    fail = models.IntegerField(default=0)
    fail_completely = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.id}"

class SuccessScheduledTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    src_bank_account = models.ForeignKey(BankAccount, related_name="success_sources", on_delete=models.CASCADE)
    dst_bank_account = models.ForeignKey(BankAccount, related_name="success_detinations", on_delete=models.CASCADE)
    transaction_id = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    amount = models.FloatField()
    direction = models.CharField(max_length=10, choices=(("credit", "credit"), ("debit", "debit")), default="debit")
    date = models.DateField(default=date.today)
    
    def __str__(self):
        return f"{self.id}"

class FailScheduledTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    src_bank_account = models.ForeignKey(BankAccount, related_name="fail_sources", on_delete=models.CASCADE)
    dst_bank_account = models.ForeignKey(BankAccount, related_name="fail_detinations", on_delete=models.CASCADE)
    transaction_id = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    amount = models.FloatField()
    direction = models.CharField(max_length=10, choices=(("credit", "credit"), ("debit", "debit")), default="debit")
    date = models.DateField(default=date.today)
    
    def __str__(self):
        return f"{self.id}"
