# 📜 독립운동가 웹툰 에이전트 (Webtoon Agent)

> **공공데이터(Public Data) 기반 독립운동가 공적 정보를 바탕으로 AI 에이전트(Agent)가 역사적 팩트체크(Fact Check)를 거쳐 웹툰 스토리보드(Storyboard)를 생성하고, ComfyUI API(Application Programming Interface)를 통해 웹툰 컷 이미지를 자동으로 렌더링(Rendering)하는 혁신적인 웹툰 자동화 파이프라인(Pipeline) 서비스입니다.**

---

## 🏛️ 프로젝트 소개 (Project Introduction)

본 프로젝트는 독립운동가분들의 숭고한 희생과 역사를 현대적인 웹툰 형식으로 대중에게 널리 알리고자 기획되었습니다. 범용 이미지 생성 AI(Artificial Intelligence)가 겪는 **화풍 일관성 결여** 및 **인체 붕괴 현상**, **역사적 사실 왜곡**이라는 치명적인 기술적 문제를 해결하기 위해 다음과 같은 특화 기술을 통합하였습니다.

1. **역사적 고증과 팩트체크(Fact Check)**: 공공데이터 포털의 API를 연동하여 신뢰할 수 있는 독립운동 계열 정보를 구축하고, 구글 제미나이(Google Gemini) 모델을 통해 2단계에 걸친 철저한 역사적 사실 검증을 수행합니다.
2. **독립운동가 화풍 LoRA(Low-Rank Adaptation) 학습**: 엄격하게 정예화된 고품질 이미지 데이터셋(Dataset)을 통해 학습된 특화 LoRA 모델을 ComfyUI에서 동적으로 스위칭(Switching)하여 고품질의 일관된 웹툰 화풍을 보장합니다.
3. **태극기 합성 및 인페인팅(Inpainting) 기술**: 역사적 상징물인 태극기가 들어간 컷의 정교한 묘사를 위해, 2차 세그먼트 애니띵 모델(Segment Anything Model, SAM) 기반 인페인팅 워크플로우(Workflow)를 자동 연동하여 그래픽 품질을 극대화합니다.
4. **캔바(Canva) 대량 제작 연동**: 생성 완료된 이미지와 스토리 대사본(CSV 파일)을 하나의 압축 파일(ZIP)로 한 번에 다운로드(Download)하여 디자이너가 캔바 도구에서 즉시 웹툰을 레이아웃(Layout)할 수 있도록 돕습니다.

---

## 🧩 시스템 아키텍처 (System Architecture)

본 서비스는 사용자의 브라우저 화면부터 AI 이미지 생성 백엔드(Backend)와 데이터 저장소까지 유기적으로 연결된 4단계 파이프라인(Pipeline) 구조를 갖추고 있습니다.

```mermaid
graph TD
    subgraph Frontend [프론트엔드 - Streamlit]
        UI[웹 대시보드 UI]
    end

    subgraph Orchestrator [오케스트레이터 - Python]
        DB_Manager[데이터베이스 매니저]
        Gemini_Agent[Gemini 스토리 에이전트]
        Comfy_Client[ComfyUI API 클라이언트]
    end

    subgraph Storage [저장소 - PostgreSQL]
        DB[(PostgreSQL DB)]
    end

    subgraph AI_Engine [AI 생성 엔진]
        ComfyUI[ComfyUI Server]
        LoRA_Model[성별 맞춤 LoRA 모델]
    end

    UI -->|1. 인물 선택 & 키 입력| Gemini_Agent
    Gemini_Agent -->|2. 역사 팩트체크 & 스토리보드 생성| DB_Manager
    DB_Manager <-->|3. 공적 데이터 조회 & 이력 저장| DB
    Gemini_Agent -->|4. Danbooru 프롬프트 최적화| Comfy_Client
    Comfy_Client -->|5. 워크플로우 템플릿 제어| ComfyUI
    ComfyUI -->|6. 성별 자동 스위칭 & 렌더링| LoRA_Model
    ComfyUI -->|7. 이미지 결과 저장| UI
    UI -->|8. Canva 연동 패키지 다운로드| UI
```

---

## 🚀 주요 기능 (Key Features)

