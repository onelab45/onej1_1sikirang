# 식이랑 (Sikirang) 🌱

식이랑은 화분의 무게 측정을 통해 식물에게 물을 주어야 하는 시점을 예측하고 효율적으로 관리할 수 있도록 돕는 모바일 우선 웹 애플리케이션입니다.

---

## 1. 주요 기능
- **닉네임 및 PIN 번호 로그인**: 사용자는 닉네임과 4자리 PIN 번호로 독립적으로 가입하고 세션(7일간 유지) 로그인할 수 있습니다.
- **철저한 사용자 격리**: 데이터베이스 수준에서 사용자별 데이터 및 화분 이력이 완벽히 분리되어 다른 유저의 데이터 접근을 차단합니다.
- **물주기 D-Day 자동 예측**: 화분의 무게 감소 패턴을 분석하여 물주기 예정일과 남은 D-Day를 4가지 상태 배지 색상으로 시각화합니다.
- **화분 통합 이력 로그**: 화분 등록, 물주기("물 줬어요"), 수정 이벤트 등을 한눈에 모니터링할 수 있는 타임라인을 제공합니다.
- **월간 캘린더**: 사용자가 키우는 모든 화분의 다음 예정일을 달력 형식으로 직관적으로 모출합니다.

---

## 2. 개발 및 배포 기술 스택
- **Backend/Core**: Python 3.12, Django 4.2.x
- **Database**: SQLite (Cloud Run의 영구 저장소 볼륨 마운트 연동 대응)
- **Frontend**: Django Template Engine, HTML, Vanilla CSS (모바일 우선 반응형 스타일링)
- **Production Server**: Gunicorn (WSGI) 및 WhiteNoise (정적 자원 압축/캐싱)
- **Deployment Platform**: Google Cloud Run (Docker Containerization)

---

## 3. 환경변수 설정 목록 (.env)
로컬 개발 및 배포 환경에서 아래 환경변수를 참조합니다:

| 환경변수 키 | 설명 | 기본값 / 예시 |
| :--- | :--- | :--- |
| `SECRET_KEY` | Django 세션/서명 암호화 비밀키 | `django-insecure-...` (로컬 fallback) |
| `DEBUG` | 디버그 모드 활성화 여부 | `True` (로컬) / `False` (운영배포) |
| `ALLOWED_HOSTS` | 웹 서비스를 허용할 도메인 주소 목록 | `localhost,127.0.0.1` |
| `CSRF_TRUSTED_ORIGINS` | CSRF 신뢰할 수 있는 도메인 리스트 | `http://localhost:8000` |
| `DATABASE_PATH` | SQLite 데이터베이스 저장 절대 경로 | `db.sqlite3` / `/mnt/data/db.sqlite3` |

---

## 4. 로컬 개발 환경 실행 방법

### 가상환경 활성화 및 패키지 설치
**Windows (PowerShell):**
```powershell
# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 의존성 패키지 설치
pip install -r requirements.txt
```

**Mac / Linux (Bash):**
```bash
# 가상환경 활성화
source venv/bin/activate

# 의존성 패키지 설치
pip install -r requirements.txt
```

### 환경변수 파일 준비 (.env)
루트 경로에 `.env` 파일을 만들고 로컬 설정을 적어줍니다 (샘플 제공: `.env.example`).
```ini
SECRET_KEY=django-insecure-local-dev-secret-key-1234
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000
DATABASE_PATH=db.sqlite3
```

### 데이터베이스 마이그레이션 및 관리자 생성
```bash
# 마이그레이션 반영
python manage.py migrate

# 관리자(Superuser) 계정 생성
python manage.py createsuperuser
```

### 개발 서버 가동 및 테스트 실행
```bash
# 로컬 개발 서버 실행
python manage.py runserver

# 단위 테스트 구동
python manage.py test --noinput
```
- 로컬 웹 서비스 접속: `http://127.0.0.1:8000/`
- 관리자 어드민 페이지 접속: `http://127.0.0.1:8000/admin/`

---

## 5. Google Cloud Run 운영 서버 배포 안내
Google Cloud Run 배포를 위한 가이드는 별도의 **[DEPLOY.md](file:///d:/source/sikirang/DEPLOY.md)** 파일에 상세히 기술되어 있습니다.
- 영구 보존용 볼륨 마운트 설정(SQLite)
- Cloud Build를 통한 도커 이미지 빌드 및 Artifact Registry 푸시
- Cloud Run 서비스 배포 환경변수 주입 안내
