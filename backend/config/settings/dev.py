from backend.config.settings.base import *

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# django-debug-toolbar
# django-debug-toolbar가 동작할 IP 주소를 지정
INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1"])

# INSTALLED_APPS += ["debug_toolbar"]

# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
