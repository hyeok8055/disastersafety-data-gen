# RECS00 대피소 조건별 구호품 추천 모델 구축 가이드 (Twitter 오픈소스 추천 로직 차용)

본 문서는 공무원이 입력한 대피소 조건을 바탕으로 과거 사례/소비 기록을 학습하여 품목과 수량(초기 추정)을 추천하는 시스템을, 트위터 오픈소스 추천 로직의 구조(후보 생성→랭킹→리랭킹)를 차용해 구현하는 가이드입니다.

## 1. 목표와 지표
- 목표: 대피소 상황(재난유형, 수용, 인구구성, 계절, 접근성)에 맞는 품목 리스트를 자동 추천
- 지표: 오프라인 NDCG@k, Recall@k, Item coverage, 운영 적합성 피드백 점수(공무원 평가)

## 2. 파이프라인 개요
1) 후보 생성
   - 사례 기반: 과거 유사 조건(재난유형, 계절, 인구비, 수용률)에서 많이 소비/요청된 품목 TopN
   - 카테고리 prior: 필수 기본 세트(식량/위생/의약품/침구 등) 카테고리별 대표 품목
   - 지역/날씨 prior: 지역/계절 특화 품목 후보
2) 전처리/필터
   - 중복/부적합(예: 반려동물 미허용 → 반려용품 제외)
   - 재고/보급 주기 정책 반영
3) 랭킹
   - 특징량 기반 경량 모델(GBDT/로지스틱) 또는 규칙+점수
4) 리랭킹
   - 다양성/커버리지, 예산/물류 제약 고려, 카테고리 밸런스

## 3. 입력 스키마(OFFC02 연계)
- API Contract
```
POST /recs/recs00/recommend
Content-Type: application/json
{
  "shelter_id": "SH_000001",    // 선택: 있으면 해당 대피소 프로필 사용
  "context": {                     // 없으면 여기에 조건 필수 기입
    "disaster_type": "지진",         
    "season": "겨울",                
    "total_capacity": 300,
    "current_occupancy": 180,
    "occupancy_rate": 0.6,
    "has_disabled_facility": true,
    "has_pet_zone": false,
    "children_ratio": 0.25,
    "elderly_ratio": 0.15,
    "disabled_ratio": 0.08,
    "weather_conditions": "추위",
    "distribution_efficiency": 0.8,
    "region_code": "RGN_11680"
  },
  "top_k": 50
}
```

- 내부 사용 테이블/컬럼
  - shelters(..., disaster_type, total_capacity, current_occupancy, occupancy_rate,
    has_disabled_facility, has_pet_zone, amenities, latitude, longitude)
  - consumption_info(shelter_id, disaster_incident_id, relief_item_id,
    consumed_quantity, duration_days, daily_consumption_rate, seasonality,
    children_ratio, elderly_ratio, disabled_ratio, disaster_severity, weather_conditions)
  - relief_items(item_id, item_code, category, subcategory, item_name, unit)
  - disaster_incidents(disaster_year, ndms_disaster_type_code, region_code, seasonality, severity)

- 파생 피처(예시)
  - shelter_profile_embedding: 조건 벡터화(원핫/임베딩)
  - item_popularity: 유사 프로필에서의 사용 빈도/소비량 표준화
  - adequacy_prior: 유사 사례의 adequacy_level(부족/적정/충분)로부터 학습된 priors

## 4. 출력 스키마
```
{
  "recommended_items": [
    {
      "category": "식량",
      "subcategory": "즉석식품",
      "item_id": "relief_item_001",
      "item_code": "FOOD_001",
      "item_name": "햇반",
      "initial_quantity_suggestion": 300,   // 1차 정성 추정치(정수)
      "unit": "개",
      "score": 0.86,
      "rationale": ["계절:겨울", "점유율:0.6", "유사사례 소비높음"]
    }
  ],
  "generation_info": { "created_at": "2025-09-16T10:00:00Z", "version": "recs00_v1" }
}
```

## 5. 특징량 설계(예시)
- 대피소 컨텍스트: season, occupancy_rate, capacity, children/elderly/disabled ratio, weather
- 재난 컨텍스트: disaster_type, severity, 최근 사건 근접도
- 품목 컨텍스트: 카테고리, 유사사례 소비량/요청 빈도, 폐기율(waste_rate) 페널티, 만족도 가중
- 물류/접근성: distribution_efficiency, accessibility_score

## 6. 랭킹 점수(예시)
- score = g(w1*item_pop + w2*context_match + w3*(1-waste_rate) + w4*satisfaction)
- 다양성 리랭킹: 카테고리별 최소/최대 비율 제약, subcategory spread 보장

## 7. 학습 데이터 스키마(오프라인)
- key: (shelter_profile_id, item_id, snapshot_date)
- label: 다음 기간(consumption window) 내 소비/요청 발생 여부 또는 소비량 구간
- features: 상기 피처 + 지역/계절 이동평균

## 8. 온라인/운영 고려
- 기본 세트 fallback: 냉/난방/계절/위생 필수 리스트를 최소 확보
- 정책: 반려동물 시설 없음 → 반려용품 제외 등 하드 필터
- 캐싱: 프로필 버킷 단위 TopN 10~15분 캐시

## 9. 실패/예외
- 시간초과/데이터 부족: "추천 계산 중 오류가 발생했습니다. 다시 시도해주세요."

## 10. 연계
- RECS01: 유저 기부와의 매칭 후보 생성에 활용
- LSTM 수량예측 모델: initial_quantity_suggestion을 정교화
