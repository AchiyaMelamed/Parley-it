from celery.schedules import crontab
from celery.task import periodic_task

from Parleyit.settings import BASE_URL

from datetime import date
from time import sleep

from api.models import Transaction, ScheduledTransaction

import threading

import requests
import schedule

def perform_todays_advance(self):
    print("starting...")
    if self.scheduled_transaction.success + self.scheduled_transaction.success == 12:
        self.stop()
        return

    today = date.today()
    # perform scheduled transactions for today or before
    if today <= scheduled_transaction.schedule:
        perform_transaction_json = {
            "src_bank_account": scheduled_transaction.src_bank_account.account_number,
            "dst_bank_account": scheduled_transaction.dst_bank_account.account_number,
            "amount": scheduled_transaction.amount,
            "direction": scheduled_transaction.direction}
        response = requests.post(BASE_URL+"perform_transaction/", json=perform_transaction_json)
        response_json = response.json()
        transaction_created = Transaction.objects.get(id=response_json['transaction_id'])
        
        # add the transaction to the scheduled_transaction and its id to performed_transactions_ids
        scheduled_transaction.transaction_id = transaction_created
        scheduled_transaction.save()
        self.performed_transactions_ids.append(response_json['transaction_id'])

            
    # get the results using download_report
    if self.performed_transactions_ids:
        report = requests.get(BASE_URL+"download_report/")
        report_json = report.json()
        results = report_json["report"]

        # reschedule fail scheduled transactions
        fail_ids = [result["transaction_id"] for result in results if result["result"] == "fail" and result["transaction_id"] in self.performed_transactions_ids]
        if fail_ids:
                fail_scheduled_transactions = [t for t in self.scheduled_transactions_list if t.transaction_id.id in fail_ids]
                for fail_scheduled_transaction in fail_scheduled_transactions:
                    fail_scheduled_transaction.schedule = self.week_before_the_last
                    fail_scheduled_transaction.transaction_id = None
                    fail_scheduled_transaction.save()
        
        # delete success scheduled transactions
        success_ids = [result["transaction_id"] for result in results if result["result"] == "success" and result["transaction_id"] in self.performed_transactions_ids]
        if success_ids:
            success_scheduled_transactions = [t for t in self.scheduled_transactions_list if t.transaction_id.id in success_ids]
            for success_scheduled_transaction in success_scheduled_transactions:
                self.scheduled_transactions_list.pop(self.scheduled_transactions_list.index(success_scheduled_transaction))
                
            ScheduledTransaction.objects.filter(transaction_id__in=success_ids).delete()


            
    print("LEFT", self.scheduled_transactions_list)
    print("PERFORMED", self.performed_transactions_ids)

    self.performed_transactions_ids = []