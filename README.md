# 식이랑 (Sikirang)

식이랑은 화분의 무게 측정을 통해 식물에게 물을 주어야 하는 시점을 예측하고 효율적으로 관리할 수 있도록 돕는 모바일 우선 웹 애플리케이션입니다.

---

## 1. 프로젝트 개요
- **설명**: 화분 무게 변화 패턴 분석으로 최적의 물주기 시점을 D-Day 형식으로 안내
- **기술 스택**: Python, Django, SQLite, HTML/CSS/JS (Django Template)
- **무게 단위**: `g` 통일
- **로그인 방식**: 브라우저 세션 기반 (MVP 개발 중)
- **디자인 컨셉**: 나무색, 황토색 등 자연 톤의 심플하고 세련된 모바일 UI

---

## 2. 1단계 완료 내용
- **가상환경 설정**: venv 구축 및 Django(v4.2.30) 패키지 설치
- **Django 설정**: 프로젝트(`config`) 및 앱(`plants`) 생성, 한국어 설정(`ko-kr`) 및 시간대(`Asia/Seoul`) 설정 완료
- **데이터베이스 모델 구현**: 
  - `Plant`: 화분 정보(현재 무게, 하루 무게 감소량, 한계 무게, 측정 시간 등) 및 오늘 예상 무게, 남은 일수, 다음 물주기 예정일 계산 로직 탑재
  - `WaterLog`: 물주기 이력(물 준 시각, 물 준 후 무게, 메모) 관리
- **Django Admin 설정**: 목록 뷰 및 검색/필터 기능 설정, 모델 인스턴스에 대한 한국어 표시 완비
- **형상 관리**: `.gitignore` 작성 및 최초 Git 커밋 등록

---

## 3. 개발 환경 구성 및 실행 방법

### 가상환경 활성화

**Windows (PowerShell):**
```powershell
# 가상환경 활성화
.\venv\Scripts\Activate.ps1
```

**Mac / Linux (Bash/Zsh):**
```bash
# 가상환경 활성화
source venv/bin/activate
```

### 필수 패키지 설치
```bash
pip install -r requirements.txt
```

### 서버 실행 및 접속
```bash
# 데이터베이스 마이그레이션 적용 (초기 설정 시 자동 적용됨)
python manage.py migrate

# 로컬 개발 서버 실행
python manage.py runserver
```
- 브라우저에서 `http://127.0.0.1:8000/` 로 접속

### 관리자(Superuser) 계정 생성
관리자 기능을 사용하기 위해 아래 명령어를 실행하여 계정을 생성합니다:
```bash
python manage.py createsuperuser
```
생성 후 `http://127.0.0.1:8000/admin/` 에서 로그인하여 등록된 화분 및 물주기 기록을 관리할 수 있습니다.