### 1. 공공데이터 기반 정보 마이그레이션 (Data Migration)
* **파일**: `migrate_db.py`, `database.py`
* **기능**: 독립기념관의 오픈 API(Open API)를 활용하여 3.1운동, 계몽운동, 광복군, 임시정부 등 10개 주요 독립운동 계열의 인물 정보를 자동으로 수집(Fetch) 및 파싱(Parsing)하여 로컬 데이터베이스(Database)에 정밀하게 적재합니다.

### 2. 역사 고증 중심의 2단계 스토리보드 생성 (Fact-Checking Storyboard)
* **파일**: `generatestory.py`
* **기능**:
  * **1단계 초안 작성(Drafting)**: 인물의 상세 공적 데이터를 입력받아 웹툰 연출 기법(종스크롤 페이싱, 클라이맥스 강조, 카툰 앵글)에 맞게 6~10컷의 한국어 스토리보드를 자동 작성합니다.
  * **2단계 역사 팩트체크(Fact-Checking)**: 초안의 내용과 원본 공공데이터를 정밀 대조하여 인물 이름, 연도, 장소, 사건 등의 역사적 왜곡이나 왜상(Hallucination)을 걸러내고 엄격히 보정합니다.

### 3. 단부루 스타일 프롬프트 자동 변환 (Danbooru Tag Optimization)
* **파일**: `generateprompts.py`
* **기능**: Animagine XL 4.0 등 애니메이션 특화 확산 모델(Diffusion Model)의 성능을 극대화하기 위해, 스토리보드의 시각적 묘사를 단부루 스타일의 영어 태그(Danbooru Tags) 조합으로 자동 가공합니다. 한복의 고증 왜곡을 막기 위한 성별 태그 가중치와 역사 분위기에 걸맞은 부정 프롬프트(Negative Prompt)가 기본 세팅되어 작동합니다.

### 4. ComfyUI API 오케스트레이션 및 성별 LoRA 자동 스위칭 (Dynamic LoRA Switching)
* **파일**: `generateimages.py`, `start_server.py`
* **기능**: 
  * 백엔드에서 ComfyUI 서버가 켜져 있는지 확인 및 자동 부팅을 처리합니다.
  * 긍정 프롬프트의 텍스트 분석을 바탕으로 주인공 인물의 성별을 감지하여 **남성 한복 LoRA**와 **여성 한복 LoRA**의 가중치(Strength)를 실시간으로 스위칭하여 자연스러운 전통 복식을 구현합니다.
  * 컷마다 5장의 후보 이미지를 동시에 배클 렌더링(Batch Rendering)하여 최적의 연출을 고를 수 있도록 돕습니다.

### 5. 태극기 정교합성용 세그먼트 인페인팅 (Taegeukgi Inpainting)
* **파일**: `workflow_inpaint_only.json`, `generateimages.py`
* **기능**: 단순 프롬프트만으로 묘사가 까다로운 대한민국 태극기(Taegeukgi)를 정교하게 렌더링하기 위해, 인페인트(Inpaint) 전용 워크플로우를 가동하여 사용자가 엄선한 원본 컷 이미지 위에 태극기 마스크(Mask) 합성을 안전하게 수행합니다.

### 6. Canva 웹툰 대량 제작 포맷 추출 (Canva Batch Integration)
* **파일**: `app.py`
* **기능**: 각 컷별로 사용자가 고른 베스트 컷 이미지 파일들과 이에 상응하는 지문, 자막(내레이션), 캐릭터 대사 텍스트 데이터를 유니코드(UTF-8-SIG) 기반의 CSV(Comma-Separated Values) 스프레드시트 파일과 묶어 단일 ZIP 패키지로 신속히 내보냅니다.

---

## 🛠️ 기술 스택 (Tech Stack)

* **언어(Language)**: Python (>= 3.11)
* **웹 프레임워크(Web Framework)**: Streamlit (>= 1.30.0)
* **데이터베이스(Database / ORM)**: PostgreSQL (v17), SQLAlchemy (>= 2.0.0)
* **AI API 연동**: `google-genai` (Gemini-2.5-Flash 활용)
* **이미지 생성 서버(Image Generation Engine)**: ComfyUI (Animagine XL 4.0 및 성별 LoRA 모델 통합)
* **기타 라이브러리**: `xmltodict`, `psycopg2-binary`, `pillow` (PIL)

