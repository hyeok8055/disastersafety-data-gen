# RECS01 수요-기부 매칭 모델 구축 가이드 (Twitter 오픈소스 추천 로직 차용)

본 문서는 트위터 오픈소스 추천 시스템(그래프 기반 후보 생성 + 다단계 랭킹)의 아이디어를 차용하여, 이어드림의 "수요 구호품–기부 희망 구호품 매칭" 기능(RECS01)을 모델/시스템 관점에서 구현하기 위한 실무 가이드라인입니다.

## 1. 목표와 성공 기준
- 목표: 기부자의 희망 구호품과 전국 대피소의 요청 구호품을 연결해 최대 사회 효용(긴급도, 적합도, 충족량)을 달성하는 매칭 리스트를 생성.
- 핵심 성공 지표(KPIs)
  - 매칭 충족률: matched_quantity / requested_quantity
  - 긴급도 개선: 매칭 이후 remaining_quantity 감소량 가중 합계
  - 사용자 클릭/수락률: 추천 매칭 제안에 대한 사용자의 수락률
  - 공정성/커버리지: 다양한 지역/대피소로의 매칭 분산도

## 2. 시스템 개요 (Twitter 스타일 파이프라인)
- 피처: 그래프 신호(사용자-아이템-대피소 3파팅 그래프), 인기도/신선도, 지리/물류, 예산 제약, 재난/긴급 신호 등
- 파이프라인 단계
  1) 후보 생성(Recall)
     - 그래프 워크/유사도(아이템명/코드 기반): 동일/유사 아이템 요청 중인 대피소 후보 수집
     - 지역 근접성: 사용자 위치 반경 내 대피소(예: 50km)
     - 긴급 큐: 긴급도 높음/마감 임박 요청 선별
  2) 프라이어 필터링
     - 상태 필터: 대기중 요청만, 재고/잔여 필요량 > 0
     - 중복/차단 필터: 사용자가 이미 매칭한 요청 제외
  3) 랭킹(Scoring)
     - 다특징 로지스틱/GBDT 혹은 경량 신경망 점수화
     - 탐험(exploration) 가중치(신규 대피소/저노출 요청 가점)
  4) 리랭킹/할당
     - 예산/수량 제약 하에서 최적 분배(선형할당/그리디)
     - 동일 아이템 다 대피소 분할 여부 정책

## 3. 데이터 입출력 스키마 정의

### 3.1 입력: 매칭 요청 payload
- Contract (API/서빙)
```
POST /recs/recs01/match
Content-Type: application/json
{
  "user_id": "user_0001",                // 필수
  "relief_items": [                        // 선택: 없으면 DB의 user_donation_wishes 미매칭 항목 사용
    { "item_name": "컵라면", "quantity": 20 },
    { "item_name": "물티슈", "quantity": 50 }
  ],
  "budget": 120000,                        // 선택, 원 단위
  "max_candidates": 200,                   // 후보 최대 수(디폴트 300)
  "radius_km": 50,                         // 반경 검색 km(디폴트 100)
  "allow_split": true                      // 품목을 여러 대피소에 분할 허용
}
```

- 내부 조인 대상 테이블 및 주요 컬럼
  - users(user_id, zipcode, road_address, latitude, longitude, preferred_categories)
  - user_donation_wishes(user_id, relief_item_id, quantity, remaining_quantity, status)
  - relief_items(item_id, item_code, category, subcategory, item_name, unit)
  - shelters(shelter_id, shelter_name, latitude, longitude, status, total_capacity, current_occupancy)
  - shelter_relief_requests(request_id, shelter_id, relief_item_id, requested_quantity, current_stock,
    urgent_quantity, urgency_level, needed_by, status, remaining_quantity)

- 파생 컬럼/전처리
  - wish_key: user_id + relief_item_id
  - distance_km: haversine(user, shelter)
  - remaining_need = max(requested_quantity - current_stock - total_matched_quantity, 0)
  - urgency_score_base: urgency_level(높음/중간/낮음 → 1.0/0.6/0.3) × time_decay(needed_by)

