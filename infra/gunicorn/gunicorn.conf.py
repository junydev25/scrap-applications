import multiprocessing
from pathlib import Path

import environ

env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent
DJANGO_ENV = env("DJANGO_ENV", default="dev")
environ.Env.read_env(env_file=BASE_DIR / f".env.{DJANGO_ENV}")

wsgi_app = "backend.config.wsgi:application"

# =====================================================
# 네트워크 및 소켓 설정
# =====================================================

# bind: 어느 주소와 포트에서 요청을 받을지
# 형식: "IP:PORT" 또는 "unix:/path/to/socket"
bind = env.get_value("GUNICORN_BIND")
# bind = "127.0.0.1:8000"  # 로컬만
# bind = "unix:/tmp/gunicorn.sock"  # Unix 소켓 (Nginx와 함께 사용)

# backlog: 대기열에 쌓을 수 있는 연결 수
# 클라이언트가 연결 요청을 보냈지만 아직 워커가 처리하지 못한 요청들의 대기열
# 높을수록 더 많은 연결을 대기시킬 수 있지만 메모리 사용량 증가
backlog = 2048  # 기본값: 2048

# =====================================================
# 워커 프로세스 설정
# =====================================================

# workers: 몇 개의 워커 프로세스를 생성할지
# 공식: (CPU 코어 수 * 2) + 1
# CPU 바운드: 코어 수만큼, I/O 바운드: 더 많이
workers = multiprocessing.cpu_count() * 2 + 1
threads = env("GUNICORN_THREADS")

# worker_class: 워커 타입
worker_class = "sync"  # 기본값, 동기 처리
# worker_class = "gevent"    # 비동기, I/O 집약적 작업에 좋음
# worker_class = "eventlet"  # 비동기, 코루틴 기반
# worker_class = "tornado"   # Tornado 기반

# worker_connections: 각 워커가 동시에 처리할 수 있는 연결 수
# sync worker에서는 보통 1, async worker에서는 1000+
worker_connections = 1000

# max_requests: 워커가 처리한 후 재시작되는 요청 수
# 메모리 누수 방지용, 0이면 재시작 안함
max_requests = env("GUNICORN_MAX_REQUESTS")

# max_requests_jitter: max_requests에 랜덤 값 추가
# 모든 워커가 동시에 재시작되는 것 방지
max_requests_jitter = 100  # 900~1100 요청 후 재시작

# preload_app: 앱을 미리 로드할지
# True면 앱을 한 번만 로드하고 워커들이 공유 (메모리 효율적)
# False면 각 워커가 앱을 개별 로드 (코드 변경 시 자동 반영)
preload_app = True

# =====================================================
# 타임아웃 및 keepalive 설정
# =====================================================

# timeout: 워커가 요청 처리를 완료해야 하는 시간 (초)
# 이 시간 내에 응답하지 못하면 워커 재시작
timeout = 30  # 60초

# graceful_timeout: 워커가 graceful shutdown 할 수 있는 시간
graceful_timeout = 30

# keepalive: HTTP Keep-Alive 연결을 유지할 시간 (초)
# 클라이언트가 같은 연결로 여러 요청을 보낼 때 연결을 재사용
# 0이면 Keep-Alive 비활성화
keepalive = 2  # 2초간 연결 유지

# =====================================================
# 보안 및 제한 설정
# =====================================================

# limit_request_line: HTTP 요청 라인의 최대 길이
# 너무 긴 URL이나 헤더로 인한 공격 방지
limit_request_line = 4094  # 기본값

# limit_request_fields: HTTP 헤더 필드 최대 개수
limit_request_fields = 100

# limit_request_field_size: 각 헤더 필드의 최대 크기
limit_request_field_size = 8190

# =====================================================
# 성능 최적화
# =====================================================

# worker_tmp_dir: 워커 임시 디렉토리
# 메모리에 임시 디렉토리를 만들어 I/O 성능 향상
# worker_tmp_dir = "/dev/shm"  # RAM disk, Linux만 가능

# worker_class가 sync가 아닐 때의 추가 설정
if worker_class in ["gevent", "eventlet"]:
    worker_connections = 1000  # 비동기에서는 더 많은 연결 처리 가능

# =====================================================
# Gunicorn Logging
# =====================================================

