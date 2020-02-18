"""
WSGI config for capital project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Enforce this environment variable (since wsgi is used only in production):
os.environ['DJANGO_SETTINGS_MODULE'] = 'capital.prod_settings'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capital.settings')

application = get_wsgi_application()
