# 이어드림 모델 학습 데이터셋 빌드 가이드

이 디렉터리는 3가지 모델(RECS01 매칭, RECS00 대피소 조건 추천, LSTM 수량예측)을 위한 학습 데이터셋을 생성합니다. 코드와 학습 스크립트는 다음과 같이 분리되어 있습니다.

- 데이터 생성: `models/data/build_datasets.py`
- 학습/베이스라인: `models/code/*.py`

## 1) 사전 준비
1. 패키지 설치
```powershell
python -m pip install -r tools\requirements.txt
```
2. 원천 CSV 생성(없다면)
```powershell
python tools\generate_fake_data_csv.py --real_shelter_csv "tools\대피소추가_API\shelter_schema_전국.csv" --seed 42
```

## 2) 데이터셋 생성
```powershell
python models\data\build_datasets.py --real_shelter_csv "tools\대피소추가_API\shelter_schema_전국.csv" --seed 42 --min_rows 30000
```
- --min_rows: 각 데이터셋의 최소 행수를 지정합니다. 부족 시 부트스트랩 복제 + 수치 피처 소량 잡음(jitter)으로 증강하여 최소 n행 이상을 보장합니다.
- 저장 형식은 CSV(UTF-8-sig)입니다.

### 산출물 구조
```
models/data/
  raw/                   # 원천 CSV 스냅샷
  recs01_matching/
    train.csv            # 후보-라벨 데이터
    schema.json          # 라벨/피처 정의
  recs00_item_rec/
    train.csv
    schema.json
  lstm_forecast/
    train.csv            # 일 단위 패널 시계열
    stats.json           # 기술통계(정규화 참고)
    schema.json
```

## 3) 각 데이터셋 생성 로직 요약

### RECS01 수요–기부 매칭(recs01_matching)
- 후보 생성: 동일 `relief_item_id` 기준으로 `user_donation_wishes` × `shelter_relief_requests` 내부 조인
- 라벨: `donation_matches`에 (wish_id, request_id) 존재하면 1, 아니면 0
- 주요 피처
  - 수량/재고: requested_quantity, current_stock, wish_remaining_quantity, remaining_need
  - 긴급도: urgency_score (높음/중간/낮음 매핑)
  - 적합도: need_ratio = min(wish_remaining_quantity, remaining_need) / remaining_need
  - 거리: distance_km (사용자 좌표는 임시 난수 부여 후 허버사인 계산; 실제 서비스는 지오코딩 권장)

### RECS00 대피소 조건별 추천(recs00_item_rec)
- pair 생성: consumption_info를 (shelter_id, relief_item_id)로 집계 + requests 집계 병합
- 라벨: total_remaining > 0 → 1 (베이스라인 대용 라벨)
- 주요 피처: consumed_days, consumed_qty, daily_rate, total_requested, total_remaining, urgent, popularity

### LSTM 수량 예측(lstm_forecast)
- 일 단위 패널 생성: 각 소비 레코드를 시작~종료일까지 일 단위로 펼침, y_t = 일일 소비량
- 이동통계 피처: cons_ma7/14/28
- 범주 인코딩: seasonality, disaster_severity, weather를 원-핫 인코딩
- stats.json: 기술통계(후속 정규화/스케일링 참고용)

## 4) 학습/평가 스크립트 위치 및 실행
학습/베이스라인 스크립트는 `models/code`에 있습니다. 간단 실행 예시는 아래와 같습니다.

```powershell
# RECS01 베이스라인
python models\code\train_recs01_baseline.py

# RECS00 베이스라인
python models\code\train_recs00_baseline.py

# LSTM 템플릿(간단 통계)
python models\code\train_lstm_template.py
```

출력은 각 데이터셋 폴더에 JSON 파일로 저장됩니다.

## 5) 주의 및 팁
- 거리(distance_km)는 임시 난수 기반 사용자 좌표로 계산됩니다. 실제 위치 데이터가 확보되면 해당 부분을 교체하세요.
- RECS01의 라벨이 한 클래스만 존재할 수 있습니다. 이 경우 베이스라인 스크립트는 ROC/PR 계산을 건너뜁니다. 데이터 균형을 원하면 네거티브 샘플링 규칙을 추가하세요.
- 실제 전국 대피소 CSV가 있을 경우, `tools/대피소추가_API/shelter_schema_전국.csv`를 우선 사용합니다.
