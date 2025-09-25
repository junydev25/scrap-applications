# Changelog

모든 변경 사항은 이 파일에서 관리됩니다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)를 따릅니다.  
이 프로젝트는 [Semantic Versioning](https://semver.org/lang/ko/)을 사용합니다.

## [Unreleased]

### Added

- API 서버 추가(SSR -> SPA)
    - `djangorestframework`
    - `Vue.js`

### Changed

- Session Login을 JWT로 변경

### Deprecated

### Removed

### Fixed

### Security

- [Docker] 외부에서 접근이 가능하면 안되는 접근이 가능
    - `Prometheus`
    - `CAdvisor`
    - `Oracle DB Exporter`
- [Environment] 환경변수가 `Dockerfile`과 `docker-compose.yml`에 노출

## [1.1.0] - 2025-09-25

### Added

- Embedded Database(`SQLite3`)를 외부 DataBase(`Oracle`)로 분리

## [1.0.0] - 2025-09-24

### Added

- `v1.0.0`의 특징
    - 동기 서버
    - SSR(Server Side Rendering)로 구성
        - Django Template 사용
        - `index.html`: `login.html` 또는 `approvals.html`로 리다이렉션
        - `login.html`: 로그인 페이지
        - `approvals.html`: 신청 내역 및 승인(거부) 페이지
- Application 추가
    - Web Server => `Nginx`
    - Web Application Server(Web Server Gateway Interface) => `Gunicorn`
        - Backend Framework => `Django`
    - Database => Django Embedded DB(`SQLite3`)
    - Monitoring => `Prometheus` / `Node Exporter`(`CAdvisor`) / `Grafana`
- Local 및 Docker에서 모두 수행 가능하도록 작성
    - Local에서는 `Node Exporter`로 수행해야 시스템 메트릭을 얻을 수 있지만 Docker에서는 `CAdvisor`로 시스템 메트릭 수집