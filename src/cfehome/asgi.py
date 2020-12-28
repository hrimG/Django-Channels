import os
from channels.routing import get_default_application
from django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfehome.settings')
django.setup()

application = get_default_application()