---

## 🏃 실행 및 구동 방법 (How to Run)

### 1. 사전 요구사항 (Prerequisites)
* **UV 패키지 매니저(Package Manager)** 설치 권장 (가상환경의 고속 구축 지원)
* **도커(Docker)** 및 **도커 컴포즈(Docker Compose)** 설치 (PostgreSQL 환경 구동용)
* **ComfyUI** 로컬 설치 환경 확보 및 이미지 생성용 LoRA 가중치 파일 구비

### 2. 가상환경(Virtual Environment) 구축 및 패키지 설치
UV 패키지 매니저를 사용하여 가상환경을 효율적으로 세팅하고 의존 패키지(Dependencies)를 설치합니다.

```bash
# 1. uv를 이용해 의존 패키지 및 가상환경 설정
uv venv
source .venv/Scripts/activate  # Windows(윈도우) 환경 기준 활성화

# 2. 필요한 파이썬 라이브러리 일괄 설치
uv pip install -r requirements.txt
```

### 3. 환경 변수 설정
프로젝트 루트(Root) 디렉토리에 `.env` 파일을 생성하고 아래 형식을 참조하여 DB 주소를 입력합니다.

```env
# 데이터베이스 연결 기본 주소 (PostgreSQL 아이디:비밀번호@호스트:포트/DB명)
DATABASE_URL=postgresql://user:qwer@localhost:5432/webtoon_db
```

### 4. 도커 컨테이너(Docker Container)를 이용한 데이터베이스 구동
도커 컴포즈 명령을 활용해 백그라운드에서 PostgreSQL 컨테이너를 가동합니다.

```bash
# 백그라운드 모드로 데이터베이스 서버 가동
docker-compose up -d
```

### 5. 공공데이터 API 연동 데이터베이스 마이그레이션 실행
로컬 데이터베이스에 독립운동가 오픈 API 정보를 이관(Migration)하기 위해 아래의 마이그레이션 스크립트를 수행합니다.

```bash
# DB 스키마 초기화 및 독립운동가 인물 목록 자동 적재
python migrate_db.py
```

### 6. Streamlit 웹 서비스 대시보드 실행
준비가 끝나면 대시보드 웹 프로그램을 실행하여 웹툰 자동 생성 서비스를 웹 프라우저에서 이용합니다.

```bash
# 스트림릿 애플리케이션 가동
streamlit run app.py
```

---

## 📂 디렉토리 구조 (Project Structure)

```text
webtoon_agent/
│
├── .env                       # 데이터베이스 연결 주소 및 비밀 환경 변수 설정 파일
├── app.py                     # Streamlit 기반 통합 웹 대시보드 메인 컨트롤러
├── database.py                # PostgreSQL DB 커넥션 및 SQLAlchemy ORM 테이블 모델
├── migrate_db.py              # 공공데이터 API 연동 및 DB 적재 파이프라인 스크립트
├── generatestory.py           # Gemini 2.5-Flash 연동 역사 팩트체크 스토리보드 빌더
├── generateprompts.py         # 컷별 스토리를 Danbooru 태그 및 한복 고증 프롬프트로 변환
├── generateimages.py          # ComfyUI API 통신 및 성별 LoRA/SAM 인페인팅 제어 로직
├── start_server.py            # ComfyUI 로컬 실행 엔진 체크 및 서브프로세스 기동
├── docker-compose.yml         # PostgreSQL DB 컨테이너 가상화 구성 명세서
│
├── workflow_normal.json       # ComfyUI 표준 이미지 생성 워크플로우 템플릿
├── workflow_inpaint_only.json # ComfyUI SAM 기반 태극기 인페인트 보정 워크플로우
├── webtoon_randomseed.json    # 화풍 고정용 및 무작위 시드 관리용 메타데이터
│
└── pyproject.toml             # UV 패키지 매니저 빌드 의존성 및 메타 정보 명세서
```

---

### 📜 라이선스 및 사용 안내 (License)
본 프로젝트는 교육 및 포트폴리오(Portfolio) 목적으로 작성되었으며, 수집된 모든 독립운동가 데이터의 소유권은 독립기념관 공공데이터 플랫폼에 있습니다. 무단 상업적 재배포를 금지합니다.
