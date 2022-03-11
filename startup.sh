#!bin/bash

python crawler/rightmove 2>&1 &
python manage.py runserver 0.0.0.0:8000