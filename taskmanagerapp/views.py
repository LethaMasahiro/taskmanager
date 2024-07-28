from datetime import datetime, timedelta
import pytz
import requests
from dateutil.parser import isoparse

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import now, localtime
from django.conf import settings

from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import SignupForm, LoginForm
from .models import Task
from .tasks import send_task_email_to_assignee_created, send_task_email_to_assignee_updated, notify_superusers_of_task_updated, warn_users_one_day_before_deadline
from .serializers import TaskSerializer


# Helper Functions
def get_auth_headers(user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    return {'Authorization': f'Bearer {access_token}'}


def check_superuser(user):
    if not user.is_superuser:
        raise PermissionError('Permission denied.')

    
def convert_to_utc_aware_datetime(date_str):
    try:
        # Parse the date string into a naive datetime object
        naive_datetime = datetime.fromisoformat(date_str)

        # Localize the naive datetime to the Korean timezone
        korean_timezone = pytz.timezone('Asia/Seoul')
        korean_aware_datetime = korean_timezone.localize(naive_datetime)

        # Convert the localized datetime to UTC
        utc_aware_datetime = korean_aware_datetime.astimezone(pytz.UTC)

        # Format the datetime to the required format
        utc_aware_datetime_str = utc_aware_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

        return utc_aware_datetime_str
    except ValueError:
        raise ValueError("Invalid date format: Ensure it is ISO format.")


def handle_api_response(response, success_redirect, error_template, request, data=None):
    try:
        response_data = response.json()
    except ValueError:
        response_data = {"error": "Failed to decode response as JSON."}
        response_status = 500
    else:
        response_status = response.status_code

    if response_status in [200, 201, 204]:
        return redirect(success_redirect)
    else:
        print(f"Error: {response_status} - {response.text}")
        if data:
            print(f"Sent Data: {data}")
        return render(request, error_template, {'error': response_data})


def notify_assignee_email(task, start_date_aware, deadline_aware, is_update=False):
    if is_update:
        send_task_email_to_assignee_updated.delay(
            task.assignee.email,
            task.assignee.username,
            task.title
        )
    else:
        send_task_email_to_assignee_created.delay(
            task.assignee.email,
            task.assignee.username,
            task.title,
            start_date_aware,
            deadline_aware
        )


def schedule_warning_email(deadline_aware, assignee_email, assignee_username, task_title):
    notify_time = deadline_aware - timedelta(days=1)
    if notify_time > timezone.now():
        warn_users_one_day_before_deadline.apply_async(
            (
                assignee_email,
                assignee_username,
                task_title,
                deadline_aware
            ),
            eta=notify_time
        )
    else:
        print("Deadline is too soon to schedule a warning email.")


# Decorators
def admin_required(view_func):
    return user_passes_test(lambda user: user.is_superuser)(view_func)


def is_admin(user):
    return user.is_superuser


# Views
def index(request):
    if not (request.user.is_superuser):
        return redirect('tasklist')
    return render(request, 'index.html')


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_superuser:
                    return redirect('home')
                return redirect('tasklist')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def user_signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
@admin_required
def admin_index(request):
    return render(request, 'index_admin.html')


@login_required
@admin_required
def admin_tasklist(request):
    # Generate JWT token for the user
    headers = get_auth_headers(request.user)
    current_time = now()

    response = requests.get(
        f'{settings.BASE_URL}/api/tasks/',
        headers=headers
    )

    if response.status_code == 200:
        tasks = response.json()
        for task in tasks:
            assignee_id = task['assignee']
            assignee = User.objects.get(id=assignee_id)
            task['assignee_name'] = assignee.username
        return render(
            request,
            'tasklist_admin.html',
            {'tasks': tasks, 'current_time': current_time}
        )
    else:
        return render(
            request,
            'tasklist.html',
            {'error': 'Failed to retrieve tasks'}
        )


# Convert Task.Status choices to a list of dictionaries
def get_status_choices():
    return [
        {
            'id': choice.value,
            'name': choice.label
        } for choice in Task.Status
    ]


@login_required
def user_tasklist(request):
    assignee_id = request.GET.get('assignee', request.user.id)

    headers = get_auth_headers(request.user)

    response = requests.get(
        f'{settings.BASE_URL}/api/tasks/?assignee={assignee_id}',
        headers=headers
    )

    if response.status_code == 200:
        tasks = response.json()
        status_choices = get_status_choices()
        current_time = now()
        return render(request, 'tasklist.html', {
            'tasks': tasks,
            'status_choices': status_choices,
            'current_time': current_time
        })
    else:
        return render(
            request,
            'tasklist.html',
            {'error': 'Failed to retrieve tasks'}
        )


@login_required
@admin_required
def task_create(request):
    if request.method == 'POST':
        # Convert datetime strings to timezone-aware datetime objects
        start_date_str = request.POST.get('startDate')
        end_date_str = request.POST.get('deadline')

        try:
            start_date = convert_to_utc_aware_datetime(start_date_str)
            end_date = convert_to_utc_aware_datetime(end_date_str)

        except ValueError:
            return render(
                request,
                'tasklist_create.html',
                {'error': 'Invalid date format'}
            )

        data = {
            'title': request.POST.get('title'),
            'description': request.POST.get('description'),
            'status': request.POST.get('status'),
            'assignee': request.POST.get('assignee'),
            'startDate': start_date,
            'deadline': end_date,
            'priority': request.POST.get('priority')
        }

        # Generate JWT token for the user
        headers = get_auth_headers(request.user)
        response = requests.post(
            f'{settings.BASE_URL}/api/tasks/',
            data=data,
            headers=headers
        )
        return handle_api_response(
            response,
            'admin-tasklist',
            'tasklist_create.html',
            request, data
        )

    else:
        users = User.objects.all()
        statuses = Task.Status.choices
        priorities = Task.Priority.choices
        return render(
            request,
            'tasklist_create.html',
            {
                'users': users,
                'statuses': statuses,
                'priorities': priorities
            }
        )


@login_required
@admin_required
def task_update(request, task_id):
    current_task = get_object_or_404(Task, pk=task_id)
    if request.method == 'POST':
        # Convert datetime strings to timezone-aware datetime objects
        start_date_str = request.POST.get('startDate')
        end_date_str = request.POST.get('deadline')

        data = {
            'title': request.POST.get('title'),
            'description': request.POST.get('description'),
            'status': request.POST.get('status'),
            'assignee': request.POST.get('assignee'),
            'startDate': start_date_str,
            'deadline': end_date_str,
            'priority': request.POST.get('priority')
        }

        # Filter out any fields that are empty or not present
        data = {k: v for k, v in data.items() if v}

        headers = get_auth_headers(request.user)

        if 'startDate' in data:
            data['startDate'] = convert_to_utc_aware_datetime(start_date_str)

        if 'deadline' in data:
            data['deadline'] = convert_to_utc_aware_datetime(end_date_str)

        response = requests.patch(
            f'{settings.BASE_URL}/api/tasks/{task_id}/',
            json=data,
            headers=headers
        )
        return handle_api_response(
            response,
            'admin-tasklist',
            'tasklist_update.html',
            request, data
        )

    else:
        users = User.objects.all()
        statuses = Task.Status.choices
        priorities = Task.Priority.choices
        korean_timezone = pytz.timezone('Asia/Seoul')
        current_task.startDate = localtime(current_task.startDate).astimezone(korean_timezone)
        current_task.deadline = localtime(current_task.deadline).astimezone(korean_timezone)

        # Format the datetimes as naive local datetime strings
        start_date_str = current_task.startDate.strftime('%Y-%m-%dT%H:%M')
        deadline_date_str = current_task.deadline.strftime('%Y-%m-%dT%H:%M')
        return render(
            request,
            'tasklist_update.html',
            {
                'users': users,
                'statuses': statuses,
                'priorities': priorities,
                'task': current_task,
                'start_date_str': start_date_str,
                'deadline_date_str': deadline_date_str
            }
        )


@login_required
@admin_required
def task_delete(request, task_id):
    if request.method == 'POST':

        headers = get_auth_headers(request.user)

        response = requests.delete(
            f'{settings.BASE_URL}/api/tasks/{task_id}/',
            headers=headers
        )

        if response.status_code in [200, 204]:
            return redirect('admin-tasklist')
        else:
            try:
                error_message = response.json()
            except ValueError:
                error_message = {'error': 'Failed to delete task.'}

            return render(
                request,
                'tasklist_admin.html',
                {'error': error_message}
            )
    else:
        return redirect('admin-tasklist')


# REST framework viewset
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class TaskListApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # Helper functions
    def get_task(self, pk):
        return get_object_or_404(Task, pk=pk)

    # List all todos
    def get(self, request, *args, **kwargs):

        assignee_id = request.query_params.get('assignee', None)
        sort_by = request.query_params.get('sort', 'deadline')  # Default sorting by deadline
        order = request.query_params.get('order', 'asc')  # Default order ascending

        if request.user.is_superuser and not assignee_id:
            tasks = Task.objects.all()
        else:
            if assignee_id:
                tasks = Task.objects.filter(assignee=assignee_id)
            else:
                tasks = Task.objects.filter(assignee=request.user.id)

        if sort_by in [
            'title',
            'assignee',
            'status',
            'startDate',
            'deadline',
            'priority']:
            if order == 'desc':
                tasks = tasks.order_by(f'-{sort_by}')
            else:
                tasks = tasks.order_by(sort_by)
        else:
            tasks = tasks.order_by('deadline')

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Create a Todo
    def post(self, request, *args, **kwargs):
        try:
            check_superuser(request.user)

            if request.content_type == 'application/json':
                data = request.data
            else:
                data = request.POST
            serializer = TaskSerializer(data=data)

            if serializer.is_valid():
                task = serializer.save()
                response_data = serializer.data

                response_data['assignee_email'] = task.assignee.email

                notify_assignee_email(
                    task,
                    task.startDate,
                    task.deadline
                )
                schedule_warning_email(
                    task.deadline,
                    task.assignee.email,
                    task.assignee.username,
                    task.title
                )

                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Update an existing task

    def put(self, request, *args, **kwargs):
        try:
            # check_superuser(request.user)
            task = self.get_task(kwargs.get('pk'))
            serializer = TaskSerializer(task, data=request.data, partial=False)

            if serializer.is_valid():
                serializer.save()
                response_data = serializer.data

                start_date_str = request.data['startDate']
                deadline_str = request.data['deadline']

                response_data['assignee_email'] = task.assignee.email

                notify_assignee_email(
                    task,
                    start_date_str,
                    deadline_str,
                    is_update=True
                )
                schedule_warning_email(
                    isoparse(deadline_str),
                    task.assignee.email,
                    task.assignee.username,
                    task.title
                )

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Partially update a task
    def patch(self, request, *args, **kwargs):
        task = self.get_task(kwargs.get('pk'))

        if not request.user.is_superuser and task.assignee != request.user:
            return Response(
                {'detail': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data

            deadline_str = request.data.get('deadline')
            if deadline_str:
                try:
                    response_data['assignee_email'] = task.assignee.email

                    send_task_email_to_assignee_updated.delay(
                        task.assignee.email,
                        task.assignee.username,
                        task.title
                    )
                    notify_superusers_of_task_updated.delay(
                        task.title,
                        request.user.username
                    )
                    schedule_warning_email(
                        isoparse(deadline_str),
                        task.assignee.email,
                        task.assignee.username,
                        task.title
                    )

                except ValueError:
                    return Response(
                        {'error': 'Invalid date format'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):

        if not request.user.is_superuser:
            return Response(
                {'detail': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )

        task = self.get_task(kwargs.get('pk'))
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
