#!/bin/sh

# Collect static files and migrate if needed
python /home/api/manage.py collectstatic --noinput
python /home/api/manage.py makemigrations --noinput
python /home/api/manage.py makemigrations api --noinput
python /home/api/manage.py migrate --noinput
python /home/api/manage.py migrate api --noinput

python /home/api/manage.py process_tasks &

# create a new super user, with username and password 'admin'
echo "from django.contrib.auth import get_user_model
User = get_user_model()
if User.objects.count() == 0:
    User.objects.create_superuser('$ADMIN_USERNAME', 'admin@example.com', '$ADMIN_PASSWORD')
" | python manage.py shell

python /home/load_examples.py &

#uwsgi --post-buffering=1 --http-socket :8000 --master --log-master --chdir /home/api/  --module core.wsgi
gunicorn --chdir /home/api --bind 0.0.0.0:8000 core.wsgi
