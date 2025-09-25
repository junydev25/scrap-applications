FROM python:3.10.18-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=backend.config.settings.base
ENV DJANGO_ENV=prod

# Oracle Instant Client 설치
RUN apt-get update
RUN apt-get install -y wget unzip libaio1
RUN wget -q https://download.oracle.com/otn_software/linux/instantclient/2119000/instantclient-basiclite-linux.x64-21.19.0.0.0dbru.zip
RUN unzip -q instantclient-basiclite-linux.x64-21.19.0.0.0dbru.zip -d /opt/oracle
RUN rm instantclient-basiclite-linux.x64-21.19.0.0.0dbru.zip
RUN rm -rf /var/lib/apt/lists/*

# Oracle Client 환경변수 설정
ENV PATH=/opt/oracle/instantclient_21_19:${PATH}
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_19:${LD_LIBRARY_PATH}

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./manage.py .
# 🔥 보안 문제: .env.prod 파일을 이미지에 포함시키면 안됨 (Secret 노출)
COPY ./.env.prod .
COPY ./backend  ./backend
COPY ./infra/gunicorn/gunicorn.conf.py ./infra/gunicorn/gunicorn.conf.py

RUN python manage.py collectstatic --noinput --ignore admin/*

RUN groupadd --system --gid 1001 scrap 2>/dev/null
RUN useradd --system --gid scrap --no-create-home --home /nonexistent --shell /bin/false --uid 1001 scrap 2>/dev/null
RUN chown -R 1001:1001 /app
USER 1001

# 포트 노출
EXPOSE 8000

# Gunicorn으로 실행
CMD ["sh", "-c", "\
python manage.py makemigrations --noinput && \
python manage.py migrate --noinput && \
python manage.py seed_approvals && \
gunicorn -c infra/gunicorn/gunicorn.conf.py\
"]