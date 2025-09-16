# 다변량 LSTM 기반 구호품 수량 예측 모델 구축 가이드

본 문서는 RECS00이 제안한 품목에 대해, 대피소 컨텍스트와 과거 소비/요청 데이터를 활용하여 향후 기간의 필요 수량을 예측하는 순차 모델(LSTM) 구축 가이드입니다.

## 1. 문제 정의
- 입력: 대피소-재난-품목 시계열 컨텍스트(과거 T일)
- 출력: 향후 H일 수요 총량 또는 일별 수요 시계열 예측
- 목적: OFFC02 자동 수량 채움, RECS01 매칭 시 remaining_need 추정 정밀화

## 2. 데이터셋 설계
### 2.1 기본 테이블 및 조인
- consumption_info: (shelter_id, disaster_incident_id, relief_item_id, consumed_quantity, start_date, end_date, duration_days, daily_consumption_rate, seasonality, ...)
- shelter_relief_requests: (shelter_id, relief_item_id, requested_quantity, current_stock, urgent_quantity, needed_by, status, remaining_quantity, created_at)
- shelters: (shelter_id, occupancy_rate, total_capacity, accessibility_score, distribution_efficiency, latitude, longitude, has_disabled_facility, has_pet_zone, amenities)
- disaster_incidents: (incident_id, disaster_year, region_code, disaster_severity, weather_conditions, latitude, longitude, first_registered_at)
- relief_items: (item_id, category, subcategory, item_name, unit)

### 2.2 학습용 레코드 구성(일 단위 패널)
- 키: (shelter_id, relief_item_id, date)
- 타깃: y_t = 당일 소비/필요 수량(ground truth). 우선 순서: consumption_info.daily_consumption_rate 추정 → 요청 데이터 보강
- 피처(시점 t에서 관측 가능)
  - 과거 k일 이동합/이동평균: 소비량, 요청량, 잔여량
  - 점유/수용: current_occupancy, occupancy_rate
  - 재난/날씨: disaster_severity, weather_conditions(원핫/임베딩)
  - 인구구성: children_ratio, elderly_ratio, disabled_ratio
  - 계절/요일: seasonality, dayofweek, holiday flag
  - 물류/운영: distribution_efficiency, restock_frequency
  - 품목 메타: category/subcategory 임베딩

### 2.3 최종 학습 테이블 스키마(컬럼)
- index: shelter_id(string), relief_item_id(string), date(date)
- target: y_t(int)
- features (예시)
  - cons_ma7, cons_ma14, cons_ma28 (float)
  - req_ma7, req_ma14, req_ma28 (float)
  - remain_est (float)
  - occupancy_rate (float), current_occupancy (int), total_capacity(int)
  - disaster_severity (int 1~5), weather_hot, weather_cold, weather_rain, weather_snow, weather_normal (binary)
  - season_spring, season_summer, season_fall, season_winter (binary)
  - children_ratio, elderly_ratio, disabled_ratio (float)
  - distribution_efficiency (float), accessibility_score(float)
  - item_cat_id(int), item_subcat_id(int)
  - dow_0..6 (binary), holiday (binary)

## 3. 모델 사양
- 입력 텐서: X ∈ [batch, T, D] (T=lookback window, 예: 28~56일, D=피처 수)
- 출력
  - 옵션 A: 단일 스텝 총량: ŷ_total ∈ [batch, 1] (H일 합)
  - 옵션 B: 다중 스텝: Ŷ ∈ [batch, H] (각 일자 예측)
- 모델 구조(예시)
  - Input → LSTM(64~128) → Dropout → LSTM(32~64) → Dense(H) → ReLU
  - 추가: 카테고리 임베딩 + 컨텍스트 MLP 분기 후 concat

## 4. 학습 파이프라인
1) 시계열 윈도우 생성: 슬라이딩 윈도우로 (T 입력, H 라벨) 샘플링
2) 정규화: 연속형 표준화, 카테고리 임베딩
3) 손실: MSE/MAE + 재난 구간 가중치(심각/긴급 구간에 더 높은 가중)
4) 검증: temporally consistent split(기간 기준), rolling-origin
5) 평가 지표: MAE, RMSE, sMAPE, WAPE, P50/P90 quantile loss(선택)

## 5. 서빙/출력 스키마
- API Contract
```
POST /forecast/lstm/predict
{
  "shelter_id": "SH_000001",
  "items": ["relief_item_001", "relief_item_010"],
  "horizon_days": 7,
  "context_override": { "occupancy_rate": 0.7, "weather_conditions": "추위" }
}
```
- 응답
```
{
  "forecasts": [
    {
      "shelter_id": "SH_000001",
      "relief_item_id": "relief_item_001",
      "horizon_days": 7,
      "daily_forecast": [45, 48, 51, 55, 52, 50, 49],
      "total_forecast": 350,
      "p50": 345, "p90": 420,
      "explanations": ["점유율↑", "날씨:추위"],
      "generated_at": "2025-09-16T10:00:00Z",
      "model_version": "lstm_v1"
    }
  ]
}
```

## 6. 훈련 데이터 생성 파이프라인(ETL)
- 단계
  1) 원천 적재: tools/output_csv 및 실제 API 대피소 데이터
  2) 패널 생성: 일 단위로 확장, 결측 전파/보간
  3) 윈도우 피처 생성: 이동통계, 최근/계절 피처, 원핫/임베딩 인코딩
  4) 타깃 생성: consumption_info와 요청데이터 융합으로 y_t 추정
  5) 스플릿/저장: train/valid/test by time
- 산출물
  - train.parquet: [shelter_id, relief_item_id, date, features..., y_t]
  - stats.json: 표준화/스케일링 파라미터, 카테고리 매핑

## 7. 엣지 케이스/로버스트 설계
- 콜드스타트 대피소/품목: 글로벌 평균 + 유사 프로필 priors 사용
- 재난 급변: 최근 k일 가중, change-point 탐지로 downweight 과거
- 드랍아웃/정규화로 과적합 방지, 학습 재현성(seed, 버전 관리)

## 8. 운영
- 배치 재학습: 주간/격주, 심각 이벤트 시 on-demand
- 모니터링: WAPE drift, 캘리브레이션, 예측-실측 차이 알람
- 모델 레지스트리: 버전, 데이터 스탬프, 하이퍼파라미터 기록
