from django.db import models
from django.contrib.auth.models import User
import uuid
import datetime

# Create your models here.
class BankAccount(models.Model):
    id  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account_number = models.CharField(max_length=10)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        if not self.account_number:
            next_number = BankAccount.objects.all().count() + 1
            self.account_number = str(next_number) + "0" * (10 - len(str(next_number)))
        super(BankAccount, self).save()                                         

    def __str__(self):
        model = BankAccount
        return f"{self.user}: {self.account_number}"

class Transaction(models.Model):
    id = models.AutoField(primary_key=True)
    src_bank_account = models.ForeignKey(BankAccount, related_name="sources", on_delete=models.CASCADE)
    dst_bank_account = models.ForeignKey(BankAccount, related_name="detinations", on_delete=models.CASCADE)
    amount = models.FloatField()
    direction = models.CharField(max_length=10, choices=(("credit", "credit"), ("debit", "debit")), default="debit")
    result = models.CharField(max_length=10, choices=(("success", "success"), ("fail", "fail")), null=True, blank=True)
    date = models.DateField(default=datetime.date.today)

    def __str__(self):
        return f"{self.id}. {self.result}: {self.src_bank_account.user} -> {self.dst_bank_account.user} ({self.direction}, {self.amount})"

class ScheduledTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    src_bank_account = models.ForeignKey(BankAccount, related_name="scheduled_sources", on_delete=models.CASCADE)
    dst_bank_account = models.ForeignKey(BankAccount, related_name="scheduled_detinations", on_delete=models.CASCADE)
    started_at = models.DateField(default=datetime.date.today)
    credit_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.FloatField()
    direction = models.CharField(max_length=10, choices=(("credit", "credit"), ("debit", "debit")), default="debit")
    token = models.CharField(max_length=300)
    success = models.IntegerField(default=0)
    fail_once = models.IntegerField(default=0)
    fail_completely = models.IntegerField(default=0)
    dates_done = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.id}. {(self.dates_done)/12*100}%: {self.src_bank_account.user} -> {self.dst_bank_account.user} ({self.direction}, {self.amount})"

class SuccessScheduledTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    transaction_id = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.id}: {self.transaction_id}"

class FailScheduledTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    transaction_id = models.ForeignKey(Transaction, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id}: {self.transaction_id}"
