# Create your tasks here
# THIS IS ONLY A DEMO, CHANGE THIS

# tasks.py

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def my_task(arg1, arg2):
    # Task logic here
    result = arg1 + arg2
    return result

@shared_task(bind=True)
def send_task_email_to_assignee(self, assignee_email, task_title):
    mail_subject="Hi from celery"
    message="Yaaaa....I have completed this task by celery!!"
    send_mail(
        subject= mail_subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[assignee_email],
    )
    return "Done"