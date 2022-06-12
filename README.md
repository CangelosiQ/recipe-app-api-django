# recipe-app-api-django



## Project setup 
docker-compose run --rm app sh -c "django-admin startproject app ."



## Create a new app
docker-compose run --rm app sh -c "python manage.py startapp core"

## Collect Static files
docker-compose run --rm app sh -c "python manage.py collectstatic"

## Linting
docker-compose run --rm app sh -c "flake8"

## Run Tests
python manage.py test

### using pytest
docker-compose run --rm app sh -c "pytest"
docker-compose run --rm app sh -c "flake8 && pytest"

### using pytest-watch
docker-compose run --rm app sh -c 'ptw'


## Using the ORM
Define models -> generate migration files -> setup database -> store data

Each model maps to a table. Models contain a name, fields, other metadata, custom python logic.

docker-compose run --rm app sh -c 'python manage.py makemigrations'
docker-compose run --rm app sh -c 'python manage.py wait_for_db && python manage.py migrate'

## Create Super User
docker-compose run --rm app sh -c "python manage.py createsuperuser"

## Check the logs
docker-compose -f docker-compose-deploy.yml logs


## Update server
docker-compose -f docker-compose-deploy.yml build app
docker-compose -f docker-compose-deploy.yml up --no-deps -d app