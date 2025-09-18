# 샘플 만화 데이터

이 디렉토리에는 Comix Server 테스트를 위한 샘플 만화 데이터가 포함되어 있습니다.

## 📁 구조

```
sample-manga/
├── README.md                    # 이 파일
├── Series A/                    # 시리즈 A (아카이브 파일 예제)
│   ├── Volume 1.zip            # ZIP 아카이브 예제
│   ├── Volume 2.cbz            # CBZ 아카이브 예제
│   └── cover.jpg               # 시리즈 커버 이미지
├── Series B/                    # 시리즈 B (개별 이미지 파일 예제)
│   └── Chapter 01/
│       ├── page001.jpg
│       ├── page002.jpg
│       ├── page003.png
│       └── cover.jpg
├── Standalone Comics/           # 독립 만화들
│   ├── oneshot.cbz
│   └── special.zip
└── Mixed Content/               # 혼합 콘텐츠
    ├── archive.zip
    ├── image1.jpg
    └── image2.png
```

## 🎯 테스트 목적

각 디렉토리와 파일은 다음 기능을 테스트하기 위해 설계되었습니다:

### Series A (아카이브 테스트)
- **Volume 1.zip**: ZIP 파일 처리 테스트
- **Volume 2.cbz**: CBZ 파일 처리 테스트  
- **cover.jpg**: 직접 이미지 파일 테스트

### Series B (개별 파일 테스트)
- **Chapter 01/**: 디렉토리 탐색 테스트
- **page*.jpg**: JPEG 이미지 처리 테스트
- **page*.png**: PNG 이미지 처리 테스트

### Standalone Comics
- 독립적인 만화 아카이브 테스트
- 다양한 아카이브 형식 지원 확인

### Mixed Content
- 아카이브와 개별 파일이 혼재된 환경 테스트
- 파일 필터링 및 정렬 테스트

## 📝 참고사항

### 실제 이미지 파일 대신 더미 파일 사용

이 예제에서는 저작권 문제를 피하기 위해 실제 만화 이미지 대신 더미 파일을 사용합니다:

- **텍스트 파일**: 이미지 파일명으로 된 텍스트 파일
- **작은 크기**: 빠른 테스트를 위한 최소 크기
- **다양한 형식**: 지원되는 모든 이미지 형식 포함

### 실제 사용 시

실제 환경에서는:

1. 이 샘플 데이터를 삭제하고
2. 실제 만화 파일들을 복사하여 사용하세요

```bash
# 샘플 데이터 제거
rm -rf ~/manga/sample-manga

# 실제 만화 파일 복사
cp -r /path/to/your/manga/* ~/manga/
```

## 🧪 테스트 방법

### 1. 기본 테스트

```bash
# 서버 시작
comix-server

# 다른 터미널에서 테스트
curl http://localhost:31257/manga/

# 시리즈 A 목록
curl "http://localhost:31257/manga/Series%20A/"

# ZIP 파일 내용
curl "http://localhost:31257/manga/Series%20A/Volume%201.zip"
```

### 2. 자동 테스트

```bash
# 테스트 클라이언트 실행
python examples/basic-setup/test-client.py
```

### 3. AirComix 앱 테스트

1. AirComix 앱에서 서버 연결
2. Series A, Series B 탐색
3. 이미지 로딩 확인

## 🔧 커스터마이징

### 추가 테스트 데이터 생성

```bash
# 새 시리즈 디렉토리 생성
mkdir -p "~/manga/My Series/Volume 1"

# 더미 이미지 파일 생성
for i in {1..10}; do
    echo "Page $i content" > "~/manga/My Series/Volume 1/page$(printf %03d $i).jpg"
done

# ZIP 아카이브 생성
cd "~/manga/My Series"
zip -r "Volume 1.zip" "Volume 1/"
```

### 다양한 파일 형식 테스트

```bash
# 지원되는 모든 이미지 형식 생성
formats=("jpg" "jpeg" "png" "gif" "bmp" "tif" "tiff")
for fmt in "${formats[@]}"; do
    echo "Test image" > "test.$fmt"
done

# 지원되는 아카이브 형식 테스트
# (실제 RAR 파일은 unrar 도구가 필요)
```

## ⚠️ 주의사항

- 이 샘플 데이터는 테스트 목적으로만 사용하세요
- 실제 만화 파일을 사용할 때는 저작권을 준수하세요
- 대용량 파일 테스트 시 시스템 리소스를 고려하세요

## 🤝 기여

더 나은 테스트 데이터나 시나리오가 있다면:

1. GitHub Issues에 제안해주세요
2. Pull Request로 기여해주세요
3. 실제 사용 사례를 공유해주세요