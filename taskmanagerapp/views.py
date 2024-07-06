from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def hello(request):
    return HttpResponse("Hello, World!")

from .tasks import my_task

result = my_task.delay(3, 5)