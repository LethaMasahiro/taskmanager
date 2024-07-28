#coding 
### 1. **Install Django REST Framework**

First, ensure that you have Django REST Framework installed:

bash

Code kopieren

`pip install djangorestframework`

### 2. **Add DRF to Your Installed Apps**

Update your `settings.py` to include `rest_framework` in the `INSTALLED_APPS` list:

python

Code kopieren

`INSTALLED_APPS = [     ...     'rest_framework', ]`

### 3. **Create a Serializer for Your Task Model**

Create a `serializers.py` file in your app directory and define a serializer for the `Task` model:

python

Code kopieren

`# taskmanagerapp/serializers.py  from rest_framework import serializers from .models import Task  class TaskSerializer(serializers.ModelSerializer):     class Meta:         model = Task         fields = '__all__'  # Include all fields from the Task model`

### 4. **Define API Views for CRUD Operations**

You can use DRF’s `ModelViewSet` to create views for the `Task` model:

python

Code kopieren

`# taskmanagerapp/views.py  from rest_framework import viewsets from .models import Task from .serializers import TaskSerializer  class TaskViewSet(viewsets.ModelViewSet):     queryset = Task.objects.all()     serializer_class = TaskSerializer`

### 5. **Create URL Endpoints for the API**

Add a new `urls.py` file in your app directory or update the existing one to include the API routes:

python

Code kopieren

`# taskmanagerapp/urls.py  from django.urls import path, include from rest_framework.routers import DefaultRouter from .views import TaskViewSet  router = DefaultRouter() router.register(r'tasks', TaskViewSet)  # Register the TaskViewSet with the router  urlpatterns = [     path('', include(router.urls)),  # Include the router's URLs ]`

Make sure you include this `urls.py` file in the main `urls.py` of your project:

python

Code kopieren

`# project/urls.py  from django.contrib import admin from django.urls import path, include  urlpatterns = [     path('admin/', admin.site.urls),     path('api/', include('taskmanagerapp.urls')),  # Include the app's API URLs ]`

### 6. **Add Authentication to Your API (Optional)**

If you want to require authentication for accessing your API, update your `settings.py` to include authentication classes:

python

Code kopieren

`# settings.py  REST_FRAMEWORK = {     'DEFAULT_AUTHENTICATION_CLASSES': [         'rest_framework.authentication.BasicAuthentication',         'rest_framework.authentication.SessionAuthentication',     ],     'DEFAULT_PERMISSION_CLASSES': [         'rest_framework.permissions.IsAuthenticated',     ], }`

### 7. **Testing Your API Endpoints**

You can test your API endpoints using tools like Postman or CURL. Here are the basic endpoints:

- **List Tasks:** `GET /api/tasks/`
- **Create a New Task:** `POST /api/tasks/`
- **Retrieve a Single Task:** `GET /api/tasks/<task_id>/`
- **Update a Task:** `PUT /api/tasks/<task_id>/`
- **Delete a Task:** `DELETE /api/tasks/<task_id>/`

### 8. **Example API Requests**

Here are examples of how you might interact with your API:

- **List Tasks:**
    
    bash
    
    Code kopieren
    
    `curl -X GET http://localhost:8000/api/tasks/ -H "Authorization: Basic <base64-encoded-credentials>"`
    
- **Create a New Task:**
    
    bash
    
    Code kopieren
    
    `curl -X POST http://localhost:8000/api/tasks/ -H "Content-Type: application/json" -H "Authorization: Basic <base64-encoded-credentials>" -d '{"title": "New Task", "description": "Task Description", "status": "PENDING", "assigneeId": 1, "startDate": "2024-07-10T14:00:00Z", "deadline": "2024-07-20T14:00:00Z", "priority": "HIGH"}'`
    
- **Update a Task:**
    
    bash
    
    Code kopieren
    
    `curl -X PUT http://localhost:8000/api/tasks/1/ -H "Content-Type: application/json" -H "Authorization: Basic <base64-encoded-credentials>" -d '{"title": "Updated Task", "description": "Updated Description", "status": "COMPLETED", "assigneeId": 2, "startDate": "2024-07-11T14:00:00Z", "deadline": "2024-07-21T14:00:00Z", "priority": "LOW"}'`
    
- **Delete a Task:**
    
    bash
    
    Code kopieren
    
    `curl -X DELETE http://localhost:8000/api/tasks/1/ -H "Authorization: Basic <base64-encoded-credentials>"`
    

### 9. **Handling Permissions and Authentication**

To further customize permissions, you can create custom permissions and include them in your API views. For example, you could allow only the task’s owner to update or delete it.

python

Code kopieren

`# taskmanagerapp/permissions.py  from rest_framework import permissions  class IsTaskOwner(permissions.BasePermission):     def has_object_permission(self, request, view, obj):         return obj.assigneeId == request.user.id`

And update your `TaskViewSet` to use this permission class:

python

Code kopieren

`# taskmanagerapp/views.py  from .permissions import IsTaskOwner  class TaskViewSet(viewsets.ModelViewSet):     queryset = Task.objects.all()     serializer_class = TaskSerializer     permission_classes = [IsTaskOwner]  # Apply the custom permission class`

### **Summary of Code Changes**

1. **`serializers.py`:**
    
    python
    
    Code kopieren
    
    `from rest_framework import serializers from .models import Task  class TaskSerializer(serializers.ModelSerializer):     class Meta:         model = Task         fields = '__all__'`
    
2. **`views.py`:**
    
    python
    
    Code kopieren
    
    `from rest_framework import viewsets from .models import Task from .serializers import TaskSerializer  class TaskViewSet(viewsets.ModelViewSet):     queryset = Task.objects.all()     serializer_class = TaskSerializer`
    
3. **`urls.py`:**
    
    python
    
    Code kopieren
    
    `from django.urls import path, include from rest_framework.routers import DefaultRouter from .views import TaskViewSet  router = DefaultRouter() router.register(r'tasks', TaskViewSet)  urlpatterns = [     path('', include(router.urls)), ]`
    
4. **`settings.py`:**
    
    python
    
    Code kopieren
    
    `REST_FRAMEWORK = {     'DEFAULT_AUTHENTICATION_CLASSES': [         'rest_framework.authentication.BasicAuthentication',         'rest_framework.authentication.SessionAuthentication',     ],     'DEFAULT_PERMISSION_CLASSES': [         'rest_framework.permissions.IsAuthenticated',     ], }`
    
5. **Testing API Endpoints:**
    
    - Use tools like Postman or `curl` for API testing.
    - **List Tasks:** `GET /api/tasks/`
    - **Create Task:** `POST /api/tasks/`
    - **Retrieve Task:** `GET /api/tasks/<task_id>/`
    - **Update Task:** `PUT /api/tasks/<task_id>/`
    - **Delete Task:** `DELETE /api/tasks/<task_id>/`