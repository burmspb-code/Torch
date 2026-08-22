import os
from logging.config import dictConfig

from celery import Celery

from celery.signals import worker_init
from django.conf import settings

# 1. Указываем Django, что настройки лежат в config.settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# 2. Создаем экземпляр Celery с именем config
app = Celery("config")

# 3. Читаем настройки Celery из settings.py с префиксом CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Отключаем перехват root logger'а Celery, чтобы использовать Django настройки
app.conf.worker_hijack_root_logger = False

# 4. Автоматически ищем файлы tasks.py в приложениях (например, в daily и users)
app.autodiscover_tasks()

# 5. Настраиваем логирование Celery через Django настройки при инициализации worker
@worker_init.connect
def config_loggers(*args, **kwargs):
    dictConfig(settings.LOGGING)
