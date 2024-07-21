from django.urls import path, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TaskListApiView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

#REST router
#router = DefaultRouter()
#router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('', views.index, name='home'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('index/admin', views.admin_index, name='admin-index'),
    path('tasklist/', views.user_tasklist, name='tasklist'),
    path('tasklist/admin/', views.admin_tasklist, name='admin-tasklist'),
    path('createtask/', views.task_create, name='task-create'),
    path('updatetask/<int:task_id>/', views.task_update, name='task-update'),
    path('deletetask/<int:task_id>/', views.task_delete, name='task-delete'),
    path('api/tasks/', TaskListApiView.as_view(), name='task-list-api'),
    path('api/tasks/<int:pk>/', TaskListApiView.as_view(), name='task-detail-api'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh')
]