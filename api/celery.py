from celery.schedules import crontab
from celery.task import periodic_task

from datetime import date
from time import sleep

from .models import Transaction

@periodic_task(run_every=crontab(hour=0, minute=0))
def pay_once_aweek(transactions_list):
    done = []
    if not transactions_list:
        return
    today = date.today()
    for transaction in transactions_list:
        if transaction.schedule == today:
            # perform_transaction(transaction)
            done.append(transaction)
    for t in done:
        transactions_list.pop(transactions_list.index(t))
    sleep(5)
    pay_once_aweek(transactions_list)