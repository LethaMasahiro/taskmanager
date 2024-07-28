# Taskmanager

Hello and thank you for trying out my very first Django project! This project has been motivated by AKA Intelligence, who asked me to develop a task managing app with Django, including a Celery backend, a Django REST API framework, all dockerized in components. I developed this project over the course of a few weeks with some downtime in between, and I experienced many ups and downs, but in general it was a very valuable experience to create a web application from scratch with new technologies. The project is not perfect and I will keep working on it to refine the functionality, but it is quite stable in its use case and can be installed and used by others.
Enjoy! :D

## Installation Instructions

1. First, clone this project on your local machine and open it with a development environment of your choice. You can probably also start this project in your console but I haven't tried starting it without visual studio code yet.\
2. Since the application is dockerized, use your console to navigate to ./taskmanager, if you're not already there yet, since the Dockerfile is situated there.
3. Use the command ```docker-cpmpose build``` to build the project.\
4. Start the containers with ```docker-compose up``` and wait until Celery has loaded the tasks.\
5. In your browser, navigate to http://localhost:8000/ . You can now start using the application.\
6. If you want to stop the containers, use ctrl+c in the console anytime.\

## A Few Notes and Restrictions

1. My application divides the users in two roles. While superusers can create, fully update and delete tasks, normal users can only update the status of the tasks they are assigned to. The superusers can also view either only their own tasks or they can have a look at all of the tasks in the database. Normal users only have an insight of their own tasks.\
2. If you want to sign in with your own account, you will be assigned the role of a normal user. However, you can use the following superuser account to have a look at the admin functionality:\
username: bb\
password: abcdefgh12\
3. Additionally to receiving a mail when a task has been assigned to a user, I implemented a functionality that keeps track of the task's deadline and informs the assignee 24 hours prior to the deadline. However, this only works when the service is running and since this application is not in production, it might generate these mails too late (when the service is started again). I also didn't fully test this functionality yet with my new timezone management.\
4. The hardest part about this project was actually the management of timezones. For me, it's still quite unintuitive how datetimes are saved in Django, so I had a lot of difficulties enforcing my architecture. This is also one of the reasons why the code might look more complicated than it actually, especially in views.py and in my unit tests. I would like to work more on it and include dynamic timezones, but for now I am just glad that the timezone conversion works for Korea.\

If you have any questions, feel free to reach out to me!
