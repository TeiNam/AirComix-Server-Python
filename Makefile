# Comix Server Makefile
# Docker 운영을 위한 편리한 단축 명령어 제공

.PHONY: help build build-dev run run-dev stop restart logs status clean test setup

# 기본 타겟
help: ## 도움말 메시지 표시
	@echo "Comix Server Docker 명령어"
	@echo "=========================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "사용 예시:"
	@echo "  make setup     # 초기 설정"
	@echo "  make run       # 프로덕션 서버 시작"
	@echo "  make run-dev   # 개발 서버 시작"
	@echo "  make logs      # 로그 확인"

# =============================================================================
# 빌드 명령어 (Build Commands)
# =============================================================================

build: ## 프로덕션 Docker 이미지 빌드
	@echo "🔨 프로덕션 이미지 빌드 중..."
	@cd docker && docker-compose build --no-cache
	@echo "✅ 빌드 완료"

build-dev: ## 개발용 Docker 이미지 빌드
	@echo "🔨 개발용 이미지 빌드 중..."
	@cd docker && docker-compose -f docker-compose.dev.yml build --no-cache
	@echo "✅ 개발용 빌드 완료"

build-quick: ## 캐시를 사용한 빠른 빌드
	@echo "⚡ 빠른 빌드 중..."
	@cd docker && docker-compose build
	@echo "✅ 빠른 빌드 완료"

# =============================================================================
# 실행 명령어 (Run Commands)
# =============================================================================

run: ## 프로덕션 서비스 시작 (백그라운드)
	@echo "🚀 프로덕션 서버 시작 중..."
	@cd docker && docker-compose up -d
	@echo "✅ 서버가 백그라운드에서 실행 중입니다"
	@echo "🌐 접속 주소: http://localhost:31257"

run-dev: ## 개발 서비스 시작 (핫 리로드)
	@echo "🚀 개발 서버 시작 중..."
	@cd docker && docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ 개발 서버가 핫 리로드와 함께 실행 중입니다"
	@echo "🌐 접속 주소: http://localhost:31257"
	@echo "🐛 디버그 포트: 5678"

run-fg: ## 프로덕션 서비스 시작 (포그라운드)
	@echo "🚀 프로덕션 서버 시작 중 (포그라운드)..."
	@cd docker && docker-compose up

run-dev-fg: ## 개발 서비스 시작 (포그라운드)
	@echo "🚀 개발 서버 시작 중 (포그라운드)..."
	@cd docker && docker-compose -f docker-compose.dev.yml up

run-build: ## 빌드 후 프로덕션 서비스 시작
	@echo "🔨 빌드 후 서버 시작 중..."
	@cd docker && docker-compose up -d --build
	@echo "✅ 빌드 및 시작 완료"

# =============================================================================
# 관리 명령어 (Management Commands)
# =============================================================================

stop: ## 모든 서비스 중지
	@echo "🛑 서비스 중지 중..."
	@cd docker && docker-compose down
	@echo "✅ 프로덕션 서비스 중지됨"

stop-dev: ## 개발 서비스 중지
	@echo "🛑 개발 서비스 중지 중..."
	@cd docker && docker-compose -f docker-compose.dev.yml down
	@echo "✅ 개발 서비스 중지됨"

stop-all: ## 모든 서비스 중지 (프로덕션 + 개발)
	@echo "🛑 모든 서비스 중지 중..."
	@cd docker && docker-compose down
	@cd docker && docker-compose -f docker-compose.dev.yml down
	@echo "✅ 모든 서비스 중지됨"

restart: ## 프로덕션 서비스 재시작
	@echo "🔄 서비스 재시작 중..."
	@cd docker && docker-compose restart
	@echo "✅ 재시작 완료"

restart-dev: ## 개발 서비스 재시작
	@echo "🔄 개발 서비스 재시작 중..."
	@cd docker && docker-compose -f docker-compose.dev.yml restart
	@echo "✅ 개발 서비스 재시작 완료"

# =============================================================================
# 모니터링 명령어 (Monitoring Commands)
# =============================================================================

logs: ## 프로덕션 서비스 로그 확인
	@cd docker && docker-compose logs -f

logs-dev: ## 개발 서비스 로그 확인
	@cd docker && docker-compose -f docker-compose.dev.yml logs -f

status: ## 서비스 상태 확인
	@echo "📊 서비스 상태:"
	@cd docker && docker-compose ps
	@echo ""
	@echo "📊 개발 서비스 상태:"
	@cd docker && docker-compose -f docker-compose.dev.yml ps

# =============================================================================
# 유지보수 명령어 (Maintenance Commands)
# =============================================================================

clean: ## 사용하지 않는 컨테이너 및 이미지 정리
	@echo "🧹 Docker 리소스 정리 중..."
	@docker container prune -f
	@docker image prune -f
	@docker volume prune -f
	@echo "✅ 정리 완료"

clean-all: ## 모든 컨테이너, 이미지, 볼륨 제거 (주의!)
	@echo "⚠️  경고: 이 명령어는 프로젝트의 모든 Docker 리소스를 제거합니다"
	@read -p "정말 계속하시겠습니까? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@cd docker && docker-compose down -v --rmi all 2>/dev/null || true
	@cd docker && docker-compose -f docker-compose.dev.yml down -v --rmi all 2>/dev/null || true
	@echo "🗑️  모든 리소스가 제거되었습니다"

# =============================================================================
# 개발 명령어 (Development Commands)
# =============================================================================

