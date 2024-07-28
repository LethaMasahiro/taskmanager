#management 

### Task Manager Project  
## Objective  
Build a simple web application with Django that includes a REST API and background task processing using Celery, all orchestrated with Docker Compose.  
## Requirements  
### Django Project  
- Create a Django project and a simple app.  
- Set up a basic model (e.g., Task with fields like title, description, completed).  
### Django Rest Framework  [[Django Rest Framework]]
- Create API endpoints for CRUD operations on the Task model.  [Tutorial which I can follow](https://blog.logrocket.com/django-rest-framework-create-api/)
### Celery  
- Set up Celery to handle background tasks.  
- Create a simple task, such as sending an email notification when a new Task is created or updated.  
### Django Celery  
- Integrate Celery with Django and ensure that tasks are scheduled and executed properly.  
### Docker Compose  
- Create a Dockerfile for the Django app.  
- Create a docker-compose.yml to orchestrate the Django app, a PostgreSQL database, and a Redis instance for Celery.  
## Steps  
### Set up Django   [This describes an approach for a task management functionality](https://www.geeksforgeeks.org/create-task-management-system-using-django/)
1. Create a new Django project and app.  
	1. Install Django: [I did it with this link](https://docs.djangoproject.com/en/5.0/howto/windows/)
	2. Create a new App with HelloWorld: [This link contains important command line snippets too](https://medium.com/@devsumitg/create-a-hello-world-application-using-django-framework-f8fec58b22df)
2. Define the Task model.  
	1. UML Model [Lucidchart](https://lucid.app/lucidchart/f734e319-7a40-493d-a36c-20f25578a72a/edit?viewport_loc=-1361%2C-880%2C2626%2C1273%2C0_0&invitationId=inv_bcc84086-450e-4b88-96ef-3539b7267dbc)
	2. Write the model in models.py
3. My addition: Add user login and registration [Use basic django forms instead of individual migrations/models](https://medium.com/@devsumitg/django-auth-user-signup-and-login-7b424dae7fab)
4. My addition: Add GUI
	1. For authentication
	2. For nice task management
5. Set up Django Rest Framework and create serializers and viewsets for the Task model.  
6. Configure URLs and routing.  
### Set up Celery  [might be helpful](https://testdriven.io/courses/django-celery/getting-started/)
1. Install Celery and configure it in the Django settings.  
2. Create a simple Celery task.  
3. Set up a Redis broker and backend.  
### Dockerize the Application  [Very important link](https://betterstack.com/community/guides/scaling-python/dockerize-django/#step-6-building-a-postgresql-image)
1. Write a Dockerfile for the Django application.  
2. Write a docker-compose.yml file to run the Django app, PostgreSQL, and Redis.  
3. Ensure that all services can communicate with each other.  
### Testing  
1. Test the API endpoints using a tool like Postman.  
2. Verify that Celery tasks are executed in the background.  
3. Write Unit tasks [https://docs.djangoproject.com/en/5.0/topics/testing/overview/](Simple Unit Tests)
### Documentation  
Write a brief README with instructions on how to set up and run the project.


## Django Project Timeline
[[Django Project Timeline]]
[[Calendar Events]]
[[Full Test]]