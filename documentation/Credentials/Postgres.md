#coding 

**Database User**: postgres
**Password**: 7712

## Postgres commands

**postgres -U (username)**  -> get into bash with username (need to put password after)
**\l** -> shows databases
**\c django_todo** -> connects to database django_todo
**\dt** -> Show tables when in a database
**\q** -> quit postgres

## Docker Commands
**docker ps** -> look at current built containers
**docker-compose up -d --build** -> builds the current containers defined in the docker-compose.yml
**docker-compose up** -> runs the built containers (need to open new terminal for further commands)
**docker compose exec db psql --username postgres --dbname django_todo** -> in C:\Users\viola\OneDrive\Desktop\Programming\TaskManager\taskmanager> when I want to get to db bash
**docker-compose down -v** -> Shuts down all containers I think
