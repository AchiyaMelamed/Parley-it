from Parleyit.settings import BASE_URL
from .models import Transaction, ScheduledTransaction

import requests
import datetime

def perform_transaction_and_check_result(src_bank_account_obj, dst_bank_account_obj, amount, direction):
    """make a transaction, get the transaction id, then get the report and check if the transaction success/fail
    

        Args:
            src_bank_account_obj (BankAccount): 
            dst_bank_account_obj (BankAccount): 
            amount (Float): 
            direction (String): credit/debit
        
        Returns:
        transaction_id (Integer)
        result (Boolean): True - 'success', False - 'fail'
    """
    # make the credit (amount)
    perform_transaction_json = {
                        "src_bank_account": src_bank_account_obj.account_number,
                        "dst_bank_account": dst_bank_account_obj.account_number,
                        "amount": amount,
                        "direction": direction}
    response = requests.post(BASE_URL+"perform_transaction/", json=perform_transaction_json)
    response_json = response.json()
    transaction_id = response_json["transaction_id"]
    
    # check if the credit secceed
    report = requests.get(BASE_URL+"download_report/")
    report_json = report.json()
    results = report_json["report"]
    result = [result["result"] for result in results if result["transaction_id"] == transaction_id]
    
    return transaction_id, "success" in result
    
    
def create_scheduled_transaction_object_and_dates(src_bank_account_obj, dst_bank_account_obj, credit_transaction_id, amount, direction):
    """create ScheduledTransaction, and the dates it will perform.

        Args:
            src_bank_account_obj (BankAccount)
            dst_bank_account_obj (BankAccount)
            amount (Float)
            direction (String): credit/debit

        Returns:
        new_scheduled_transaction_obj: ScheduledTransaction to perform
        scheduled_dates: 12 dates to perform the new_scheduled_transaction
    """
    # create schedule transaction
    credit_transaction_obj = Transaction.objects.get(id=credit_transaction_id)
    one_pay = amount / 12
    new_scheduled_transaction_obj = ScheduledTransaction.objects.create(src_bank_account=src_bank_account_obj, dst_bank_account=dst_bank_account_obj, credit_transaction=credit_transaction_obj, amount=one_pay, direction=direction)
    
    # calculate the dates to make transaction in each
    today = datetime.date.today()
    next_sunday = today + datetime.timedelta( (6 - today.weekday() % 7) )
    scheduled_dates = [next_sunday + datetime.timedelta(weeks=i) for i in range(12)]

    return new_scheduled_transaction_obj, scheduled_dates