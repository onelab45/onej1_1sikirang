# 1. Base 이미지 지정: 가볍고 최신인 python:3.12-slim 사용
FROM python:3.12-slim

# 2. 필수 환경변수 설정 (Python 출력 버퍼 방지 및 바이트코드 자동생성 방지)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 3. 작업 디렉터리 생성 및 설정
WORKDIR /app

# 4. 의존성 패키지 목록을 먼저 복사 (도커 빌드 캐시 최적화)
COPY requirements.txt /app/

# 5. pip 업그레이드 및 패키지 설치
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. 소스 코드 전체 복사
COPY . /app/

# 7. 배포 시 정적 자원 최적화 빌드를 위해 collectstatic 실행
#    (이때 settings.py의 SECRET_KEY와 임시 환경변수들을 주입하여 실행 오류를 방지함)
RUN SECRET_KEY=django-insecure-build-time-dummy-key \
    DEBUG=False \
    ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput

# 8. Cloud Run 기본 수신 포트인 8080 포트 노출
EXPOSE 8080

# 9. 컨테이너 구동 시점의 Entrypoint 명령어 설정
#    - 실행 시점에 데이터베이스 마이그레이션(migrate)을 수행
#    - Gunicorn을 구동하며 Cloud Run이 주입하는 $PORT 환경변수로 바인딩
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"]
