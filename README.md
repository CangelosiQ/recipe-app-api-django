# recipe-app-api-django

docker-compose run --rm app sh -c "python manage.py collectstatic"
docker-compose run --rm app sh -c "flake8"
docker-compose run --rm app sh -c "flake8"


Project setup 
docker-compose run --rm app sh -c "django-admin startproject app ."


Run Tests
python manage.py test

Create a new app
docker-compose run --rm app sh -c "python manage.py startapp core"


docker-compose run --rm app sh -c "pytest"


docker-compose run --rm app sh -c 'ptw'

docker-compose run --rm app sh -c 'ptw --onpass "growlnotify -m \"All tests passed!\"" --onfail "growlnotify -m \"Tests failed\""'


## Using the ORM

Define models -> generate migration files -> setup database -> store data

Each model maps to a table. Models contain a name, fields, other metadata, custom python logic.

docker-compose run --rm app sh -c 'python manage.py makemigrations'
docker-compose run --rm app sh -c 'python manage.py wait_for_db && python manage.py migrate'

## Create Super User
docker-compose run --rm app sh -c "python manage.py createsuperuser"