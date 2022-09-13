from rest_framework import serializers
from .models import BankAccount, Transaction

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ["id", "username", "account_number", "password"]
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        bank_account = BankAccount(
            username=validated_data['username'],
        )
        bank_account.set_password(validated_data['password'])
        bank_account.save()
        return bank_account


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ('id', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        bank_account = BankAccount.objects.create(username=validated_data['username'], password=validated_data['password'])

        return bank_account

class LoginSerializer(serializers.Serializer):
   username = serializers.CharField()
   password = serializers.CharField()

   def validate(self, data):
      user = authenticate(**data)
      if user and user.is_active:
         return user
      raise serializers.ValidationError("Incorrect Credentials")