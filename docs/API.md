# API 문서

Comix Server는 AirComix iOS 앱과 호환되는 RESTful API를 제공합니다.

## 기본 정보

- **Base URL**: `http://localhost:31257`
- **Content-Type**: `text/plain` (목록), `image/*` (이미지)
- **인증**: 없음 (로컬 네트워크 사용 가정)

## 엔드포인트

### 1. 루트 디렉토리 정보

만화 컬렉션의 루트 디렉토리 이름을 반환합니다.

```http
GET /
```

#### 응답

```
Status: 200 OK
Content-Type: text/plain

manga
```

#### 예제

```bash
curl http://localhost:31257/
```

---

### 2. 서버 정보

서버의 기능 및 버전 정보를 반환합니다.

```http
GET /welcome.102
```

#### 응답

```
Status: 200 OK
Content-Type: text/plain

allowDownload=True
allowImageProcess=True
Comix Server Python Port - FastAPI 기반 만화 스트리밍 서버
```

#### 예제

```bash
curl http://localhost:31257/welcome.102
```

---

### 3. 헬스 체크

서버의 상태를 확인합니다.

```http
GET /health
```

#### 응답

```
Status: 200 OK
Content-Type: text/plain

status=healthy
manga_directory=/var/lib/comix/manga
debug_mode=false
service=comix-server
```

#### 오류 응답

```
Status: 503 Service Unavailable
Content-Type: text/plain

Service unavailable
```

#### 예제

```bash
curl http://localhost:31257/health
```

---

### 4. 만화 콘텐츠 처리

만화 디렉토리 내의 모든 콘텐츠를 처리하는 통합 엔드포인트입니다.

```http
GET /manga/{path}
```

#### 매개변수

- `path` (string): 요청할 경로 (URL 인코딩 필요)

#### 동작 방식

요청된 경로의 타입에 따라 다르게 동작합니다:

1. **디렉토리**: 파일 및 하위 디렉토리 목록 반환
2. **아카이브 파일**: 아카이브 내 이미지 파일 목록 반환
3. **이미지 파일**: 이미지 스트리밍
4. **아카이브 내 이미지**: 아카이브에서 이미지 추출 후 스트리밍

---

#### 4.1. 디렉토리 목록

디렉토리의 파일 및 하위 디렉토리 목록을 반환합니다.

##### 요청

```http
GET /manga/
GET /manga/Series%20A/
```

##### 응답

```
Status: 200 OK
Content-Type: text/plain

Series A
Series B
standalone.jpg
collection.zip
```

##### 필터링 규칙

다음 파일들은 목록에서 제외됩니다:
- 숨김 파일 (`.`으로 시작)
- 시스템 파일 (`@eaDir`, `Thumbs.db`, `.DS_Store`)
- 시스템 디렉토리 (`__MACOSX`)
- 지원되지 않는 파일 형식

##### 예제

```bash
# 루트 디렉토리 목록
curl http://localhost:31257/manga/

# 특정 시리즈 디렉토리
curl "http://localhost:31257/manga/Series%20A/"

# 중첩 디렉토리
curl "http://localhost:31257/manga/Series%20A/Volume%201/"
```

---

#### 4.2. 아카이브 파일 목록

아카이브 파일 내의 이미지 파일 목록을 반환합니다.

##### 지원 형식

- ZIP, CBZ
- RAR, CBR (unrar 설치 필요)

##### 요청

```http
GET /manga/series1.zip
GET /manga/Series%20A/Volume%201.cbz
```

##### 응답

```
Status: 200 OK
Content-Type: text/plain

page001.jpg
page002.jpg
page003.png
cover.jpg
```

##### 정렬

파일명 기준 자연 정렬 (숫자 순서 고려)

##### 예제

```bash
# ZIP 파일 내용
curl http://localhost:31257/manga/series1.zip

# CBZ 파일 내용
curl "http://localhost:31257/manga/Series%20A/Volume%201.cbz"

# 경로에 공백이 있는 경우
curl "http://localhost:31257/manga/My%20Series/Vol%2001.zip"
```

---

#### 4.3. 직접 이미지 스트리밍

파일 시스템의 이미지 파일을 직접 스트리밍합니다.

##### 지원 형식

- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- GIF (`.gif`)
- BMP (`.bmp`)
- TIFF (`.tif`, `.tiff`)

##### 요청

```http
GET /manga/cover.jpg
GET /manga/Series%20A/artwork.png
```

##### 응답

```
Status: 200 OK
Content-Type: image/jpeg
Content-Length: 245760

[이미지 바이너리 데이터]
```

##### 헤더

- `Content-Type`: 이미지 MIME 타입
- `Content-Length`: 파일 크기 (바이트)
- `Cache-Control`: 캐싱 정책

##### 예제

```bash
# 이미지 다운로드
curl http://localhost:31257/manga/cover.jpg -o cover.jpg

# 이미지 정보만 확인
curl -I http://localhost:31257/manga/cover.jpg

# 스트리밍으로 표시
curl http://localhost:31257/manga/cover.jpg | display
```

---

#### 4.4. 아카이브 내 이미지 스트리밍

아카이브 파일에서 특정 이미지를 추출하여 스트리밍합니다.

##### 요청

```http
GET /manga/series1.zip/page001.jpg
GET /manga/Series%20A/Volume%201.cbz/cover.png
```

##### 응답

```
Status: 200 OK
Content-Type: image/jpeg
Content-Length: 156432

[이미지 바이너리 데이터]
```

##### 경로 형식

`/manga/{archive_path}/{image_path}`

- `archive_path`: 아카이브 파일 경로
- `image_path`: 아카이브 내 이미지 파일 경로

##### 예제

