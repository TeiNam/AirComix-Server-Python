# Synology Container Manager 배포

## 설치

1. `docker-compose.yml` 과 `.env.example` 을 NAS 폴더에 올린다 (예: `/volume1/docker/aircomix`)
2. `.env.example` 을 `.env` 로 복사하고 값을 채운다
3. Container Manager > 프로젝트 > 생성 > 경로 선택 > 기존 `docker-compose.yml` 업로드
4. 빌드 시작

## 구버전(`aircomix-server-py.json`)에서 넘어올 때

기존 컨테이너 설정에서 반드시 바뀌어야 하는 것들이다.

### 1. 인증 환경변수 이름 — 중요

구버전 설정은 이렇게 되어 있다.

```
AUTH_ENABLED=true
AUTH_PASSWORD=...
```

이 두 키는 **서버가 읽지 않는다.** 설정 모델의 `env_prefix` 가 `COMIX_` 라서
`COMIX_` 로 시작하는 키만 인식한다. 즉 인증을 켠 줄 알았지만 실제로는 꺼진 채로
동작해 왔다. 올바른 이름은 다음과 같다.

```
COMIX_ENABLE_AUTH=true
COMIX_AUTH_PASSWORD=...   # 6자 이상
```

### 2. 만화 볼륨을 읽기 전용으로

구버전은 `/comix` 를 `rw` 로 마운트했다. 서버는 만화 디렉토리에 쓸 일이 없다.

```
/volume1/comix → /comix (ro)
```

### 3. 썸네일 캐시 볼륨 추가 — 신규

만화 볼륨이 읽기 전용이 되면서 썸네일 캐시가 갈 곳이 필요하다. 이 볼륨이 없으면
캐시를 쓰지 못해 매번 다시 생성한다.

```
aircomix-cache → /app/cache
```

### 4. 이미지 태그 고정

구버전은 `teinam/aircomix-server:latest` 를 쓴다. `latest` 는 main 에 머지될
때마다 preview 빌드로 덮이므로, 정식 버전을 고정하는 편이 안전하다.

```
teinam/aircomix-server:1.0.2
```

### 5. 넘길 필요 없는 것

구버전 JSON 의 `PATH`, `LANG`, `GPG_KEY`, `PYTHON_VERSION`, `PYTHON_SHA256`,
`PYTHONPATH` 는 이미지가 자체적으로 설정한다. `cmd` 도 마찬가지로 이미지의
기본 명령을 그대로 쓰면 된다.

## 확인

```bash
curl http://<NAS-IP>:31257/health   # status=healthy
curl http://<NAS-IP>:31257/         # comix
```

## 업그레이드

`docker-compose.yml` 의 이미지 태그를 새 버전으로 바꾸고 프로젝트를 다시 빌드한다.
