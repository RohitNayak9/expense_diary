from django.db import models,transaction
from django.contrib.auth.models import AbstractBaseUser,Group,Permission
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import BaseUserManager

class UserProfileManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        """
        Create and return a regular user with an email, username, and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        # Normalize the email (convert to lowercase for consistency)
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        """
        Create and return a superuser with an email, username, and password.
        """
        # Set default values for superuser-specific fields
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)
    

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with email as the unique identifier.
    """
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Custom manager for the user model
    objects = UserProfileManager() 

    # Specify the field to be used as the unique identifier (email)
    USERNAME_FIELD = 'email'

    # Additional fields required when creating a user via createsuperuser
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    

class Expense(models.Model):
    EXPENSE_TYPES = (
        ('EQUAL', 'Equal'),
        ('EXACT', 'Exact'),
        ('PERCENT', 'Percent'),
    )
    expense_name = models.CharField(max_length=255)
    payer_id=models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    expense_type = models.CharField(max_length=10, choices=EXPENSE_TYPES)
    participants = models.ManyToManyField(User, related_name='expenses')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"id: {self.id} ,expense_name {self.expense_name}"
    

    def get_user_expense_details(user_id):
        user = User.objects.get(pk=user_id)
        expenses = Expense.objects.filter(payer_id=user)
        return expenses


class Passbook(models.Model):
    expense_id=models.ForeignKey(Expense, on_delete=models.CASCADE,related_name='expense')
    creditor_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creditor')
    debtor_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='debtor')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    