access_logging_path = BASE_DIR / env.get_value("GUNICORN_ACCESSLOG_PATH")
access_logging_path.mkdir(parents=True, exist_ok=True)

error_logging_path = BASE_DIR / env.get_value("GUNICORN_ERRORLOG_PATH")
error_logging_path.mkdir(parents=True, exist_ok=True)

logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {"level": "INFO", "handlers": ["console"]},
    "formatters": {
        "generic": {
            "format": "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": "ext://sys.stdout",
        },
        "error_console": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": "ext://sys.stderr",
        },
        "access_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(access_logging_path / "access.log"),
            "when": "midnight",
            "interval": env.get_value("GUNICORN_LOGGING_INTERVAL", cast=int),
            "backupCount": env.get_value("GUNICORN_LOGGING_BACKUP_COUNT", cast=int),
            "formatter": "generic",
            "level": "INFO",
            "encoding": env.get_value("GUNICORN_LOGGING_ENCODING"),
        },
        "error_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(error_logging_path / "error.log"),
            "when": env.get_value("LOGGING_WHEN"),
            "interval": env.get_value("GUNICORN_LOGGING_INTERVAL", cast=int),
            "backupCount": env.get_value("GUNICORN_LOGGING_BACKUP_COUNT", cast=int),
            "formatter": "generic",
            "level": env.get_value("GUNICORN_LOGGING_LEVEL"),
            "encoding": env.get_value("GUNICORN_LOGGING_ENCODING"),
        },
    },
    "loggers": {
        "gunicorn.access": {
            "handlers": ["access_file"],
            "propagate": False,
            "level": "INFO",
            "qualname": "gunicorn.access",
        },
        "gunicorn.error": {
            "handlers": ["error_file"],
            "propagate": False,
            "level": env.get_value("GUNICORN_LOGGING_LEVEL"),
            "qualname": "gunicorn.error",
        },
    },
}

# Gunicorn 자체의 로그와 HTTP 액세스 로그

# # accesslog: HTTP 요청 로그
# # 누가, 언제, 무엇을 요청했는지
# accesslog = str(BASE_DIR / env.get_value("GUNICORN_ACCESSLOG_PATH"))
# accesslog = "-"  # stdout으로 출력
#
# # errorlog: Gunicorn 에러 로그
# # 워커 재시작, 설정 오류, 시스템 에러 등
# errorlog = str(BASE_DIR / env.get_value("GUNICORN_ERRORLOG_PATH"))
# errorlog = "-"  # stderr로 출력
#
# # loglevel: 로그 레벨
loglevel = env.get_value(
    "GUNICORN_LOGGING_LEVEL"
)  # debug, info, warning, error, critical
#
# # access_log_format: 액세스 로그 포맷
# # 어떤 정보를 로그에 남길지 정의
access_log_format = """{
                    "client_ip": "%(h)s",
                    "remote_logname": "%(l)s",
                    "remote_user": "%(u)s",
                    "timestamp": "%(t)s",
                    "request": "%(r)s",
                    "status_code": "%(s)s",
                    "response_size": "%(b)s",
                    "referer": "%(f)s",
                    "user_agent": "%(a)s",
                    "response_time_microseconds": "%(D)s"
                }"""

# capture_output: stdout/stderr을 로그 파일로 캡처
capture_output = False

# disable_redirect_access_to_syslog = True

# enable_stdio_inheritance: 자식 프로세스가 부모의 stdout/stderr 상속
enable_stdio_inheritance = True

# =====================================================
# 프로세스 관리
# =====================================================

# proc_name: 프로세스 이름 (ps 명령어에서 보이는 이름)
proc_name = env.get_value("GUNICORN_PROC_NAME")

# user, group: 워커가 실행될 사용자/그룹
# 보안상 root가 아닌 사용자로 실행 권장
# user = "django_gunicorn_worker"
# group = "django_gunicorn"

# tmp_upload_dir: 파일 업로드 임시 디렉토리
tmp_upload_dir = None

# secure_scheme_headers: HTTPS 감지를 위한 헤더
# 리버스 프록시(Nginx) 뒤에 있을 때 사용
# secure_scheme_headers = {
#     'X-FORWARDED-PROTOCOL': 'ssl',
#     'X-FORWARDED-PROTO': 'https',
#     'X-FORWARDED-SSL': 'on'
# }
