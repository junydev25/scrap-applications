from pathlib import Path

import cx_Oracle
import environ
import structlog

# Setting User model
AUTH_USER_MODEL = "users.User"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

env = environ.Env()
DJANGO_ENV = env("DJANGO_ENV", default="dev")
environ.Env.read_env(env_file=BASE_DIR / f".env.{DJANGO_ENV}")

# Properteis
APPROVALS_PROPERTIES = {
    "EXTERNAL_URL": env.get_value("EXTERNAL_URL"),
    "ITEMS_PER_PAGE": 10,
    "ORDER_BY": "ASC",  # DESC
}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")
DEBUG = True if DJANGO_ENV == "dev" else False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

CSRF_FAILURE_VIEW = "backend.config.views.csrf_failure_view"

# Application definition
INSTALLED_APPS = [
    "django_prometheus",
    "backend.apps.core",
    "django_structlog",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "backend.apps.users",
    "backend.apps.approvals",
]

if DJANGO_ENV == "dev":
    INSTALLED_APPS += [
        "django.contrib.admin",
    ]

# 요청과 응답 사이에 거쳐 가는 필터들
# 순서가 중요(위에서부터 차례로 실행)
MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "backend.config.urls"

TEMPLATES_DIR = BASE_DIR / "backend" / "templates"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATES_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.config.wsgi.application"

# Database
# Database 연결 설정
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
db_name = None
if DJANGO_ENV == "dev":
    db_file_path = BASE_DIR / "infra" / "db"
    db_file_path.mkdir(parents=True, exist_ok=True)
    db_name = str(db_file_path / env.get_value("DB_NAME"))
elif DJANGO_ENV == "prod":
    db_name = env.get_value("DB_NAME")

DATABASES = {
    "default": {
        "ENGINE": env.get_value("DB_ENGINE"),
        "NAME": db_name,
        "USER": env.get_value("DB_USER"),
        "PASSWORD": env.get_value("DB_PASSWORD"),
        "HOST": env.get_value("DB_HOST"),
        "PORT": env.get_value("DB_PORT"),
    }
}

# Password validation
# 회원가입/비밀번호 변경 시 사용할 비밀번호 검증 규칙
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = env.get_value("LANGUAGE_CODE")
TIME_ZONE = env.get_value("TIME_ZONE")

USE_I18N = True
USE_TZ = True  # Timezone

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "backend" / "static"]
STATIC_ROOT = BASE_DIR / "backend" / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "backend" / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging
logging_path = BASE_DIR / env.get_value("LOGGING_FILE_PATH")
logging_path.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": env.get_value("LOGGING_FORMATTER"),
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(logging_path / "scraping.log"),
            "formatter": env.get_value("LOGGING_FORMATTER"),
            "level": env.get_value("LOGGING_LEVEL"),
            "encoding": env.get_value("LOGGING_ENCODING"),
            "when": env.get_value("LOGGING_WHEN"),
            "interval": env.get_value("LOGGING_INTERVAL", cast=int),
            "backupCount": env.get_value("LOGGING_BACKUP_COUNT", cast=int),
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": env.get_value("LOGGING_LEVEL"),
    },
}

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(ensure_ascii=False),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