### 3.2 출력: 매칭 결과 payload
```
{
  "matched_shelters": [
    {
      "shelter_id": "SH12345",
      "shelter_name": "동작구민회관 대피소",
      "matched_items": [
        { "item_name": "컵라면", "relief_item_id": "relief_item_001",
          "requested": 50, "matched": 20 }
      ],
      "urgency_score": 92.5,
      "distance_km": 12.3,
      "allocation_cost": 18000,            // 해당 매칭 분배에 따른 추정 비용
      "request_ids": ["request_001"],
      "notes": "마감 임박(내일)"
    }
  ],
  "total_allocation_cost": 54000,
  "remaining_budget": 66000,
  "generation_info": { "created_at": "2025-09-16T10:00:00Z", "version": "recs01_v1" }
}
```

- 컬럼/필드 설명
  - urgency_score: 0~100 스케일(정규화)
  - allocation_cost: 단가 추정치 × matched 합

## 4. 특징량(Features)
- 사용자 측: 선호 카테고리, 과거 기부 히스토리의 카테고리/아이템 분포, 과거 매칭 수락/거절율
- 아이템 측: 카테고리/소분류, 인기도(요청 빈도), 신선도(요청 최신성)
- 대피소 측: 거리, 수용률, 재난/사건 연계 심각도, 접근성 점수, 배송 효율
- 요청 측: remaining_need, urgency_level, needed_by 잔여시간, 과거 충족률

## 5. 점수 산식(예: 경량 가중 합)
- base_score = w1*urgency + w2*need_ratio + w3*distance_decay + w4*popularity + w5*freshness
  - need_ratio = min(available_quantity, remaining_need)/remaining_need
  - distance_decay = exp(-distance_km/τ)
  - popularity = item 요청 빈도 표준화
  - freshness = 최근 요청일 가중
- exploration_bonus = ε for under-exposed shelters/regions
- final_score = base_score + exploration_bonus

## 6. 후보 생성 알고리즘(예시)
- Item join: relief_items.item_name 또는 item_code로 매칭되는 요청 집합
- 지역 버킷: radius_km 내 shelter_relief_requests 조인
- 긴급 큐: urgency_level=='높음' 또는 needed_by≤48h

## 7. 리랭킹/할당
- 제약: 총 예산 ≤ budget, 각 wish의 remaining_quantity 범위 내 분배
- 전략: 점수 순으로 그리디하게 matched = min(remaining_need, available_quantity) 할당
- 분할 정책: allow_split=false면 품목당 1개 대피소만 선택

## 8. 오프라인 학습/평가
- 학습용 레이블: 과거 donation_matches 기반 전환(매칭→배송완료) 여부/수량
- 학습 데이터 스키마(positive/negative sampling 포함)
  - key: (user_id, wish_id, request_id, ts)
  - label: matched_quantity>0 여부(이진) 또는 매칭 비율(연속)
  - features: 상기 사용자/아이템/대피소/요청 특징량
- 오프라인 지표: AUC/PR-AUC, NDCG@k, Recall@k, Coverage, Calibration

## 9. 온라인 서빙/캐시
- 후보 캐시: 인기 아이템별 긴급 요청 TopN 캐시(5~15분 TTL)
- 사용자 컨텍스트 캐시: 최근 위치/예산/희망품목 세션 캐시(세션 TTL)

## 10. 실패/예외 처리
- 입력 유효성 실패, 내부 쿼리 오류, 후보 부족 시: 메시지와 대체 추천(인접 카테고리) 제공
- 메시지: "매칭 과정에서 문제가 발생했습니다. 다시 시도해주세요."

## 11. 보안/정책
- 스팸/중복 방지: 동일 사용자의 반복 요청 rate limit
- 지역 편향 완화: 노출 제한 및 리랭킹 페널티

## 12. 레퍼런스
- Twitter Recommendation Algorithm(오픈소스): 그래프 기반 후보 생성과 랭킹, 리랭킹 아이디어 차용
