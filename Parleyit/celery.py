from celery.schedules import crontab
from celery.task import periodic_task

from Parleyit.settings import BASE_URL

from datetime import datetime, date
from time import sleep

from api.models import Transaction, ScheduledTransaction, SuccessScheduledTransaction, FailScheduledTransaction
from api.utils import perform_transaction_and_check_result

import threading

import requests


class PerformTransactionEveryWeek(threading.Thread):
    def __init__(self, scheduled_transaction, scheduled_dates, *args, **kwargs):
        super(PerformTransactionEveryWeek, self).__init__(*args, **kwargs)
        self.scheduled_transaction = scheduled_transaction
        
        self.src_bank_account = self.scheduled_transaction.src_bank_account
        self.dst_bank_account = self.scheduled_transaction.dst_bank_account
        self.amount = self.scheduled_transaction.amount
        self.direction = self.scheduled_transaction.direction
        
        self.scheduled_dates = scheduled_dates
        self.week_before_the_last = self.scheduled_dates[-2]
        self.scheduled_dates_left = scheduled_dates
        self.amount_week_before_last = 0
    
    
    def calculate_secs_to_next_schedule(self):
        scheduled_date = self.scheduled_dates_left[0]
        now = datetime.now()
        schedule_datetime = datetime(scheduled_date.year, scheduled_date.month, scheduled_date.day, 0, 0)
        totla_secs = (schedule_datetime-now).total_seconds()
        return totla_secs + 60
        
        
    def perform_todays_transaction(self):
        print("starting...")

        today = date.today()
        # perform scheduled transaction for today or before
        if today >= self.scheduled_dates_left[0]:
            
            # if we are in the week before the last then debit all the failed transactions, if failed again send to FailScheduledTransaction table
            if len(self.scheduled_dates_left) == 2:
                self.amount_week_before_last = self.amount + self.amount * self.scheduled_transaction.fail
                transaction_id ,success = perform_transaction_and_check_result(
                                                                            src_bank_account_obj=self.src_bank_account,
                                                                            dst_bank_account_obj=self.dst_bank_account,
                                                                            amount=self.amount_week_before_last,
                                                                            direction=self.direction
                                                                            )
                transaction_obj = Transaction.objects.get(id=transaction_id)
                    
                if success:
                    self.scheduled_transaction.success += 1 + self.scheduled_transaction.fail
                    self.scheduled_transaction.fail = 0
                    self.scheduled_transaction.save()
                    success_transaction = SuccessScheduledTransaction(
                                                                    src_bank_account=self.src_bank_account,
                                                                    dst_bank_account=self.dst_bank_account,
                                                                    transaction_id=transaction_obj,
                                                                    amount=self.amount_week_before_last,
                                                                    direction=self.direction,
                                                                    date=self.scheduled_dates_left[0]
                                                                    )
                    success_transaction.save()
                else:
                    self.scheduled_transaction.fail_completely = self.scheduled_transaction.fail + 1
                    self.scheduled_transaction.fail = 0
                    self.scheduled_transaction.save()
                    fail_transaction = FailScheduledTransaction(
                                                                src_bank_account=self.src_bank_account,
                                                                dst_bank_account=self.dst_bank_account,
                                                                transaction_id=transaction_obj,
                                                                amount=self.amount_week_before_last,
                                                                direction=self.direction,
                                                                date=self.scheduled_dates_left[0]
                                                                )
                    fail_transaction.save()
                
            
            # if we are before the one week before the last or in the last week   
            else:
                transaction_id ,success = perform_transaction_and_check_result(src_bank_account_obj=self.src_bank_account,
                                                                               dst_bank_account_obj=self.dst_bank_account,
                                                                               amount=self.amount,
                                                                               direction=self.direction
                                                                               )
                transaction_obj = Transaction.objects.get(id=transaction_id)
                if success:
                    transaction_obj = Transaction.objects.get(id=transaction_id)
                    self.scheduled_transaction.success += 1
                    self.scheduled_transaction.save()
                    success_transaction = SuccessScheduledTransaction(src_bank_account=self.src_bank_account,
                                                                      dst_bank_account=self.dst_bank_account,
                                                                      transaction_id=transaction_obj,
                                                                      amount=self.amount,
                                                                      direction=self.direction,
                                                                      date=self.scheduled_dates_left[0])
                    success_transaction.save()
                else:
                    if len(self.scheduled_dates_left) == 1:
                        self.scheduled_transaction.fail_completely += 1
                        fail_transaction = FailScheduledTransaction(
                                                                src_bank_account=self.src_bank_account,
                                                                dst_bank_account=self.dst_bank_account,
                                                                transaction_id=transaction_obj,
                                                                amount=self.amount,
                                                                direction=self.direction,
                                                                date=self.scheduled_dates_left[0]
                                                                )
                        fail_transaction.save()
                    else:
                        self.scheduled_transaction.fail += 1
                        self.scheduled_transaction.save()
                
            self.scheduled_dates.pop(0)
    
    
    def run(self):
        while self.scheduled_transaction.success + self.scheduled_transaction.fail + self.scheduled_transaction.fail_completely < 12:
            secs_to_sleep = self.calculate_secs_to_next_schedule()
            print("sleeping ", secs_to_sleep)
            sleep(secs_to_sleep)
            self.perform_todays_transaction()