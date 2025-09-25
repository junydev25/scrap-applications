import environ

env = environ.Env()
ENV = env("DJANGO_ENV", default="dev")

if ENV == "production":
    from backend.config.settings.prod import *
else:
    from backend.config.settings.dev import *
