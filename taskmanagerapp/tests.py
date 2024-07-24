from django.test import TestCase, Client
from taskmanagerapp.models import Task
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import datetime
from taskmanagerapp.forms import SignupForm, LoginForm
from django.contrib.auth import authenticate
import json
from unittest.mock import patch
from taskmanagerapp.tasks import (
    send_task_email_to_assignee_created,
    send_task_email_to_assignee_updated,
    notify_superusers_of_task_updated,
    warn_users_one_day_before_deadline
)
from django.conf import settings


class TaskModelTest (TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='bb',
            email='testb@test.com',
            password='12345678'
        )
        self.superuser = User.objects.create_superuser(
            username='aa',
            email='testa@test.com',
            password='12345678'
        )
        self.task_model = Task.objects.create(
            title="Unit Test 1",
            description="This is the first unit test",
            status="To Do",
            assignee=self.user,
            startDate="2024-07-22T00:00:00Z",
            deadline="2024-07-23T00:00:00Z",
            priority="High"
        )

    def testModelCreation(self):
        self.assertEqual(self.task_model.title, 'Unit Test 1')
        self.assertEqual(self.task_model.description, 'This is the first unit test')
        self.assertEqual(self.task_model.status, 'To Do')
        self.assertEqual(self.task_model.assignee, self.user)
        self.assertEqual(self.task_model.startDate, '2024-07-22T00:00:00Z')
        self.assertEqual(self.task_model.deadline, '2024-07-23T00:00:00Z')
        self.assertEqual(self.task_model.priority, 'High')


