# GitHub Secrets 확인 가이드

## 현재 상황
"buildUsername and password required" 오류가 계속 발생하고 있습니다.

## 즉시 확인해야 할 사항

### 1. GitHub Secrets 이름 확인
GitHub 저장소의 **Settings > Secrets and variables > Actions**에서 정확히 다음 이름으로 설정되어 있는지 확인:

```
✅ DOCKERHUB_USERNAME (정확한 이름)
✅ DOCKERHUB_TOKEN (정확한 이름)
```

**주의**: 다음과 같은 이름들은 작동하지 않습니다:
- ❌ `DOCKER_PASSWORD`
- ❌ `DOCKER_USERNAME`
- ❌ `DOCKER_TOKEN`
- ❌ `dockerhub_username` (소문자)

### 2. 값 확인
#### DOCKERHUB_USERNAME
- Docker Hub 로그인 시 사용하는 사용자명
- 이메일 주소가 아닌 사용자명
- 예: `myusername` (❌ `myemail@example.com`)

#### DOCKERHUB_TOKEN
- Docker Hub에서 생성한 액세스 토큰
- `dckr_pat_` 또는 `dckr_` 로 시작
- 비밀번호가 아닌 토큰!

### 3. 토큰 재생성 (권장)
기존 토큰이 문제가 있을 수 있으므로 새로 생성:

1. https://hub.docker.com 로그인
2. **Account Settings** → **Security**
3. 기존 토큰 삭제 (있다면)
4. **New Access Token** 클릭
5. 설정:
   - **Description**: `github-actions-comix`
   - **Access permissions**: 
     - ✅ **Read**
     - ✅ **Write**
6. **Generate** 클릭
7. 생성된 토큰을 즉시 복사
8. GitHub Secrets의 `DOCKERHUB_TOKEN`에 붙여넣기

### 4. 로컬 테스트
토큰이 올바른지 로컬에서 확인:

```bash
# 토큰 테스트
echo "YOUR_TOKEN_HERE" | docker login -u YOUR_USERNAME --password-stdin

# 성공하면 다음 메시지가 나타남:
# Login Succeeded
```

### 5. GitHub Actions 로그 확인
1. **Actions** 탭 클릭
2. 최신 워크플로우 실행 클릭
3. **build** 작업 클릭
4. **Debug - Check secrets** 단계 확인:
   - Username length가 0이 아닌지
   - Token length가 0이 아닌지

### 6. 일반적인 실수들

#### 실수 1: 잘못된 Secret 이름
```yaml
# ❌ 잘못된 예
password: ${{ secrets.DOCKER_PASSWORD }}

# ✅ 올바른 예
password: ${{ secrets.DOCKERHUB_TOKEN }}
```

#### 실수 2: 비밀번호 사용
```
❌ Docker Hub 계정 비밀번호 사용
✅ Docker Hub 액세스 토큰 사용
```

#### 실수 3: 이메일 주소 사용
```
❌ DOCKER_USERNAME: myemail@example.com
✅ DOCKER_USERNAME: myusername
```

### 7. 긴급 해결책
위 방법들이 모두 실패하면:

1. **모든 Secrets 삭제**
2. **새 Docker Hub 토큰 생성**
3. **Secrets 다시 생성**:
   - `DOCKERHUB_USERNAME`: Docker Hub 사용자명
   - `DOCKERHUB_TOKEN`: 새로 생성한 토큰

### 8. 확인 체크리스트
- [ ] GitHub Secrets 이름이 정확함 (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`)
- [ ] Docker Hub 사용자명이 정확함 (이메일 아님)
- [ ] 액세스 토큰이 최신이고 올바름
- [ ] 토큰 권한이 Read, Write 포함
- [ ] 로컬에서 토큰 테스트 성공
- [ ] GitHub Actions 디버그 로그에서 길이가 0이 아님

모든 항목을 확인한 후에도 문제가 지속되면 GitHub Issues에 보고해주세요.