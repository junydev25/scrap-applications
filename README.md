# Scraping Project v1 (`django-scraping 1.1.0`)

![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white)
![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=Prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/grafana-%23F46800.svg?style=for-the-badge&logo=grafana&logoColor=white)
![CAdvisor](https://img.shields.io/badge/cadvisor-%34E0A1.svg?style=for-the-badge&logo=tripadvisor&logoColor=white)
![Oracle](https://img.shields.io/badge/oracle-F80000?style=for-the-badge&logo=oracle&logoColor=white)

## 실행 방법

### Local

```shell
# 1. .evn.dev 또는 .env.prod 생성 후 필요한 환경변수 작성(dev -> sqlite3 / prod -> oracle)
cp .env.template .env.dev

# 2. Migration
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# 2.1 운영 서버인 경우
python manage.py collectstatic --noinput --ignore admin/*

# 2.2 Sample Dataset이 필요한 경우
python manage.py seed_approvals

# 3. Run
python manage.py runserver
```

### Docker
```shell
# 1. .evn.dev 또는 .env.prod 생성 후 필요한 환경변수 작성(dev -> sqlite3 / prod -> oracle)
# 1.1 만약 .env.dev를 선택하면 Dockerfile, docker-compose.yml에서 env 파일 수정 필요
cp .env.template .env.dev

# 2. docker-compose.yml 실행
docker compose up -d 
```

## Scraping Project v1 설명

`django-scraping`의 `1.1.0`버전은 다음을 목표로 구성되었습니다.

- Django로 백엔드 서버 구성
    - 동기 서버로 구성
- Server Side Rendering(SSR)로 구성
    - Django Template 사용
    - `index.html`: `login.html` 또는 `approvals.html`로 리다이렉션
    - `login.html`: 로그인 페이지
    - `approvals.html`: 신청 내역 및 승인(거부) 페이지
- WSGI(Web Server Gateway Interface)
    - Gunicorn 사용 → `8000` 포트
- Database Server
  - `dev`: SQLite3 사용
  - `prod`: Oracle 사용 → `1521` 포트
- Web Server
    - Nginx 사용 → `80` 포트
- Monitoring
    - Prometheus(`django_prometheus`) → `9090` 포트
    - Grafana → `3000` 포트
    - CAdvisor → `8080` 포트
    - Oracle DB Exporter → `9161` 포트
> [!WARNING]
> 추후에 Grafana Server에 TLS 설정을 추가한 후 Prometheus, CAdvisor, Oracle DB Exporter 포트는 닫아야 함

> [!IMPORTANT]
> Oracle DB 사용시 주의 사항
> - Django version < `5.0.0`인 경우 `cx_Oracle`을 사용하기 때문에 그에 맞는 설정을 해줘야 합니다. 특히, SID를 사용하도록 되어 있기 때문에 PDB와 연결하고 싶은 경우 `DATABASES[default][NAME]`에 직접 `DATABASES[default][HOST]`와 `DATABASES[default][PORT]`를 넣어서 작성해야 합니다.(Ex. `HOST:PORT/NAME`(`oracle-db:1521/XEPDB1`))
> - Django version >= `5.0.0`인 경우 `cx_Oracle` 대신 `oracledb`를 사용하기 때문에 위와 같은 설정 대신 각자 설정을 해주면 됩니다.([cx_Oracle is deprecated](https://docs.djangoproject.com/en/5.2/ref/databases/#oracle-notes]))

- Logging
    - Application(`django_structlog`): `./logs/application/scraping.log`
    - Gunicorn: `./logs/gunicorn/access.log`, `./logs/gunicorn/error.log`
    - Nginx: `/var/log/nginx/django_v1_access.log`, `/var/log/nginx/django_v1_error.log`

## 👁️ Prometheus 설정

- `INSTALLED_APPS` 리스트 맨 앞에 추가
- `MIDDLEWARE` 맨 앞과 맨 뒤에 추가
    - `django_prometheus.middleware.PrometheusBeforeMiddleware`
    - `django_prometheus.middleware.PrometheusAfterMiddleware`
- `apps/core/metrics/core.py`, `apps/core/metrics/collectors.py`, `apps/core/metrics/middleware.py` 작성
- `views.py`에서 필요한 부분에 측정하도록 추가
- `config/urls.py`에 `urlpatterns` 추가
  ```python
    urlpatterns = [
        path("", include("django_prometheus.urls"))
    ]
  ```

## 🐍 WSGI(Gunicorn) 설치 및 실행

- Gunicorn 설치
  ```shell
    uv run add gunicorn
    uv lock
  ```
- Gunicorn 실행전 설정(`gunicorn.conf.py` 생성)
    - `wsgi_app = "config.wsgi:application"`(중요!)
- Gunicorn 실행
    - `uv run gunicorn -c gunicorn.conf.py`

> [!WARNING]
> Django와 함께 사용할 시 `settings`에서 Logging 설정(`disable_existing_loggers=True`)와 충돌하여 log가 기록되지 않는 문제가 발생
> 반드시 `disable_existing_loggers=False`로 설정

> [!WARNING]
> 권한 문제 때문에 `gunicorn` 명령어가 가상환경에서 얽힐 수 있으므로 실행이 안될 경우 한 번 더 확인 필요

## 추가 설명

> [!NOTE]
> `Sentry`를 추가하려고 했으나 운영 서버에서 사용하기에는 비용적인 문제가 매우 문제가 되어 제거

# 향후 Release

## `django-scraping 1.2.0`

- Session-based Login -> JWT
- `django-scraping 1.1.0`와 비교 테스트 진행

## `django-scraping 2.0.0`

- API 서버로 변환이 필요한 경우 진행(`djangorestframework`)
- API 서버로 변경되면서 Front Server 생성(SPA)
    - `Vue.js` 사용