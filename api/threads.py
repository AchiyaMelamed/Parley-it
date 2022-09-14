from api.models import Transaction, SuccessScheduledTransaction, FailScheduledTransaction
from api.utils import perform_transaction_and_check_result

import datetime
from time import sleep
import threading


class PerformTransactionEveryWeek(threading.Thread):
    def __init__(self, scheduled_transaction, scheduled_dates, *args, **kwargs):
        super(PerformTransactionEveryWeek, self).__init__(*args, **kwargs)
        self.lock = threading.Lock()
        
        self.scheduled_transaction = scheduled_transaction
        self.src_bank_account = self.scheduled_transaction.src_bank_account
        self.dst_bank_account = self.scheduled_transaction.dst_bank_account
        self.amount = self.scheduled_transaction.amount
        self.direction = self.scheduled_transaction.direction
        self.token = self.scheduled_transaction.token
        
        self.scheduled_dates = scheduled_dates
        self.scheduled_dates_left = scheduled_dates
        self.amount_week_before_last = 0
    
    
    def calculate_secs_to_next_schedule(self):
        scheduled_date = self.scheduled_dates_left[0]
        now = datetime.datetime.now()
        schedule_datetime = datetime.datetime(scheduled_date.year, scheduled_date.month, scheduled_date.day, 0, 0)
        totla_secs = (schedule_datetime - now).total_seconds()
        return totla_secs + 60
        
        
    def perform_todays_transaction(self):
        today = datetime.date.today()
        # perform scheduled transaction if scheduled for today or before
        if today >= self.scheduled_dates_left[0]:
            with self.lock:
                # if we are in the week before the last then debit all the failed transactions, if failed again send to FailScheduledTransaction table
                if len(self.scheduled_dates_left) == 2:
                    self.amount_week_before_last = self.amount + self.amount * self.scheduled_transaction.fail_once
                    transaction_id ,success = perform_transaction_and_check_result(
                                                                                src_bank_account_obj=self.src_bank_account,
                                                                                dst_bank_account_obj=self.dst_bank_account,
                                                                                amount=self.amount_week_before_last,
                                                                                direction=self.direction,
                                                                                token = self.token
                                                                                )
                    transaction_obj = Transaction.objects.get(id=transaction_id)
                        
                    if success:
                        self.scheduled_transaction.success += 1 + self.scheduled_transaction.fail_once
                        self.scheduled_transaction.save()
                        success_transaction = SuccessScheduledTransaction.objects.create(transaction_id=transaction_obj)

                    else:
                        self.scheduled_transaction.fail_completely = self.scheduled_transaction.fail_once + 1
                        self.scheduled_transaction.save()
                        fail_transaction = FailScheduledTransaction.objects.create(transaction_id=transaction_obj)
                    
                
                # if we are before the one week before the last or in the last week   
                else:
                    transaction_id ,success = perform_transaction_and_check_result(
                                                                                src_bank_account_obj=self.src_bank_account,
                                                                                dst_bank_account_obj=self.dst_bank_account,
                                                                                amount=self.amount,
                                                                                direction=self.direction,
                                                                                token=self.token
                                                                                )
                    transaction_obj = Transaction.objects.get(id=transaction_id)
                    
                    if success:
                        transaction_obj = Transaction.objects.get(id=transaction_id)
                        self.scheduled_transaction.success += 1
                        self.scheduled_transaction.save()
                        success_transaction = SuccessScheduledTransaction.objects.create(transaction_id=transaction_obj,)

                    else:
                        if len(self.scheduled_dates_left) == 1:
                            self.scheduled_transaction.fail_completely += 1
                            self.scheduled_transaction.save()
                            fail_transaction = FailScheduledTransaction.objects.create(transaction_id=transaction_obj,)

                        else:
                            self.scheduled_transaction.fail_once += 1
                            self.scheduled_transaction.save()
                    
                self.scheduled_dates_left.pop(0)
                self.scheduled_transaction.dates_done += 1
                self.scheduled_transaction.save()
    
    
    def run(self):
        while self.scheduled_dates_left:
            secs_to_sleep = self.calculate_secs_to_next_schedule()
            sleep(secs_to_sleep)
            self.perform_todays_transaction()