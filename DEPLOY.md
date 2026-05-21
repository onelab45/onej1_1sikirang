# Google Cloud Run 배포 가이드 문서 (DEPLOY.md)

식이랑 애플리케이션을 Docker 이미지 빌드 및 Google Cloud Run 서비스로 배포하고, SQLite 영구 보존용 볼륨 디렉터리를 구성하는 상세 절차입니다.

---

## 1. 사전 준비 단계

### 1) Google Cloud CLI 설치 및 로그인
- 로컬 개발 PC에 Google Cloud SDK(gcloud CLI)가 설치되어 있어야 합니다.
- 설치 후 터미널을 열고 인증을 진행합니다:
  ```bash
  # gcloud 인증 로그인
  gcloud auth login

  # 배포를 진행할 Google Cloud 프로젝트 설정
  gcloud config set project [GCP_PROJECT_ID]
  ```

### 2) GCP 필수 API 서비스 활성화
애플리케이션 배포와 빌드를 위해 아래 API 서비스들을 활성화합니다:
```bash
gcloud services enable run.googleapis.com \
                       cloudbuild.googleapis.com \
                       artifactregistry.googleapis.com \
                       compute.googleapis.com
```

---

## 2. SQLite 영구 저장소 볼륨 설정 (중요)

Cloud Run은 컨테이너가 재시작되면 데이터가 사라집니다. 화분 데이터를 보존하기 위해 Google Cloud Storage 버킷 또는 Cloud Filestore를 생성하여 컨테이너 경로에 마운트합니다. 
가장 비용 효율적이고 심플한 **Cloud Storage FUSE** 연동 마운트 방식 예시입니다:

1. **저장용 Storage 버킷 생성**:
   ```bash
   # asia-northeast3(서울) 리전에 식이랑 DB 보존용 버킷 생성
   gcloud storage buckets create gs://[GCP_PROJECT_ID]-sikirang-db --location=asia-northeast3
   ```
2. **볼륨 마운트 계획**:
   - 이 버킷은 Cloud Run 배포 시 컨테이너 내부의 `/mnt/data` 경로에 마운트됩니다.
   - 따라서 컨테이너 환경변수 `DATABASE_PATH`의 값을 `/mnt/data/db.sqlite3`로 주입합니다.

---

## 3. Cloud Run 배포 및 컨테이너 가동

### 첫 번째 배포 명령어 실행
소스 코드가 있는 프로젝트 루트 경로에서 아래 명령어를 실행하여 Cloud Build 및 Cloud Run 배포를 자동으로 동시에 진행합니다.

```bash
gcloud run deploy sikirang \
    --source . \
    --region asia-northeast3 \
    --allow-unauthenticated \
    --add-volume=name=sikirang-db-volume,type=cloud-storage,bucket=[GCP_PROJECT_ID]-sikirang-db \
    --add-volume-mount=volume=sikirang-db-volume,mount-path=/mnt/data \
    --set-env-vars="SECRET_KEY=yoursupersecuresecretkey","DEBUG=False","ALLOWED_HOSTS=*","DATABASE_PATH=/mnt/data/db.sqlite3"
```
*(주의: 배포 진행 중 'Artifact Registry' 리포지토리가 없다면 생성할 것인지 물어볼 수 있으며, `Y`를 입력해 자동 생성시킵니다.)*

---

## 4. 도메인 연동 및 환경변수(ALLOWED_HOSTS) 보완 업데이트

배포가 완료되면 gcloud CLI가 서비스 URL을 출력합니다.
예: `https://sikirang-xxxxxx-du.a.run.app`

### 1) URL 확인 후 환경변수 정비
보안을 강화하기 위해 `ALLOWED_HOSTS`와 `CSRF_TRUSTED_ORIGINS` 환경변수를 이 도메인 주소로 국한하여 새로 업데이트해 줍니다.
```bash
gcloud run services update sikirang \
    --region asia-northeast3 \
    --update-env-vars="ALLOWED_HOSTS=sikirang-xxxxxx-du.a.run.app","CSRF_TRUSTED_ORIGINS=https://sikirang-xxxxxx-du.a.run.app"
```

---

## 5. 향후 소스 코드 수정 후 재배포 절차

소스 코드를 수정한 후 재배포할 때는 소스 디렉터리에서 간단히 아래 업데이트 명령어로 배포를 재수행할 수 있습니다:
```bash
gcloud run deploy sikirang --source . --region asia-northeast3
```
이전 설정(볼륨 마운트 및 환경변수 등)은 그대로 유지되면서 코드 변경본만 빌드되어 신규 컨테이너 리비전으로 이관됩니다.
