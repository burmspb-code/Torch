import os
from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "users",
    "aurora",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# Password validation
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
LANGUAGE_CODE = "ru-ru"

TIME_ZONE = "Europe/Moscow"

USE_I18N = True

USE_TZ = True


# Настройки статических файлов (CSS, JavaScript, изображения)
STATIC_URL = "/static/"

STATICFILES_DIRS = [BASE_DIR / "static"]

# Настройки медиа-файлов (загружаемые пользователями файлы)
MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

AUTH_USER_MODEL = "users.CustomUser"

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Aurora API",
    "DESCRIPTION": "Документация платформы Aurora",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # ВОТ ЭТОТ ПАРАМЕТР ВКЛЮЧАЕТ СОРТИРОВКУ ТЕГОВ ПО АЛФАВИТУ В REDOC
    "REDOC_UI_SETTINGS": {
        "sortTagsAlphabetically": True,
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# ===================== НАСТРОЙКИ CELERY И REDIS ================================

# URL-адрес для подключения к Redis (брокер сообщений)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")

# URL-адрес для хранения результатов выполнения задач в Redis
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

# Тайм-аут для хранения результатов задач в Redis (в секундандах - 1 день)
CELERY_RESULT_EXPIRES = 86400

# Часовой пояс для планировщика Celery (должен совпадать с Django)
CELERY_TIMEZONE = TIME_ZONE  # Берём значение из переменной TIME_ZONE проекта

# Включаем отслеживание запуска задач
CELERY_TASK_TRACK_STARTED = True

# Расписание для автономных задач
CELERY_BEAT_SCHEDULE = {
    "check-reminders-every-minute": {
        "task": "daily.tasks.check_daily_reminders",
        "schedule": crontab(minute="*"),
    },
}

# ================== НАСТРОЙКИ отправки почтовых рассылок =======================

# Временно комментируем SMTP и включаем вывод в консоль:
#EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Конфигурация SMTP Яндекс
EMAIL_HOST = "smtp.yandex.ru"
EMAIL_PORT = 465  # Яндекс использует порт 465 для SSL
EMAIL_USE_SSL = True  # Использование SSL вместо TLS (для Яндекса это надежнее)
EMAIL_USE_TLS = False  # Отключаем TLS

# Логин и пароль приложения почты
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")

# 16-значный пароль приложения почты
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

# Email отправителя по умолчанию
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")

# Email для получения уведомлений о просмотрах
EMAIL_ADMIN_NOTIFICATION = os.getenv("EMAIL_ADMIN_NOTIFICATION")

# ============================== ЛОГИРОВАНИЕ ПРОЕКТА ==============================

# Убедимся, что папка для логов существует
LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{asctime}] {levelname} [{name}]: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "celery.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": "simple",
            "encoding": "utf-8",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        # Отключаем лишние Django логи, чтобы они не спамили в консоль Celery
        "django.utils.autoreload": {
            "handlers": [],
            "level": "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": [],
            "level": "ERROR",
            "propagate": False,
        },
        # Корневой логгер приложения (покрывает 'aurora', 'aurora.tasks', 'aurora.views' и т.д.)
        "aurora": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,  # Запрещает передачу логов выше (например, в root логгер)
        },
        # Системные логи самого Celery (воркеры, хартбиты, коннекты к брокеру)
        "celery": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
# ==============================================================================