```bash
# ZIP 파일에서 이미지 추출
curl "http://localhost:31257/manga/series1.zip/page001.jpg" -o page001.jpg

# CBZ 파일에서 커버 이미지
curl "http://localhost:31257/manga/Series%20A/Volume%201.cbz/cover.jpg" -o cover.jpg

# RAR 파일에서 이미지 (unrar 필요)
curl "http://localhost:31257/manga/series1.rar/page001.jpg" -o page001.jpg
```

---

## 오류 응답

### HTTP 상태 코드

| 코드 | 설명 | 예시 |
|------|------|------|
| 200 | 성공 | 정상적인 응답 |
| 400 | 잘못된 요청 | 지원되지 않는 파일 형식 |
| 403 | 접근 거부 | 경로 순회 공격 시도 |
| 404 | 찾을 수 없음 | 존재하지 않는 파일/디렉토리 |
| 500 | 서버 오류 | 내부 서버 오류 |
| 503 | 서비스 불가 | 서버 상태 불량 |

### 오류 응답 형식

#### 프로덕션 모드

```
Status: 404 Not Found
Content-Type: text/plain

파일 또는 디렉토리를 찾을 수 없습니다
```

#### 디버그 모드

```
Status: 404 Not Found
Content-Type: application/json

{
  "error": "파일 또는 디렉토리를 찾을 수 없습니다",
  "detail": "/path/to/missing/file",
  "status_code": 404,
  "path": "/manga/missing.jpg",
  "method": "GET"
}
```

---

## 문자 인코딩

### 지원 인코딩

- UTF-8 (기본)
- EUC-KR (한국어)
- Shift-JIS (일본어)
- CP949 (한국어 확장)

### 자동 변환

아카이브 파일 내의 파일명이 UTF-8이 아닌 경우 자동으로 감지하여 변환합니다.

```
원본: ÇÑ±Û.jpg (EUC-KR)
변환: 한글.jpg (UTF-8)
```

---

## 성능 고려사항

### 캐싱

- 이미지 파일: 브라우저 캐싱 활성화
- 디렉토리 목록: 캐싱 비활성화 (동적 콘텐츠)

### 스트리밍

- 큰 파일: 청크 단위 스트리밍
- 아카이브: 메모리 효율적 추출

### 동시 연결

- 기본: 워커당 1000개 연결
- 조정 가능: Gunicorn 설정

---

## 보안

### 경로 검증

모든 경로는 다음과 같이 검증됩니다:

```python
# 허용되지 않는 패턴
../../../etc/passwd  # 경로 순회
/absolute/path       # 절대 경로
file\x00name        # NULL 바이트
```

### 파일 타입 검증

- 확장자 기반 검증
- MIME 타입 확인
- 악성 파일 차단

---

## 클라이언트 구현 예제

### Python

```python
import requests

class ComixClient:
    def __init__(self, base_url="http://localhost:31257"):
        self.base_url = base_url
    
    def get_directory_list(self, path=""):
        """디렉토리 목록 조회"""
        url = f"{self.base_url}/manga/{path}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text.strip().split('\n')
        return []
    
    def download_image(self, path, output_file):
        """이미지 다운로드"""
        url = f"{self.base_url}/manga/{path}"
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        return False

# 사용 예제
client = ComixClient()
files = client.get_directory_list("Series A/")
client.download_image("Series A/Volume 1.zip/page001.jpg", "page001.jpg")
```

### JavaScript

```javascript
class ComixClient {
    constructor(baseUrl = 'http://localhost:31257') {
        this.baseUrl = baseUrl;
    }
    
    async getDirectoryList(path = '') {
        const response = await fetch(`${this.baseUrl}/manga/${path}`);
        if (response.ok) {
            const text = await response.text();
            return text.trim().split('\n');
        }
        return [];
    }
    
    getImageUrl(path) {
        return `${this.baseUrl}/manga/${path}`;
    }
    
    async checkHealth() {
        const response = await fetch(`${this.baseUrl}/health`);
        return response.ok;
    }
}

// 사용 예제
const client = new ComixClient();
const files = await client.getDirectoryList('Series A/');
const imageUrl = client.getImageUrl('Series A/Volume 1.zip/page001.jpg');
```

### cURL 스크립트

```bash
#!/bin/bash
# Comix Server API 테스트 스크립트

BASE_URL="http://localhost:31257"

# 서버 상태 확인
echo "=== 서버 상태 확인 ==="
curl -s "$BASE_URL/health"
echo -e "\n"

# 루트 디렉토리 목록
echo "=== 루트 디렉토리 ==="
curl -s "$BASE_URL/manga/"
echo -e "\n"

# 특정 시리즈 목록
echo "=== 시리즈 목록 ==="
curl -s "$BASE_URL/manga/Series%20A/"
echo -e "\n"

# 아카이브 내용
echo "=== 아카이브 내용 ==="
curl -s "$BASE_URL/manga/Series%20A/Volume%201.zip"
echo -e "\n"

# 이미지 다운로드
echo "=== 이미지 다운로드 ==="
curl -s "$BASE_URL/manga/Series%20A/Volume%201.zip/page001.jpg" -o "page001.jpg"
echo "이미지 저장 완료: page001.jpg"
```

---

## AirComix 앱 호환성

### 프로토콜 호환성

이 API는 기존 PHP comix-server와 100% 호환되므로 AirComix iOS 앱에서 바로 사용할 수 있습니다.

### 앱 설정

1. AirComix 앱 실행
2. 설정 → 서버 추가
3. 서버 주소: `http://your-server-ip:31257`
4. 연결 테스트 후 사용

### 지원 기능

- ✅ 디렉토리 탐색
- ✅ 아카이브 파일 읽기
- ✅ 이미지 스트리밍
- ✅ 북마크 지원
- ✅ 읽기 진행률 저장