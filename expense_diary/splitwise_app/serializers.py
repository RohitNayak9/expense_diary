from rest_framework import serializers
from .models import User, Expense, Passbook
from django.db import transaction


class UserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id', read_only=True)
    class Meta:
        model = User
        fields = ['user_id', 'email', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})



class PassbookSerializer(serializers.ModelSerializer):
    passbook_id = serializers.IntegerField(source='id', read_only=True)
    creditor_id = UserSerializer()
    debtor_id = UserSerializer()
    class Meta:
        model = Passbook
        fields = ['passbook_id','expense_id','creditor_id','debtor_id','amount']
        

class ExpenseSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True)
    class Meta:
        model = Expense
        fields = ['id','expense_name','payer_id','amount','expense_type','participants']
    
class ExpenseAdditionalSerializer(serializers.ModelSerializer):
    participants = serializers.ListField(child=serializers.IntegerField(), required=False)
    class Meta:
        model = Expense
        fields = ['id', 'expense_name', 'payer_id', 'amount', 'expense_type', 'participants']

    def create(self, validated_data):
        participant_ids = validated_data.pop('participants', [])
        instance = super().create(validated_data)
        instance.participants.set(participant_ids)
        expense_type = validated_data['expense_type']

        if expense_type == 'EQUAL':
            # Create Passbook entries using map and bulk_create
            passbook_entries = list(map(lambda participant_id: Passbook(
                expense_id=instance,
                creditor_id=instance.payer_id,
                debtor_id=User.objects.get(id=participant_id),
                amount=instance.amount / len(participant_ids)
            ), participant_ids))

            

        elif expense_type == 'EXACT':
            # Additional data to be passed to the serializer
            participants_data = self.context.get('participants_data', {})
            total_amount_specified=sum(item['specific_amounts'] for item in participants_data)
            if total_amount_specified != instance.amount:
                    raise serializers.ValidationError("The sum of specified amounts must equal the total amount.")
            passbook_entries = list(map(lambda participant_id: Passbook(
                expense_id=instance,
                creditor_id=instance.payer_id,
                debtor_id=User.objects.get(id=participant_id['id']),
                amount=participant_id['specific_amounts']
            ), participants_data))
        
        elif expense_type == 'PERCENT':
            # Additional data to be passed to the serializer
            participants_percent_data = self.context.get('participants_percent_data', {})
            passbook_entries = list(map(lambda participant: Passbook(
                expense_id=instance,
                creditor_id=instance.payer_id,
                debtor_id=User.objects.get(id=participant['id']),
                amount=round(instance.amount * participant['percentage']/100,2)
            ), participants_percent_data))

        with transaction.atomic():
            Passbook.objects.bulk_create(passbook_entries)

        serializer = ExpenseSerializer(instance)
        return serializer.data