test: ## Docker 컨테이너에서 테스트 실행
	@echo "🧪 테스트 실행 중..."
	@cd docker && docker-compose -f docker-compose.dev.yml run --rm comix-server-dev python -m pytest
	@echo "✅ 테스트 완료"

test-build: ## Docker 이미지 빌드 테스트
	@echo "🐳 Docker 빌드 테스트 실행 중..."
	@./scripts/quick-docker-test.sh
	@echo "✅ 빌드 테스트 완료"

test-build-full: ## 전체 Docker 빌드 테스트 (상세)
	@echo "🐳 전체 Docker 빌드 테스트 실행 중..."
	@./scripts/test-docker-build.sh
	@echo "✅ 전체 빌드 테스트 완료"

test-auth: ## 인증 기능 테스트
	@echo "🔐 인증 기능 테스트 실행 중..."
	@chmod +x scripts/test-auth.sh
	@./scripts/test-auth.sh
	@echo "✅ 인증 테스트 완료"

test-cov: ## 커버리지와 함께 테스트 실행
	@echo "🧪 커버리지 테스트 실행 중..."
	@cd docker && docker-compose -f docker-compose.dev.yml run --rm comix-server-dev python -m pytest --cov=app --cov-report=html
	@echo "✅ 커버리지 테스트 완료"

shell: ## 실행 중인 프로덕션 컨테이너에 셸 접속
	@docker exec -it comix-server /bin/bash

shell-dev: ## 실행 중인 개발 컨테이너에 셸 접속
	@docker exec -it comix-server-dev /bin/bash

# =============================================================================
# 설정 명령어 (Setup Commands)
# =============================================================================

setup: ## 초기 설정 - 환경 파일 생성 및 빌드
	@echo "⚙️  Comix Server 초기 설정 중..."
	@if [ ! -f docker/.env ]; then \
		cp docker/.env.example docker/.env; \
		echo "📝 docker/.env 파일이 템플릿에서 생성되었습니다"; \
		echo "📁 docker/.env 파일을 편집하여 만화 디렉토리를 설정하세요"; \
	else \
		echo "📝 docker/.env 파일이 이미 존재합니다"; \
	fi
	@$(MAKE) build-quick
	@echo "✅ 설정 완료! 'make run'으로 서버를 시작하세요"

setup-dev: ## 개발 환경 초기 설정
	@echo "⚙️  개발 환경 초기 설정 중..."
	@$(MAKE) setup
	@$(MAKE) build-dev
	@echo "✅ 개발 환경 설정 완료! 'make run-dev'로 개발 서버를 시작하세요"

# =============================================================================
# 빠른 시작 명령어 (Quick Start Commands)
# =============================================================================

quick-start: setup run ## 완전 자동 설정 및 시작 (처음 사용자용)
	@echo ""
	@echo "🎉 Comix Server가 시작되었습니다!"
	@echo "📁 docker/.env 파일에서 MANGA_DIRECTORY를 설정하는 것을 잊지 마세요"
	@echo "🌐 서버 접속: http://localhost:31257"
	@echo "📊 상태 확인: make status"
	@echo "📋 로그 확인: make logs"
	@echo "🛑 서버 중지: make stop"

quick-dev: setup-dev run-dev ## 개발 환경 빠른 시작
	@echo ""
	@echo "🎉 개발 서버가 시작되었습니다!"
	@echo "🌐 서버 접속: http://localhost:31257"
	@echo "🐛 디버그 포트: 5678"
	@echo "🔄 코드 변경 시 자동 리로드됩니다"

# =============================================================================
# 헬스체크 및 업데이트 (Health Check & Update)
# =============================================================================

health: ## 서비스 헬스체크
	@echo "🏥 Comix Server 헬스체크 중..."
	@curl -f http://localhost:31257/health > /dev/null 2>&1 && \
		echo "✅ 서버가 정상 작동 중입니다" || \
		echo "❌ 서버가 응답하지 않습니다"

update: ## 최신 변경사항 가져오기 및 재빌드
	@echo "🔄 Comix Server 업데이트 중..."
	@git pull
	@$(MAKE) build
	@$(MAKE) restart
	@echo "✅ 업데이트 완료"

release: ## 수동 릴리스 생성 (버전 입력 필요)
	@echo "🚀 수동 릴리스 생성"
	@read -p "릴리스 버전을 입력하세요 (예: v1.2.3): " VERSION; \
	if [ -z "$$VERSION" ]; then \
		echo "❌ 버전을 입력해야 합니다."; \
		exit 1; \
	fi; \
	git tag -a "$$VERSION" -m "Release $$VERSION"; \
	git push origin "$$VERSION"; \
	echo "✅ 릴리스 $$VERSION 생성 완료"

tag-list: ## 현재 태그 목록 확인
	@echo "📋 현재 태그 목록:"
	@git tag -l --sort=-version:refname | head -10

# =============================================================================
# 정보 명령어 (Information Commands)
# =============================================================================

info: ## 시스템 정보 표시
	@echo "ℹ️  Comix Server 정보"
	@echo "===================="
	@echo "Docker 버전: $$(docker --version)"
	@echo "Docker Compose 버전: $$(docker-compose --version)"
	@echo ""
	@echo "프로젝트 이미지:"
	@docker images | grep comix-server || echo "이미지가 없습니다. 'make build'를 실행하세요."
	@echo ""
	@echo "실행 중인 컨테이너:"
	@docker ps | grep comix || echo "실행 중인 컨테이너가 없습니다."