# 가상 데이터 생성기 (Faker - ko_KR) + 실제 대피소 API 데이터

프로젝트에 맞춘 가상 데이터를 생성하는 스크립트입니다. **실제 정부 API에서 가져온 대피소 데이터(약 2.2만개)와 가상 데이터를 결합**하여 완전한 테스트 데이터셋을 만들 수 있습니다.

## 🏠 대피소 데이터 처리 방식

### ✅ 실제 대피소 데이터 우선 사용
- **실제 CSV 파일 제공**: 정부 API 데이터(~22,000개) 사용, `--shelters` 옵션 무시
- **실제 CSV 파일 없음**: 가상 대피소 데이터 `--shelters` 개수만큼 생성

### 📁 실제 대피소 데이터 파일
- `tools/대피소추가_API/shelter_schema_전국.csv` (전국 ~22,000개)
- `tools/대피소추가_API/shelter_schema_대구.csv` (대구 지역)

## 📦 설치 및 설정

1. 가상환경을 만든 뒤 아래를 실행하세요.

```powershell
python -m pip install -r tools\requirements.txt
```

## 🚀 사용법

### 실제 대피소 데이터 + 가상 데이터 통합 생성 (추천)

**JSON 형태**:
```powershell
python tools\generate_fake_data.py --real_shelter_csv "tools\대피소추가_API\shelter_schema_전국.csv" --users 100 --relief_items 50 --wishes 300 --requests 250 --matches 150
```

**CSV 형태 (UTF-8-sig)**:
```powershell
python tools\generate_fake_data_csv.py --real_shelter_csv "tools\대피소추가_API\shelter_schema_전국.csv" --users 100 --relief_items 50 --wishes 300 --requests 250 --matches 150
```

### 가상 데이터만 생성 (실제 대피소 데이터 없을 때)

**JSON 형태**:
```powershell
python tools\generate_fake_data.py --users 100 --shelters 30 --relief_items 50
```

**CSV 형태**:
```powershell
python tools\generate_fake_data_csv.py --seed 42 --users 200 --shelters 80 --relief_items 160 --wishes 300 --requests 250 --matches 200 --incidents 30 --consumptions 100
```

### 🎯 간편 실행 스크립트

```powershell
python tools\example_generate_with_real_data.py
```

## 📊 출력 결과

- **JSON**: 프로젝트 루트의 `output/` 폴더에 각 테이블별 JSON 파일 생성
- **CSV**: 프로젝트 루트의 `output_csv/` 폴더에 각 테이블별 CSV 파일 생성 (인코딩: UTF-8-sig)

### 생성되는 파일들
```
output/ (또는 output_csv/)
├── users.json (csv)           # 사용자 데이터
├── shelters.json (csv)        # 🏠 실제 대피소 데이터 (~22,000개)
├── relief_items.json (csv)    # 구호품 데이터
├── user_donation_wishes.json (csv)  # 기부 의사 데이터
├── shelter_relief_requests.json (csv)  # 대피소 구호품 요청
├── donation_matches.json (csv)  # 매칭 데이터
├── disaster_incidents.json (csv)  # 재난 사건 데이터
└── consumption_info.json (csv)  # 소비 정보 데이터
```

## 📋 주요 특징

- **실제 정부 API 데이터**: 전국 대피소 약 22,000개 데이터 활용
- **한국어 로케일**: Faker의 `ko_KR` 사용으로 한국 이름, 주소, 전화번호 생성
- **지리적 정확성**: 대한민국 좌표 범위 내에서 위치 생성
- **운영 상태 초기화**: `current_occupancy`, `occupancy_rate` 등을 0으로 설정
- **관리자 자동 할당**: 생성된 사용자 중에서 대피소 관리자 자동 배정

## 📓 Jupyter 노트북

- `tools/notebooks/generate_fake_data.ipynb`: 단계별 실행과 설명 제공
- `tools/대피소추가_API/api_call.ipynb`: 실제 정부 API 데이터 수집 및 스키마 매핑

## ⚙️ 주요 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--real_shelter_csv` | 실제 대피소 CSV 파일 경로 | None |
| `--users` | 생성할 사용자 수 | 50 |
| `--shelters` | 가상 대피소 수 (실제 데이터 없을 때만) | 20 |
| `--relief_items` | 구호품 종류 수 | 30 |
| `--wishes` | 기부 의사 수 | 100 |
| `--requests` | 구호품 요청 수 | 80 |
| `--matches` | 매칭 수 | 60 |
| `--incidents` | 재난 사건 수 | 10 |
| `--consumptions` | 소비 정보 수 | 40 |
| `--seed` | 랜덤 시드 | None |
| `--out` | 출력 폴더 | output |
