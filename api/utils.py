import requests
from Parleyit.settings import BASE_URL
from .models import *

from datetime import datetime, date, timedelta

def perform_transaction_and_check_result(src_bank_account_obj, dst_bank_account_obj, amount, direction):
    """make a transaction, get the transaction id, then get the report and check if the transaction success/fail
    

    Args:
        src_bank_account_obj (BankAccount): 
        dst_bank_account_obj (BankAccount): 
        amount (Float): 
        direction (String): credit/debit
    
    Return: 
    transaction_id (Integer)
    result (Boolean): True - 'success', False - 'fail'
    """
    # make the credit (amount)
    perform_transaction_json = {
                        "src_bank_account": src_bank_account_obj.account_number,
                        "dst_bank_account": dst_bank_account_obj.account_number,
                        "amount": amount,
                        "direction": "credit"}
    response = requests.post(BASE_URL+"perform_transaction/", json=perform_transaction_json)
    response_json = response.json()
    transaction_id = response_json["transaction_id"]
    
    # check if the credit secceed
    report = requests.get(BASE_URL+"download_report/")
    report_json = report.json()
    results = report_json["report"]
    result = [result["result"] for result in results if result["transaction_id"] == transaction_id]
    
    return transaction_id, "success" in result
    
    
def perform_advance_twelve_debits(src_bank_account_obj, dst_bank_account_obj, amount, direction):
    """create ScheduledTransaction, 
       and the dates it will perform.

    Args:
        src_bank_account_obj (BankAccount)
        dst_bank_account_obj (BankAccount)
        amount (Float)
        direction (String): credit/debit

    Returns:
        new_scheduled_transaction: ScheduledTransaction to perform
        scheduled_dates: 12 dates to perform the new_scheduled_transaction
    """
    # create schedule transaction
    # TODO: Make creation as func in ScheduledTransaction
    one_pay = amount / 12
    new_scheduled_transaction = ScheduledTransaction(src_bank_account=src_bank_account_obj, dst_bank_account=dst_bank_account_obj, amount=one_pay, direction=direction)
    new_scheduled_transaction.save()
    new_scheduled_transaction = ScheduledTransaction.objects.get(id=new_scheduled_transaction.id)
    
    # calculate the dates to make transaction in each
    today = date.today()
    next_sunday = today + timedelta( (6 - today.weekday() % 7) )
    scheduled_dates = [next_sunday + timedelta(weeks=i) for i in range(12)]

    return new_scheduled_transaction, scheduled_dates