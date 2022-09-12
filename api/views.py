from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist

from Parleyit.settings import BASE_URL

import asyncio
import requests

from .models import BankAccount, Transaction, ScheduledTransaction
from .utils import perform_transaction_and_check_result, perform_advance_twelve_debits
from Parleyit.celery import PerformTransactionEveryWeek


from threading import Thread

from datetime import date, timedelta

import random

# Create your views here.
@api_view(["POST"])
def perform_transaction(request):
    src_bank_account = request.data["src_bank_account"]
    dst_bank_account = request.data["dst_bank_account"]
    amount = request.data["amount"]
    direction = request.data["direction"]
    result = random.choice(["success", "fail"])
    new_transaction = Transaction(src_bank_account=BankAccount.objects.get(account_number=src_bank_account), dst_bank_account=BankAccount.objects.get(account_number=dst_bank_account), amount=amount, direction=direction, result=result)
    new_transaction.save()
    return JsonResponse({"transaction_id": new_transaction.id})

@api_view(["GET"])
def download_report(request):
    today = date.today()
    all_transactions = Transaction.objects.all()
    ids = [t.id for t in all_transactions]
    results = [t.result for t in all_transactions if t.date + timedelta(days=5) >= today]
    
    return JsonResponse({"report":[{"transaction_id": id, "result": result} for (id, result) in zip(ids, results)]})



@api_view(["POST"])
def perform_advance(request):
    # get the data of the request
    try:
        dst_bank_account = request.data["dst_bank_account"]
        amount = request.data["amount"]
    except KeyError as ex:
        return JsonResponse({"500": "Please post dst_bank_account and an amount"})
    
    # check if there is such BankAccount and get it
    try:
        customer_bank_account_obj = BankAccount.objects.get(account_number=dst_bank_account)
    except ObjectDoesNotExist as ex:
        return JsonResponse({"500": "Bank Account dosn't exists."})
    
    
    # TODO: check what the source should be (create manager account every time the server start running if doesn't exists)
    manager_bank_account_obj = BankAccount.objects.get(account_number="000000") 

    # perfom the credit transaction and check if succeed
    transaction_id, success = perform_transaction_and_check_result(src_bank_account_obj=manager_bank_account_obj, dst_bank_account_obj=customer_bank_account_obj, amount=amount, direction="credit")
    if not success:
        return JsonResponse({"500": f"There was a problem while performing the transaction ({transaction_id}), please try again."})
    
       
    # get the scheduled transaction and its scheduled dates
    new_scheduled_transaction, scheduled_dates = perform_advance_twelve_debits(src_bank_account_obj=customer_bank_account_obj, dst_bank_account_obj=manager_bank_account_obj, amount=amount, direction="debit")
    advance_transacrion_thread = PerformTransactionEveryWeek(scheduled_transaction=new_scheduled_transaction, scheduled_dates=scheduled_dates)
    # start perform transaction every week
    advance_transacrion_thread.start()
    return JsonResponse({"Done":"transactions scheduled"})
