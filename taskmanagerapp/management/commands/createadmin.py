from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a default admin user'

    def handle(self, *args, **kwargs):
        username = 'admin'
        email = 'violalaurastumpf@gmail.com'
        password = 'adminpw12'

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS('Successfully created admin user'))
        else:
            self.stdout.write(self.style.WARNING('Admin user already exists'))


user = User.objects.get(username='bb')
user.is_superuser = True
user.is_staff = True
user.save()
