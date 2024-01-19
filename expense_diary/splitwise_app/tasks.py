from celery import shared_task
from time import sleep
from django.core.mail import send_mail
from django.template.loader import render_to_string
from splitwise_app.models import Passbook,User  
from django.db import models

@shared_task
def send_expense_notification_email(expense_id, participant_email, amount_owed):
    subject = 'You have been added to a new expense'
    message = render_to_string('expense_notification_email.txt', {
        'amount_owed': amount_owed,
    })
    from_email = 'your@gmail.com'
    recipient_list = [participant_email]
    send_mail(subject, message, from_email, recipient_list)


@shared_task
def send_weekly_summary_email():
    # Logic to calculate total amount owed per user
    users = User.objects.all()

    summary_data = {}
    for user in users:
        # Calculate the total amount owed for each user
        total_amount_owed = Passbook.objects.filter(debtor_id=user).aggregate(total_amount_owed=models.Sum('amount'))['total_amount_owed'] or 0
        summary_data[user.email] = total_amount_owed

    # Send emails to users with the summary
    for email, total_amount_owed in summary_data.items():
        send_summary_email(email, total_amount_owed)

def send_summary_email(recipient_email, total_amount_owed):
    subject = 'Weekly Expense Summary'
    message = render_to_string('weekly_summary_email.txt', {
        'total_amount_owed': total_amount_owed,
    })
    from_email = 'your@gmail.com'
    recipient_list = [recipient_email]
    
    send_mail(subject, message, from_email, recipient_list)