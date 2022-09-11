from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist

import asyncio

from .models import BankAccount, Transaction
from .celery import pay_once_aweek

from threading import Thread

from datetime import date, timedelta

# Create your views here.
@api_view(["POST"])
def perform_transaction(request, src_bank_account:int, dst_bank_account:int, amount:int, direction:str):
    return JsonResponse({"transaction_id": "Transaction.id"})

@api_view(["GET"])
def download_report(request):
    return JsonResponse({"Transaction.id": "success/fail"})

@api_view(["POST"])
def perform_advance(request):
    dst_bank_account = request.data["dst_bank_account"]
    amount = request.data["amount"]
    try:
        dst_bank_account_obj = BankAccount.objects.get(account_number=dst_bank_account)
        src_bank_account_obj = BankAccount.objects.get(account_number="000000") # TODO: check what the source should be
    except ObjectDoesNotExist as ex:
        return JsonResponse({"404": "At least one of the bank account does not exists."})

    # make the credit (amount)
    credit_customer = Transaction(src_bank_account=src_bank_account_obj, dst_bank_account=dst_bank_account_obj, amount=amount, direction="credit")
    credit_customer.save()
    # perform_transaction(request, src_bank_account=credit_customer.src_bank_account, dst_bank_account=credit_customer.dst_bank_account, amount=credit_customer.amount, direction=credit_customer.direction)
       
    # create 12 transactions of debits (amount / 12)
    one_pay = amount / 12
    advance_transactions = []
    today = date.today()
    for i in range(12):
        schedule = today + timedelta(weeks=i+1)
        new_transaction = Transaction(src_bank_account=dst_bank_account_obj, dst_bank_account=src_bank_account_obj, amount=one_pay, direction="debit", schedule=schedule)
        new_transaction.save()
        new_transaction = Transaction.objects.get(id=new_transaction.id)
        advance_transactions.append(new_transaction)
    advance_thread = Thread(target=pay_once_aweek, args=(advance_transactions,))
    advance_thread.start()
    return JsonResponse({"Done":"transactions scheduled"})
