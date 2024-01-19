from rest_framework import generics
from .models import User, Expense,Passbook
from .serializers import UserSerializer, LoginSerializer,ExpenseSerializer,PassbookSerializer,ExpenseAdditionalSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import models
from .tasks import send_expense_notification_email


class RegistrationView(APIView):
    # Allow any user, whether authenticated or not, to access this view
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UserLoginView(APIView):
    # Allow any user, whether authenticated or not, to access this view
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                email = serializer.validated_data['email']
                password = serializer.validated_data['password']
                user = authenticate(email=email, password=password)
                if user:
                    # Generate JWT tokens for the authenticated user
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    return Response({'refresh_token':str(refresh),'access_token': access_token}, status=status.HTTP_200_OK)
                return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': e}, status=status.HTTP_400_BAD_REQUEST)


class ExpenseCreate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated] 
    def post(self, request, *args, **kwargs):
        """
        Create an expense and send notification email.
        """
        try:
            data = request.data
            data['payer_id']= request.user.id
            if data['expense_type']=="EQUAL":
                serializer = ExpenseAdditionalSerializer(data=data)
            elif data['expense_type']=="EXACT":
                participants_data=data['participants']
                data['participants']=[item['id'] for item in participants_data]
                serializer = ExpenseAdditionalSerializer(data=data,context={"participants_data":participants_data})
            elif data['expense_type']=="PERCENT":
                participants_percent_data=data['participants']
                data['participants']=[item['id'] for item in participants_percent_data]
                serializer = ExpenseAdditionalSerializer(data=data,context={"participants_percent_data":participants_percent_data})

            if serializer.is_valid():
                created_data=serializer.save()
                amount_owed = created_data['amount'] 
                user=User.objects.get(id=created_data['payer_id'])
                # Send email asynchronously using a task
                send_expense_notification_email.delay(created_data['id'], str(user), amount_owed)
                
                return Response({"message":"Data saved successfully.","data":created_data},status=status.HTTP_201_CREATED)
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status":500,"message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserExpenseView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        user_id = request.user.id
        expenses=Expense.get_user_expense_details(user_id)
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BalanceView(APIView):
    def get(self, request):
        users = User.objects.all()
        balances = []
        
        for user in users:
            balance = {
                'user_id': user.id,
                'user_name': user.username  ,
                'balance': self.calculate_balance(user)
            }
            balances.append(balance)

        return Response(balances, status=status.HTTP_200_OK)

    def calculate_balance(self, user):
        credits = Passbook.objects.filter(creditor_id=user).aggregate(total_credits=models.Sum('amount'))['total_credits'] or 0
        debts = Passbook.objects.filter(debtor_id=user).aggregate(total_debts=models.Sum('amount'))['total_debts'] or 0
        return credits - debts


class BalanceDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        """
        Get user balance details, including credits and debts.

        Returns:
            Response: Serialized data including user information, balance, credits, and debts.
        """
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        debts = Passbook.objects.filter(debtor_id=user)
        credits = Passbook.objects.filter(creditor_id=user)

        debts_serializer = PassbookSerializer(debts, many=True)
        credits_serializer = PassbookSerializer(credits, many=True)
        credits_total_amount,debts_total_amount=self.calculate_balance(user)
        response_data = {
            'user_id': user.id,
            'user_name': user.username,
            'balance':credits_total_amount-debts_total_amount,
            'credits_amount':credits_total_amount,
            'debts_total_amount':debts_total_amount,
            'debts': debts_serializer.data,
            'credits': credits_serializer.data,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def calculate_balance(self, user):
        """
        Calculate the total credits and debts for a user.
        """
        credits = Passbook.objects.filter(creditor_id=user).aggregate(total_credits=models.Sum('amount'))['total_credits'] or 0
        debts = Passbook.objects.filter(debtor_id=user).aggregate(total_debts=models.Sum('amount'))['total_debts'] or 0
        return credits,debts
    
