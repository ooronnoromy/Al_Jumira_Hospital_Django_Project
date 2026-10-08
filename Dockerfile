FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN DJANGO_ENV=development DJANGO_DEBUG=1 python manage.py collectstatic --noinput
ENV DJANGO_ENV=production
CMD ["sh", "scripts/railway_start.sh"]
