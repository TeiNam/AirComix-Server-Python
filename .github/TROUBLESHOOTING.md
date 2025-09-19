# GitHub Actions 문제 해결 가이드

## "buildUsername and password required" 오류 해결

이 오류는 Docker Hub 인증 정보가 올바르게 설정되지 않았을 때 발생합니다.

### 1. GitHub Secrets 확인

GitHub 저장소의 **Settings > Secrets and variables > Actions**에서 다음을 확인하세요:

#### 필수 Secrets
- ✅ `DOCKERHUB_USERNAME`: Docker Hub 사용자명
- ✅ `DOCKERHUB_TOKEN`: Docker Hub 액세스 토큰

#### 확인 방법
```bash
# GitHub CLI 사용 (선택사항)
gh secret list

# 또는 웹 인터페이스에서 확인
# Settings > Secrets and variables > Actions
```

### 2. Docker Hub 액세스 토큰 재생성

기존 토큰이 만료되었거나 권한이 부족할 수 있습니다.

#### 단계:
1. [Docker Hub](https://hub.docker.com) 로그인
2. **Account Settings > Security**
3. 기존 토큰 삭제 (있다면)
4. **New Access Token** 클릭
5. 설정:
   - **Description**: `github-actions-comix-server`
   - **Permissions**: 
     - ✅ **Read**
     - ✅ **Write** 
     - ✅ **Delete** (선택사항)
6. 생성된 토큰을 `DOCKERHUB_TOKEN`에 업데이트

### 3. 일반적인 문제들

#### 문제 1: 잘못된 사용자명
```yaml
# ❌ 잘못된 예
username: myemail@example.com

# ✅ 올바른 예  
username: mydockerhubusername
```

#### 문제 2: 비밀번호 사용 (토큰 대신)
```yaml
# ❌ 잘못된 예
password: mypassword123

# ✅ 올바른 예
password: dckr_pat_1234567890abcdef...
```

#### 문제 3: 공백이나 특수문자
- 사용자명과 토큰에 앞뒤 공백이 없는지 확인
- 토큰을 복사할 때 전체가 복사되었는지 확인

### 4. 디버깅 단계

#### 로컬에서 테스트
```bash
# Docker Hub 로그인 테스트
echo "YOUR_TOKEN" | docker login docker.io -u YOUR_USERNAME --password-stdin

# 성공하면 다음과 같은 메시지가 나타남
# Login Succeeded
```

#### GitHub Actions 로그 확인
1. **Actions** 탭에서 실패한 워크플로우 클릭
2. **build** 작업 클릭
3. **Log in to Docker Hub** 단계 확인
4. 오류 메시지 분석

### 5. 워크플로우 수정 (필요시)

현재 워크플로우가 올바르게 설정되어 있는지 확인:

```yaml
- name: Log in to Docker Hub
  if: github.event_name != 'pull_request'
  uses: docker/login-action@v3
  with:
    registry: docker.io
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

### 6. 권한 확인

#### Repository 권한
- 저장소에 **Actions** 권한이 활성화되어 있는지 확인
- **Settings > Actions > General > Actions permissions**

#### Docker Hub 권한
- 토큰이 해당 저장소에 대한 **Write** 권한을 가지고 있는지 확인

### 7. 대안 방법

#### GitHub Container Registry 사용
Docker Hub 대신 GitHub Container Registry를 사용할 수 있습니다:

```yaml
- name: Log in to GitHub Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

### 8. 자주 발생하는 오류 메시지

| 오류 메시지 | 원인 | 해결책 |
|-------------|------|--------|
| `unauthorized: authentication required` | 잘못된 인증 정보 | 사용자명/토큰 재확인 |
| `denied: requested access to the resource is denied` | 권한 부족 | 토큰 권한 확인 |
| `repository does not exist` | 잘못된 저장소 이름 | 사용자명 확인 |
| `invalid username/password` | 비밀번호 사용 | 액세스 토큰 사용 |

### 9. 연락처

문제가 계속 발생하면:
1. GitHub Issues에 문제 보고
2. 워크플로우 로그 첨부
3. 사용한 설정 정보 공유 (민감한 정보 제외)

---

💡 **팁**: 보안을 위해 정기적으로 액세스 토큰을 갱신하세요!