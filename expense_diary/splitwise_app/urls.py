from django.urls import path
from .views import BalanceDetailView,UserExpenseView,BalanceView,ExpenseCreate,RegistrationView,UserLoginView


urlpatterns = [
    path('user-register/', RegistrationView.as_view(), name='user-register'),
    path('user-login/', UserLoginView.as_view(), name='user-login'),

    path('expenses-create/', ExpenseCreate.as_view(), name='expense-create'),
    path('user-expenses/', UserExpenseView.as_view(), name='user-expenses'),
    
    path('balances/', BalanceView.as_view(), name='balances'),
    path('balances-by-user/', BalanceDetailView.as_view(), name='balances-by-user'),
   
]

