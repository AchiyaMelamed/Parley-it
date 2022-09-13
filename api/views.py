from rest_framework import generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.serializers import AuthTokenSerializer

from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from .serializers import BankAccountSerializer, RegisterSerializer, LoginSerializer

from django.contrib.auth import login
from django.core.exceptions import ObjectDoesNotExist

from .models import BankAccount, Transaction
from .utils import perform_transaction_and_check_result, create_scheduled_transaction_object_and_dates
from .threads import PerformTransactionEveryWeek

import asyncio
import datetime
import random


# Create your views here.
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



@api_view(["POST"])
def perform_advance(request):
    # get the data of the request
    try:
        dst_bank_account = request.data["dst_bank_account"]
        amount = request.data["amount"]
    except KeyError as ex:
        return Response({"400": "Please post dst_bank_account and an amount"})
    
    # check if there is such BankAccount and get it
    try:
        customer_bank_account_obj = BankAccount.objects.get(account_number=dst_bank_account)
    except ObjectDoesNotExist as ex:
        return Response({"400": "Bank Account dosn't exists."})
    
    
    # get the super user to perform advance
    try:
        manager_bank_account_obj = BankAccount.objects.get(is_superuser=True)
    except ObjectDoesNotExist as ex:
        return Response({"500": "Manager Account dosn't exists."})

    # perfom the credit transaction and check if succeed
    transaction_id, success = perform_transaction_and_check_result(src_bank_account_obj=manager_bank_account_obj,
                                                                   dst_bank_account_obj=customer_bank_account_obj,
                                                                   amount=amount,
                                                                   direction="credit")
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


# Register and Login API - TODO: fix or delete ( setting the password without hash :( )
class RegisterAPI(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
        "user": BankAccountSerializer(user, context=self.get_serializer_context()).data,
        "token": AuthToken.objects.create(user)[1]
        })

class LoginAPI(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return super(LoginAPI, self).post(request, format=None)