# tasks.py

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

@shared_task(bind=True)
def send_task_email_to_assignee_created(self, assignee_email, assignee_name, task_title, task_startdate, task_deadline):

    tasklist_url = settings.DOMAIN_NAME + reverse('tasklist')

    mail_subject=f'Task {task_title} has been created'
    message=(
        f'Hello {assignee_name}! \n\n'
        f'The task with the title {task_title} has been created. It starts on the date {task_startdate} and the deadline is on the {task_deadline}. \n\n'
        f'For further questions, please refer to the URL: {tasklist_url}'
    )
    send_mail(
        subject= mail_subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[assignee_email],
    )
    return "Done"

@shared_task(bind=True)
def send_task_email_to_assignee_updated(self, assignee_email, assignee_name, task_title):

    tasklist_url = settings.DOMAIN_NAME + reverse('tasklist')

    mail_subject=f'Task {task_title} has been updated'
    message= (
        f'Hello {assignee_name}! \n\n' 
        f'The task with the title {task_title} has been updated. \n\n'
        f'For further questions, please refer to the URL: {tasklist_url}'
    )
    send_mail(
        subject= mail_subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[assignee_email],
    )
    return "Done"

@shared_task(bind=True)
def notify_superusers_of_task_updated (self, task_title, task_assignee):

    superusers = get_user_model().objects.filter(is_superuser=True)
    superuser_emails = [user.email for user in superusers if user.email]

    tasklist_admin_url = settings.DOMAIN_NAME + reverse('admin-tasklist')

    mail_subject=f'Status of Task {task_title} has been updated by {task_assignee}'
    message= (
        f'Hello Superuser! \n\n' 
        f'The task status with the title {task_title} has been updated by {task_assignee}. \n\n'
        f'To have a look at every available task, please refer to the URL: {tasklist_admin_url}'
    )
    send_mail(
        subject= mail_subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=superuser_emails,
    )
    return "Done"

@shared_task(bind=True)
def warn_users_one_day_before_deadline (self, assignee_email, assignee_name, task_title, task_deadline):

    tasklist_url = settings.DOMAIN_NAME + reverse('tasklist')

    mail_subject=f'Deadline of Task {task_title} is approaching'
    message= (
        f'Hello {assignee_name}! \n\n' 
        f'The Deadline of the task with the title {task_title} is set to be due in 24 hours ({task_deadline}). Please make sure to finish the task or console with your team leader. \n\n'
        f'For further questions, please refer to the URL: {tasklist_url}'
    )
    send_mail(
        subject= mail_subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[assignee_email],
    )
    return "Done"