web: gunicorn config.wsgi:application --log-file -
worker: celery -A config worker -l info
release: python manage.py migrate
