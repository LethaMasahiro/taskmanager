from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .forms import SignupForm, LoginForm
from .models import Task
from .tasks import send_task_email_to_assignee_created, send_task_email_to_assignee_updated, notify_superusers_of_task_updated, warn_users_one_day_before_deadline
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from .serializers import TaskSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.utils import timezone
import pytz
import requests
from django.conf import settings


# Homepage
def index(request):
    if not (request.user.is_superuser):
        return redirect('tasklist')
    return render(request, 'index.html')


def is_admin(user):
    return user.is_superuser


def admin_required(view_func):
    decorated_view_func = login_required(
        user_passes_test(
            lambda user: user.is_superuser
        )(view_func)
    )
    return decorated_view_func


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
    refresh = RefreshToken.for_user(request.user)
    access_token = str(refresh.access_token)
    headers = {'Authorization': f'Bearer {access_token}'}

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
            current_time = now()
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

    refresh = RefreshToken.for_user(request.user)
    access_token = str(refresh.access_token)
    headers = {'Authorization': f'Bearer {access_token}'}

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
            'access_token': access_token,
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
            start_date = datetime.fromisoformat(start_date_str).replace(tzinfo=pytz.UTC)
            end_date = datetime.fromisoformat(end_date_str).replace(tzinfo=pytz.UTC)
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
            'startDate': start_date.isoformat(),
            'deadline': end_date.isoformat(),
            'priority': request.POST.get('priority')
        }

        # Generate JWT token for the user
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        headers = {'Authorization': f'Bearer {access_token}'}

        response = requests.post(
            f'{settings.BASE_URL}/api/tasks/',
            data=data, headers=headers
        )

        try:
            response_data = response.json()
            print('Response data: ', response_data)
        except ValueError as e:
            print(f"JSON decode error: {e}")
            response_data = {"error": "Failed to decode response as JSON."}
            response_status = 500  # Internal Server Error
        else:
            response_status = response.status_code

        if response_status == 201:
            return redirect('admin-tasklist')
        else:
            print(f"Error: {response_status} - {response.text}")
            print(f"Sent Data: {data}")
            return render(
                request,
                'tasklist_create.html',
                {'error': response_data}
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
        data = {
            k: v for k, v in data.items() if v is not None and v.strip() != ''
        }

        # Generate JWT token for the user
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        # Convert datetime strings to timezone-aware datetime objects
        try:
            if 'startDate' in data:
                data['startDate'] = datetime.fromisoformat(start_date_str).replace(tzinfo=pytz.UTC).isoformat()
            if 'deadline' in data:
                data['deadline'] = datetime.fromisoformat(end_date_str).replace(tzinfo=pytz.UTC).isoformat()
        except ValueError:
            return render(
                request,
                'tasklist_create.html',
                {'error': 'Invalid date format'}
            )

        response = requests.patch(
            f'{settings.BASE_URL}/api/tasks/{task_id}/',
            json=data, headers=headers
        )

        if response.status_code == 200:
            return redirect('admin-tasklist')
        else:
            print(f"Error: {response.status_code} - {response.text}")
            print(f"Sent Data: {data}")
            return render(
                request,
                'tasklist_create.html',
                {'error': response.json()}
            )

    else:
        users = User.objects.all()
        statuses = Task.Status.choices
        priorities = Task.Priority.choices
        return render(
            request,
            'tasklist_update.html',
            {
                'users': users,
                'statuses': statuses,
                'priorities': priorities,
                'task': current_task
            }
        )


@login_required
@admin_required
def task_delete(request, task_id):
    if request.method == 'POST':
        # Generate JWT token for the user
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.delete(
            f'{settings.BASE_URL}/api/tasks/{task_id}/',
            headers=headers
        )

        if response.status_code == 204:
            return redirect('admin-tasklist')

        else:
            print(f"Error: {response.status_code} - {response.text}")
            return render(
                request,
                'tasklist.html',
                {'error': 'Failed to retrieve tasks'}
            )
    else:
        current_task = get_object_or_404(Task, pk=task_id)
        return render(request, 'tasklist_delete.html', {'task': current_task})


# REST framework viewset
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

# TODO: Allow ascending and descending sort

class TaskListApiView(APIView):
    # Add permission to check if user is authenticated
    permission_classes = [permissions.IsAuthenticated]

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
        if not request.user.is_superuser:
            return Response(
                {'detail': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if request.content_type == 'application/json':
            data = request.data
        else:
            data = request.POST
        serializer = TaskSerializer(data=data)

        if serializer.is_valid():
            task = serializer.save()
            response_data = serializer.data

            # Convert startDate and deadline to timezone-aware datetimes
            start_date_str = data['startDate']
            deadline_str = data['deadline']

            try:
                start_date_aware = datetime.fromisoformat(start_date_str).replace(tzinfo=pytz.UTC)
                deadline_aware = datetime.fromisoformat(deadline_str).replace(tzinfo=pytz.UTC)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            response_data['assignee_email'] = task.assignee.email

            send_task_email_to_assignee_created.delay(
                task.assignee.email,
                task.assignee.username,
                task.title,
                start_date_aware,
                deadline_aware
            )

            # Calculate notify_time as 24 hours before the task deadline
            notify_time = deadline_aware - timedelta(days=1)

            if notify_time > timezone.now():
                warn_users_one_day_before_deadline.apply_async(
                    (
                        task.assignee.email,
                        task.assignee.username,
                        task.title,
                        deadline_aware
                    ),
                    eta=notify_time
                )
            else:
                print("Deadline is too soon to schedule a warning email.")

            print(response_data)

            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            print(f"Validation errors: {serializer.errors}")
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    # Update an existing task

    def put(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response(
                {'detail': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )

        task = self.get_task(kwargs.get('pk'))
        serializer = TaskSerializer(task, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data

            start_date_str = request.data['startDate']
            deadline_str = request.data['deadline']

            try:
                start_date_aware = datetime.fromisoformat(start_date_str).replace(tzinfo=pytz.UTC)
                deadline_aware = datetime.fromisoformat(deadline_str).replace(tzinfo=pytz.UTC)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            response_data['assignee_email'] = task.assignee.email

            # Notify the assignee
            send_task_email_to_assignee_created.delay(
                task.assignee.email,
                task.assignee.username,
                task.title,
                start_date_aware,
                deadline_aware
            )

            # Schedule deadline warning task
            notify_time = deadline_aware - timedelta(days=1)

            if notify_time > timezone.now():
                warn_users_one_day_before_deadline.apply_async(
                    (
                        task.assignee.email,
                        task.assignee.username,
                        task.title,
                        deadline_aware
                    ),
                    eta=notify_time
                )
            else:
                print("Deadline is too soon to schedule a warning email.")

            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Partially update a task
    def patch(self, request, *args, **kwargs):
        task = self.get_task(kwargs.get('pk'))

        # Check if the user is either the assignee or a superuser
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

            try:
                if deadline_str:
                    deadline_aware = datetime.fromisoformat(deadline_str).replace(tzinfo=pytz.UTC)
            except ValueError:
                return Response(
                    {'error': 'Invalid date format'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            response_data['assignee_email'] = task.assignee.email

            # Notify the assignee
            send_task_email_to_assignee_updated.delay(
                task.assignee.email,
                task.assignee.username,
                task.title
            )

            # Notify superusers
            notify_superusers_of_task_updated.delay(
                task.title,
                request.user.username
            )

            # Schedule deadline warning task
            if deadline_str:
                notify_time = deadline_aware - timedelta(days=1)

                if notify_time > timezone.now():
                    warn_users_one_day_before_deadline.apply_async(
                        (
                            task.assignee.email,
                            task.assignee.username,
                            task.title,
                            deadline_aware
                        ),
                        eta=notify_time
                    )
                else:
                    print("Deadline is too soon to schedule a warning email.")

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

    # Self method
    def get_task(self, pk):
        return get_object_or_404(Task, pk=pk)

    def schedule_warning_email(self, task, deadline):
        # Calculate notify_time as 24 hours before the task deadline
        notify_time = deadline - timedelta(days=1)

        if notify_time > datetime.now():
            warn_users_one_day_before_deadline.apply_async(
                (
                    task.assignee.email,
                    task.assignee.username,
                    task.title,
                    task.deadline
                ),
                eta=notify_time
            )
        else:
            print("Deadline is too soon to schedule a warning email.")
