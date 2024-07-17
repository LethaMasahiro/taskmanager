from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.urls import reverse
from .forms import SignupForm, LoginForm
from .models import Task
from .tasks import send_task_email_to_assignee
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from .serializers import TaskSerializer
from rest_framework_simplejwt.tokens import RefreshToken
import requests

# Create your views here.
from django.http import HttpResponse

#Homepage
def index(request):
    return render(request, 'index.html')

#admin check
def is_admin(user):
    return user.is_superuser

admin_required = user_passes_test(lambda user: user.is_superuser)

#user login
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
                    return redirect('all_tasklist')
                return redirect('tasklist')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

#user signup
def user_signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

#logout page
def user_logout(request):
    logout(request)
    return redirect('login')

#user task list
@login_required
def user_tasklist(request):
    # tasks = Task.objects.filter(assignee=request.user)

    # Generate JWT token for the user
    refresh = RefreshToken.for_user(request.user)
    access_token = str(refresh.access_token)
    headers = {'Authorization': f'Bearer {access_token}'}

    # Get the user ID
    user_id = request.user.id

    response = requests.get(f'http://localhost:8000/api/tasks/?assignee={user_id}', headers=headers)

    if response.status_code == 200:
        tasks = response.json()
        return render(request, 'tasklist.html', {'tasks': tasks})
    
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return render(request, 'tasklist.html', {'error': 'Failed to retrieve tasks'})

#create task
@login_required
def task_create(request):
    if request.method == 'POST':

        data = {
            'title' : request.POST.get('title'),
            'description' : request.POST.get('description'),
            'status' : request.POST.get('status'),
            'assignee' : request.POST.get('assignee'),
            'startDate' : request.POST.get('startDate'),
            'deadline' : request.POST.get('deadline'),
            'priority' : request.POST.get('priority')
        }

        # Generate JWT token for the user
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        headers = {'Authorization': f'Bearer {access_token}'}

        response = requests.post(f'http://localhost:8000/api/tasks/', data=data, headers=headers)

        if response.status_code == 201:
            # Get the email of the assignee
            assignee_email = response.json().get('assignee_email')
            send_task_email_to_assignee(assignee_email, data['title'])

            return redirect('tasklist')
        
        else:
            print(f"Error: {response.status_code} - {response.text}")
            print(f"Sent Data: {data}")
            return render(request, 'tasklist_create.html', {'error': response.json()})

    else:
        users = User.objects.all()
        statuses = Task.Status.choices
        priorities = Task.Priority.choices
        return render(request, 'tasklist_create.html', {'users':users, 'statuses':statuses, 'priorities':priorities})

#Todo: Update task
@login_required
def task_update(request, task_id):
    current_task = get_object_or_404(Task, pk=task_id)
    if request.method == 'POST':

        data = {
            'title' : request.POST.get('title'),
            'description' : request.POST.get('description'),
            'status' : request.POST.get('status'),
            'assignee' : request.POST.get('assignee'),
            'startDate' : request.POST.get('startDate'),
            'deadline' : request.POST.get('deadline'),
            'priority' : request.POST.get('priority')
        }

        # Filter out any fields that are empty or not present
        data = {k: v for k, v in data.items() if v is not None and v.strip() != ''}

        # Generate JWT token for the user
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.patch(f'http://localhost:8000/api/tasks/{task_id}/', json=data, headers=headers)

        if response.status_code == 200:
            # Get the email of the assignee
            assignee_email = response.json().get('assignee_email')
            send_task_email_to_assignee(assignee_email, data['title'])

            return redirect('tasklist')
        
        else:
            print(f"Error: {response.status_code} - {response.text}")
            print(f"Sent Data: {data}")
            return render(request, 'tasklist_create.html', {'error': response.json()})

    else:
        users = User.objects.all()
        statuses = Task.Status.choices
        priorities = Task.Priority.choices
        return render(request, 'tasklist_update.html', {'users':users, 'statuses':statuses, 'priorities':priorities, 'task':current_task})

#Todo: Delete task
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

        response = requests.delete(f'http://localhost:8000/api/tasks/{task_id}/', headers=headers)

        if response.status_code == 204:
            return redirect('tasklist')
        
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return render(request, 'tasklist.html', {'error': 'Failed to retrieve tasks'})
    else:
        current_task = get_object_or_404(Task, pk=task_id)
        return render(request, 'tasklist_delete.html', {'task': current_task})

#REST framework viewset
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

class TaskListApiView(APIView):
    # add permission to check if user is authenticated
    permission_classes = [permissions.IsAuthenticated]

    # 1. List all todos
    def get(self, request, *args, **kwargs):
        
        assignee_id = request.query_params.get('assignee', None)
        if assignee_id:
            tasks = Task.objects.filter(assignee=assignee_id)
        else:
            tasks = Task.objects.filter(assignee=request.user.id)

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):  
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save()
            response_data = serializer.data
            # get email of the assignee to send an email
            response_data['assignee_email'] = task.assignee.email
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        else:
            print(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    # 3. Update an existing task
    def put(self, request, *args, **kwargs):
        task = self.get_task(kwargs.get('pk'))
        serializer = TaskSerializer(task, data=request.data, partial=False)  # Full update
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            response_data['assignee_email'] = task.assignee.email
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    #partially update a task
    def patch(self, request, *args, **kwargs):
        task = self.get_task(kwargs.get('pk'))
        serializer = TaskSerializer(task, data=request.data, partial=True)  # Partial update
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            response_data['assignee_email'] = task.assignee.email
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, *args, **kwargs):
        task = self.get_task(kwargs.get('pk'))
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    #self method: get the task
    def get_task(self, pk):
        return get_object_or_404(Task, pk=pk)


def hello(request):
    return HttpResponse("Hello, World!")

from .tasks import my_task

result = my_task.delay(3, 5)