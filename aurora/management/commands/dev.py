import os
import subprocess
import sys
import shutil
import time
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Запуск Docker Redis, Django и Celery одновременно для локальной разработки"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Запуск локальной инфраструктуры (Docker + Django + Celery) ==="))

        # Имя Docker-контейнера для Redis
        container_name = "torch"
        processes = {}

        # Проверяем наличие Docker в системе
        if not shutil.which("docker"):
            self.stdout.write(self.style.ERROR(
                "Ошибка: Docker не найден в PATH системы! Убедитесь, что Docker Desktop установлен и запущен."
            ))
            sys.exit(1)

        try:
            # Проверяем, существует ли уже контейнер с таким именем
            check_container = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                capture_output=True, text=True, check=True
            )

            if container_name in check_container.stdout:
                # Контейнер есть, запускаем его
                self.stdout.write(self.style.SUCCESS(f"-> Запуск существующего контейнера {container_name}..."))
                subprocess.run(["docker", "start", container_name], check=True, capture_output=True)
            else:
                # Контейнера нет, создаем и запускаем новый
                self.stdout.write(self.style.SUCCESS(f"-> Скачивание образа и создание контейнера {container_name}..."))
                subprocess.run(
                    ["docker", "run", "-d", "-p", "6379:6379", "--name", container_name, "redis"],
                    check=True, capture_output=True
                )

            # Небольшая пауза, чтобы Redis успел проинициализироваться внутри Docker
            time.sleep(1)

        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(
                f"Ошибка при работе с Docker. Убедитесь, что приложение Docker Desktop запущено!\nДетали: {e.stderr}"
            ))
            sys.exit(1)

        current_env = os.environ.copy()
        # Форсируем использование UTF-8 для всех потоков ввода-вывода Python
        current_env["PYTHONIOENCODING"] = "utf-8"

        # Команда для запуска Django
        self.stdout.write(self.style.SUCCESS("-> Запуск Django сервера..."))
        processes['django'] = subprocess.Popen(
            [sys.executable, "manage.py", "runserver"],
            env=current_env  # <-- Передаем окружение
        )

        # Команда для запуска Celery
        self.stdout.write(self.style.SUCCESS("-> Запуск воркера Celery..."))
        processes['celery'] = subprocess.Popen([
            "celery", "-A", "config", "worker", "--loglevel=info", "-P", "threads", "-Q", "celery,emails"
        ], stdout=sys.stdout, stderr=sys.stderr)  # Перенаправляем вывод в родительскую консоль

        try:
            # Держим главный скрипт активным, пока работает Django
            if 'django' in processes:
                processes['django'].wait()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nОстановка всех фоновых процессов..."))

            # Останавливаем Django и Celery
            for name, process in processes.items():
                try:
                    process.terminate()
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()

            # Останавливаем Docker-контейнер Redis, чтобы он не жрал оперативку в фоне
            self.stdout.write(self.style.WARNING(f"-> Остановка Docker-контейнера {container_name}..."))
            subprocess.run(["docker", "stop", container_name], capture_output=True)

            self.stdout.write(self.style.SUCCESS("Все процессы успешно остановлены."))
