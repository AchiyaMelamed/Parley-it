from rest_framework.decorators import api_view, permission_classes, authentication_classes  
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

from .serializers import UserSerializer, RegisterSerializer
from .models import BankAccount, Transaction
from .utils import perform_transaction_and_check_result, create_scheduled_transaction_object_and_dates
from .threads import PerformTransactionEveryWeek

import asyncio
import datetime
import random


# Create your views here.


########## Processor ##########
@api_view(["POST"])
def perform_transaction(request):
    """FAKE function for modeling the perform_advance request.
        This call creates a new Transaction with randomised result (75%- success, 25%- fail) and returns the transaction_id.
    """
    src_bank_account = request.data["src_bank_account"]
    dst_bank_account = request.data["dst_bank_account"]
    amount = request.data["amount"]
    direction = request.data["direction"]
    result = random.choice(["success", "success", "success", "fail"])
    
    new_transaction = Transaction.objects.create(src_bank_account=BankAccount.objects.get(account_number=src_bank_account), dst_bank_account=BankAccount.objects.get(account_number=dst_bank_account), amount=amount, direction=direction, result=result)
    return Response({"transaction_id": new_transaction.id})

@api_view(["GET"])
def download_report(request):
    """FAKE function for modeling the perform_advance request.
        This call get all the Transactions of the last 5 days and returns a report with a result of each one.
    """
    today = datetime.date.today()
    five_days_transactions = Transaction.objects.filter(date__gte=today - datetime.timedelta(days=5))
    ids = [t.id for t in five_days_transactions]
    results = [t.result for t in five_days_transactions]
    
    return Response({"report":[{"transaction_id": id, "result": result} for (id, result) in zip(ids, results)]})
########## End Processor ##########




########## Perform Advance Request ##########
@api_view(["POST"])
def perform_advance(request):
    # get the data of the request
    try:
        dst_bank_account = request.data["dst_bank_account"]
        amount = request.data["amount"]
        token = request.headers["Authorization"]
    except KeyError as ex:
        return Response({"400": "Please post dst_bank_account and an amount"})
    
    
    # check if there is such BankAccount and get it
    try:
        customer_bank_account_obj = BankAccount.objects.get(account_number=dst_bank_account)
    except ObjectDoesNotExist as ex:
        return Response({"400": "Bank Account dosn't exists."})

    # just admin or the customer itself can do this request
    if customer_bank_account_obj.user.id != request.user.id and not request.user.is_superuser:
        return Response({"401": "You are not allowed to do this request."})
    
    
    # get the super user to perform advance
    try:
        manager_bank_account_obj = BankAccount.objects.get(user__is_superuser=True)
    except ObjectDoesNotExist as ex:
        return Response({"500": "Manager Account dosn't exists."})

    # perfom the credit transaction and check if succeed
    transaction_id, success = perform_transaction_and_check_result(src_bank_account_obj=manager_bank_account_obj,
                                                                   dst_bank_account_obj=customer_bank_account_obj,
                                                                   amount=amount,
                                                                   direction="credit",
                                                                   token=token)
    if not success:
        return Response({"500": f"There was a problem while performing the transaction ({transaction_id}), please try again."})
    
       
    # get the scheduled transaction and its scheduled dates
    new_scheduled_transaction_obj, scheduled_dates = create_scheduled_transaction_object_and_dates(src_bank_account_obj=customer_bank_account_obj,
                                                                                   dst_bank_account_obj=manager_bank_account_obj,
                                                                                   credit_transaction_id=transaction_id,
                                                                                   amount=amount,
                                                                                   direction="debit")
    # create the thread object to run every week
    advance_transacrion_thread = PerformTransactionEveryWeek(scheduled_transaction=new_scheduled_transaction_obj,
                                                             scheduled_dates=scheduled_dates)
    # start perform transaction every week
    advance_transacrion_thread.start()
    
    return Response({"Done": f"transaction scheduled, id: {new_scheduled_transaction_obj.id}, scheduled for: {scheduled_dates}"})
########## End Perform Advance Request ##########




########## Users Request ##########
@api_view(["GET"])
@authentication_classes([TokenAuthentication,])
@permission_classes([IsAuthenticated])
def get_user_details(request, *args, **kwargs):
    user = User.objects.get(id=request.user.id)
    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(["POST"])
@permission_classes([AllowAny,])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(True)
    user_serializer = UserSerializer(data=request.data)
    if user_serializer.is_valid(raise_exception=True):
        user = user_serializer.save()
        token, created = Token.objects.get_or_create(user=user)
    
        bank_account = BankAccount(user=user)
        bank_account.save()

        return Response({"username": user.username, "account_number": bank_account.account_number, "token": token.key})
    else:
       return Response(user_serializer.errors) 
########## End Users Request ##########
