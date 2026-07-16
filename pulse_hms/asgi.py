import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pulse_hms.settings')
from django.core.asgi import get_asgi_application
application = get_asgi_application()