class TaskViewTest (TestCase):

    def setUp(self):
        # Setup run before every test method.
        self.client = Client()
        self.user = User.objects.create_user(
            username='bb',
            password='12345678'
        )

        self.user_with_id_5 = User.objects.create_user(
            username='user5',
            password='12345678',
            email='user5@example.com',
            id=5
        )

        self.superuser = User.objects.create_superuser(
            username='aa',
            password='12345678'
        )
        self.task_model = Task.objects.create(
            title="Unit Test 1",
            description="This is the first unit test",
            status="To Do",
            assignee=self.user,
            startDate="2024-07-22T00:00:00Z",
            deadline="2024-07-23T00:00:00Z",
            priority="High"
        )
        self.task_model_2 = Task.objects.create(
            title="Unit Test 2",
            description="This is the second unit test",
            status="To Do",
            assignee=self.superuser,
            startDate="2024-07-23T00:00:00Z",
            deadline="2024-07-24T00:00:00Z",
            priority="Medium"
        )
        self.login = self.client.post(
            reverse('login'),
            {'username': 'bb', 'password': '12345678'}
        )
        pass

    def tearDown(self):
        # Clean up run after every test method.
        pass

    def test_view_status_code(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        print('test login')
        response = self.client.post(
            reverse('login'),
            {'username': 'bb', 'password': '12345678'}
        )
        self.assertEqual(response.status_code, 302)

        # Follow the redirect
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_signup(self):
        print('test signup')
        response = self.client.post(reverse('signup'), {
            'username': 'bb',
            'password1': '12345678',
            'password2': '12345678'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='bb').exists())

    def test_get_tasks(self):
        print('test get tasks')
        self.client.login(username='bb', password='12345678')
        response = self.client.get(reverse('tasklist'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            '<tr>',
            html=True,
            msg_prefix="Expected the task list to be empty but found tasks."
        )

    def test_update_task(self):
        print('test update task')

        # Log in as superuser
        self.client.login(username='aa', password='12345678')

        # Timezone-aware initial datetime
        start_date_aware = timezone.make_aware(datetime(2024, 7, 22, 0, 0, 0))
        deadline_aware = timezone.make_aware(datetime(2024, 7, 23, 0, 0, 0))

        initial_task_data = {
            'title': 'Initial Title',
            'description': 'Initial description',
            'status': 'To Do',
            'assignee': self.user_with_id_5.id,
            'startDate': start_date_aware.isoformat(),
            'deadline': deadline_aware.isoformat(),
            'priority': 'High'
        }

        response = self.client.post(
            f'{settings.BASE_URL}/api/tasks/',
            data=json.dumps(initial_task_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(self.superuser).access_token)}'
        )
        self.assertEqual(response.status_code, 201)
        task_id = response.json()['id']

        # Updated data with the same timezone-aware datetime values
        updated_start_date_aware = timezone.make_aware(datetime(2024, 7, 22, 0, 0, 0))
        updated_deadline_aware = timezone.make_aware(datetime(2024, 7, 23, 0, 0, 0))

        updated_task_data = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'status': 'In Progress',
            'assignee': self.user.id,
            'startDate': updated_start_date_aware.isoformat(),
            'deadline': updated_deadline_aware.isoformat(),
            'priority': 'Medium'
        }

        # Perform the update
        response = self.client.put(
            f'{settings.BASE_URL}/api/tasks/{task_id}/',
            data=json.dumps(updated_task_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {str(RefreshToken.for_user(self.superuser).access_token)}'
        )

        self.assertEqual(response.status_code, 200)

        task = Task.objects.get(id=task_id)
        self.assertEqual(task.title, 'Updated Title')
        self.assertEqual(task.description, 'Updated description')
        self.assertEqual(task.status, 'In Progress')
        self.assertEqual(task.assignee, self.user)
        self.assertEqual(task.startDate, updated_start_date_aware)
        self.assertEqual(task.deadline, updated_deadline_aware)
        self.assertEqual(task.priority, 'Medium')

    def test_update_status(self):
        print('test update status')

        # Log in as normal user
        self.client.login(username='bb', password='12345678')

        # Retrieve the task with the title "Unit Test 1" assigned to the user 'bb'
        task = Task.objects.get(title="Unit Test 1", assignee=self.user)
        task_id = task.id

        updated_status = 'In Progress'

        updated_status_task_data = {
            'title': task.title,
            'description': task.description,
            'status': updated_status,
            'assignee': task.assignee.id,
            'startDate': task.startDate.isoformat(),
            'deadline': task.deadline.isoformat(),
            'priority': task.priority
        }

        # Generate JWT token for the user 'bb'
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)

        # Perform the update
        response = self.client.patch(
            f'{settings.BASE_URL}/api/tasks/{task_id}/',
            data=json.dumps(updated_status_task_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )

        self.assertEqual(response.status_code, 200)

        updated_task = Task.objects.get(id=task_id)
        self.assertEqual(updated_task.status, updated_status)

    def test_delete_task(self):
        print('test delete task')

        # Log in as superuser
        self.client.login(username='aa', password='12345678')

        task = Task.objects.get(
            title="Unit Test 1",
            assignee=self.user
        )
        task_id = task.id

        # Generate JWT token for the user 'bb'
        refresh = RefreshToken.for_user(self.superuser)
        access_token = str(refresh.access_token)

        response = self.client.delete(
            f'{settings.BASE_URL}/api/tasks/{task_id}/',
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )

        self.assertEqual(response.status_code, 204)

        with self.assertRaises(Task.DoesNotExist):
            Task.objects.get(id=task_id)

    def test_admin_view(self):
        print('test admin view')

        # Log in as superuser
        self.client.login(username='aa', password='12345678')

        # Generate JWT token for the superuser
        refresh = RefreshToken.for_user(self.superuser)
        access_token = str(refresh.access_token)

        response = self.client.get(
            f'{settings.BASE_URL}/api/tasks/',
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )

        self.assertEqual(response.status_code, 200)

        response_content = response.json()
        task_user_id = [task['id'] for task in response_content if task['assignee'] == self.user.id]
        task_superuser_id = [task['id'] for task in response_content if task['assignee'] == self.superuser.id]

        self.assertIn(self.task_model.id, task_user_id)
        self.assertIn(self.task_model_2.id, task_superuser_id)


# Write tests for Forms
class SignupFormTest(TestCase):

    def test_signup_form_valid(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'defaultpassword123',
            'password2': 'defaultpassword123',
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_signup_form_invalid(self):
        # Test with missing email
        form_data = {
            'username': 'newuser',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
        }
        form = SignupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

        # Test with non-matching passwords
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'differentpassword123',
        }
        form = SignupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_signup_form_save(self):
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(user.check_password('complexpassword123'))


class LoginFormTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='existinguser',
            password='12345678'
        )

    def test_login_form_valid(self):
        form_data = {
            'username': 'existinguser',
            'password': '12345678',
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_login_form_invalid(self):
        # Test with incorrect password
        form_data = {
            'username': 'existinguser',
            'password': 'wrongpassword',
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        self.assertIsNone(user)

        # Test with missing username
        form_data = {
            'password': '12345678',
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

        # Test with missing password
        form_data = {
            'username': 'existinguser',
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

# Write tests for Celery tasks


class CeleryTasksTest(TestCase):

    def setUp(self):
        self.assignee_email = 'test@example.com'
        self.assignee_name = 'Test User'
        self.task_title = 'Test Task'
        self.task_startdate = '2024-07-23T00:00:00Z'
        self.task_deadline = '2024-07-24T00:00:00Z'
        self.task_assignee = 'Test User'

    @patch('taskmanagerapp.tasks.send_mail')
    def test_send_task_email_to_assignee_created(self, mock_send_mail):
        # Call the task
        result = send_task_email_to_assignee_created(
            assignee_email=self.assignee_email,
            assignee_name=self.assignee_name,
            task_title=self.task_title,
            task_startdate=self.task_startdate,
            task_deadline=self.task_deadline
        )
        # Check if send_mail was called with correct parameters
        mock_send_mail.assert_called_once_with(
            subject=f'Task {self.task_title} has been created',
            message=(
                f'Hello {self.assignee_name}! \n\n'
                f'The task with the title {self.task_title} has been created. It starts on the date {self.task_startdate} and the deadline is on the {self.task_deadline}. \n\n'
                f'For further questions, please refer to the URL: http://localhost:8000/tasklist/'
            ),
            from_email='Celery <violalaurastumpf@gmail.com>',
            recipient_list=[self.assignee_email],
        )
        self.assertEqual(result, "Done")

    @patch('taskmanagerapp.tasks.send_mail')
    def test_send_task_email_to_assignee_updated(self, mock_send_mail):
        # Call the task
        result = send_task_email_to_assignee_updated(
            assignee_email=self.assignee_email,
            assignee_name=self.assignee_name,
            task_title=self.task_title
        )
        # Check if send_mail was called with correct parameters
        mock_send_mail.assert_called_once_with(
            subject=f'Task {self.task_title} has been updated',
            message=(
                f'Hello {self.assignee_name}! \n\n'
                f'The task with the title {self.task_title} has been updated. \n\n'
                f'For further questions, please refer to the URL: http://localhost:8000/tasklist/'
            ),
            from_email='Celery <violalaurastumpf@gmail.com>',
            recipient_list=[self.assignee_email],
        )
        self.assertEqual(result, "Done")

    @patch('taskmanagerapp.tasks.send_mail')
    @patch('taskmanagerapp.tasks.get_user_model')
    def test_notify_superusers_of_task_updated(self, mock_get_user_model, mock_send_mail):
        # Mock the superusers
        mock_get_user_model.return_value.objects.filter.return_value = [
            User(email='superuser@example.com'),
            User(email='another_superuser@example.com'),
        ]
        # Call the task
        result = notify_superusers_of_task_updated(
            task_title=self.task_title,
            task_assignee=self.task_assignee
        )
        # Check if send_mail was called with correct parameters
        mock_send_mail.assert_called_once_with(
            subject=f'Status of Task {self.task_title} has been updated by {self.task_assignee}',
            message=(
                f'Hello Superuser! \n\n'
                f'The task status with the title {self.task_title} has been updated by {self.task_assignee}. \n\n'
                f'To have a look at every available task, please refer to the URL: http://localhost:8000/tasklist/admin/'
            ),
            from_email='Celery <violalaurastumpf@gmail.com>',
            recipient_list=[
                'superuser@example.com',
                'another_superuser@example.com'
            ],
        )
        self.assertEqual(result, "Done")

    @patch('taskmanagerapp.tasks.send_mail')
    def test_warn_users_one_day_before_deadline(self, mock_send_mail):
        # Call the task
        result = warn_users_one_day_before_deadline(
            assignee_email=self.assignee_email,
            assignee_name=self.assignee_name,
            task_title=self.task_title,
            task_deadline=self.task_deadline
        )
        # Check if send_mail was called with correct parameters
        mock_send_mail.assert_called_once_with(
            subject=f'Deadline of Task {self.task_title} is approaching',
            message=(
                f'Hello {self.assignee_name}! \n\n'
                f'The Deadline of the task with the title {self.task_title} is set to be due in 24 hours ({self.task_deadline}). Please make sure to finish the task or console with your team leader. \n\n'
                f'For further questions, please refer to the URL: http://localhost:8000/tasklist/'
            ),
            from_email='Celery <violalaurastumpf@gmail.com>',
            recipient_list=[self.assignee_email],
        )
        self.assertEqual(result, "Done")
