FROM python:3.10.18-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=backend.config.settings.base
ENV DJANGO_ENV=dev

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./manage.py .
# 🔥 보안 문제: .env.prod 파일을 이미지에 포함시키면 안됨 (Secret 노출)
COPY ./.env.dev .
COPY ./backend  ./backend
## 🔥 문제: SQLite DB 파일을 이미지에 포함 (데이터 손실 위험, 확장성 문제)
#COPY ./infra/db/db.sqlite3 ./infra/db/db.sqlite3
COPY ./infra/gunicorn/gunicorn.conf.py ./infra/gunicorn/gunicorn.conf.py

RUN python manage.py makemigrations --noinput
RUN python manage.py migrate --noinput
# Dataset이 필요한 경우
RUN python manage.py seed_approvals
RUN python manage.py collectstatic --noinput --ignore admin/*

RUN groupadd --system --gid 1001 scrap 2>/dev/null
RUN useradd --system --gid scrap --no-create-home --home /nonexistent --shell /bin/false --uid 1001 scrap 2>/dev/null
RUN chown -R 1001:1001 /app
USER 1001

# 포트 노출
EXPOSE 8000

# Gunicorn으로 실행
CMD ["gunicorn", "-c", "infra/gunicorn/gunicorn.conf.py"]