up:
	docker compose up

down:
	docker compose down
	docker ps -a

init:
	echo "Execution copy .env.example to .env..."
	cp .env.dist .env
	echo "Booting up containers"
	docker compose up -d
	echo "Waiting for containers to finish booting..."
	sleep 15
	docker compose exec web ./venv/bin/python3 manage.py makemigrations
	docker compose exec web ./venv/bin/python3 manage.py migrate --noinput
	#docker compose exec web ./venv/bin/python3 manage.py collectstatic
	echo "Create super user"
	docker compose exec web ./venv/bin/python3 manage.py createsuperuser

migrate:
	@if [ ${app} ]; then \
      	docker compose exec web ./venv/bin/python3 manage.py migrate ${app}; \
    else \
      	docker compose exec web ./venv/bin/python3 manage.py migrate; \
    fi

migrations:
	@if [ ${app} ]; then \
      	docker compose exec web ./venv/bin/python3 manage.py makemigrations ${app}; \
    else \
      	docker compose exec web ./venv/bin/python3 manage.py makemigrations; \
    fi

db-flush:
	docker compose exec web ./venv/bin/python3 manage.py flush

bash:
	docker compose exec web /bin/bash

startapp:
	docker compose exec web ./venv/bin/python3 manage.py startapp ${app}

requirements:
	docker compose exec web ./venv/bin/python3 -m pip install -r requirements.txt #install web container
	python3 -m pip install -r requirements.txt #install locally

test:
	@if [ ${app} ] && [ ${class} ] && [ ${method} ]; then \
      	echo "Testing: App: ${app}, Class: ${class} and Method ${method}"; \
      	docker compose exec web ./venv/bin/python3 manage.py test ${app}.tests.${class}.${method} --settings=licenselinkup.settings.testing -v2; \
    elif [ ${app} ] && [ ${class} ]; then \
      	echo "Testing: App: ${app}, Class: ${class}"; \
      	docker compose exec web ./venv/bin/python3 manage.py test ${app}.tests.${class} --settings=licenselinkup.settings.testing -v2; \
    elif [ ${app} ]; then \
      	echo "Testing: App: ${app}"; \
      	docker compose exec web ./venv/bin/python3 manage.py test ${app}.tests --settings=licenselinkup.settings.testing -v2; \
    else \
      	echo "Testing: Running all tests"; \
      	docker compose exec web ./venv/bin/python3 manage.py test --settings=licenselinkup.settings.testing -v2; \
    fi
