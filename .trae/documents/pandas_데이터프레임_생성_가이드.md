# 이어드림 Pandas 데이터프레임 생성 가이드

## 1. 개요

이 문서는 이어드림 데이터베이스 스키마를 기반으로 pandas 데이터프레임 형태의 예시 데이터를 생성하는 방법을 제공합니다. 특히 다변량 LSTM 예측 모델과 트위터 오픈소스 추천 알고리즘 학습을 위한 현실적인 데이터 생성에 중점을 둡니다.

## 2. 필요한 라이브러리 설치 및 임포트

```python
import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timedelta
import random
import json
from faker import Faker
import warnings
warnings.filterwarnings('ignore')

# 한국어 데이터 생성을 위한 Faker 설정
fake = Faker('ko_KR')
Faker.seed(42)
np.random.seed(42)
random.seed(42)
```

## 3. 기본 마스터 데이터 생성

### 3.1 사용자 데이터 (users)

```python
def create_users_dataframe(num_users=1000):
    """
    사용자 데이터프레임 생성
    - 공무원 20%, 일반사용자 80% 비율
    """
    users_data = []
    
    for i in range(num_users):
        user_type = 'public_officer' if i < num_users * 0.2 else 'general_user'
        
        user = {
            'id': str(uuid.uuid4()),
            'user_id': f"user_{i:04d}",
            'email': fake.email(),
            'password_hash': fake.sha256(),
            'user_type': user_type,
            'name': fake.name(),
            'phone': fake.phone_number(),
            'cert_file_path': f"/certs/cert_{i}.pdf" if user_type == 'public_officer' else None,
            'terms_agreed': True,
            'created_at': fake.date_time_between(start_date='-2y', end_date='now'),
            'updated_at': fake.date_time_between(start_date='-1y', end_date='now'),
            'is_active': random.choice([True, True, True, False])  # 75% 활성
        }
        users_data.append(user)
    
    return pd.DataFrame(users_data)

# 사용자 데이터 생성
users_df = create_users_dataframe(1000)
print("Users DataFrame:")
print(users_df.head())
print(f"Shape: {users_df.shape}")
print(f"User types: {users_df['user_type'].value_counts()}")
```

### 3.2 구호품 마스터 데이터 (relief\_items)

```python
def create_relief_items_dataframe():
    """
    구호품 마스터 데이터프레임 생성
    """
    relief_items_data = [
        # 식량 - 즉석식품
        {'item_code': 'FOOD_001', 'category': '식량', 'subcategory': '즉석식품', 'item_name': '컵라면', 'unit': '개', 'estimated_price': 1000, 'shelf_life_days': 365},
        {'item_code': 'FOOD_002', 'category': '식량', 'subcategory': '즉석식품', 'item_name': '햇반', 'unit': '개', 'estimated_price': 1500, 'shelf_life_days': 180},
        {'item_code': 'FOOD_003', 'category': '식량', 'subcategory': '즉석식품', 'item_name': '삼각김밥', 'unit': '개', 'estimated_price': 1200, 'shelf_life_days': 3},
        
        # 식량 - 통조림
        {'item_code': 'FOOD_004', 'category': '식량', 'subcategory': '통조림', 'item_name': '참치캔', 'unit': '개', 'estimated_price': 2000, 'shelf_life_days': 1095},
        {'item_code': 'FOOD_005', 'category': '식량', 'subcategory': '통조림', 'item_name': '스팸', 'unit': '개', 'estimated_price': 3500, 'shelf_life_days': 1095},
        {'item_code': 'FOOD_006', 'category': '식량', 'subcategory': '통조림', 'item_name': '과일통조림', 'unit': '개', 'estimated_price': 2500, 'shelf_life_days': 730},
        
        # 식량 - 음료
        {'item_code': 'WATER_001', 'category': '식량', 'subcategory': '음료', 'item_name': '생수 500ml', 'unit': '개', 'estimated_price': 500, 'shelf_life_days': 730},
        {'item_code': 'WATER_002', 'category': '식량', 'subcategory': '음료', 'item_name': '이온음료', 'unit': '개', 'estimated_price': 1000, 'shelf_life_days': 365},
        {'item_code': 'WATER_003', 'category': '식량', 'subcategory': '음료', 'item_name': '우유', 'unit': '개', 'estimated_price': 2000, 'shelf_life_days': 7},
        
        # 생활용품 - 위생용품
        {'item_code': 'HYGIENE_001', 'category': '생활용품', 'subcategory': '위생용품', 'item_name': '물티슈', 'unit': '개', 'estimated_price': 3000, 'shelf_life_days': 1095},
        {'item_code': 'HYGIENE_002', 'category': '생활용품', 'subcategory': '위생용품', 'item_name': '휴지', 'unit': '개', 'estimated_price': 2000, 'shelf_life_days': 1095},
        {'item_code': 'HYGIENE_003', 'category': '생활용품', 'subcategory': '위생용품', 'item_name': '칫솔', 'unit': '개', 'estimated_price': 1500, 'shelf_life_days': 1095},
        {'item_code': 'HYGIENE_004', 'category': '생활용품', 'subcategory': '위생용품', 'item_name': '치약', 'unit': '개', 'estimated_price': 2500, 'shelf_life_days': 1095},
        {'item_code': 'HYGIENE_005', 'category': '생활용품', 'subcategory': '위생용품', 'item_name': '비누', 'unit': '개', 'estimated_price': 1000, 'shelf_life_days': 1095},
        
        # 의약품
        {'item_code': 'MEDICAL_001', 'category': '의약품', 'subcategory': '일반의약품', 'item_name': '해열제', 'unit': '개', 'estimated_price': 5000, 'shelf_life_days': 1095},
        {'item_code': 'MEDICAL_002', 'category': '의약품', 'subcategory': '일반의약품', 'item_name': '감기약', 'unit': '개', 'estimated_price': 8000, 'shelf_life_days': 1095},
        {'item_code': 'MEDICAL_003', 'category': '의약품', 'subcategory': '구급용품', 'item_name': '밴드', 'unit': '개', 'estimated_price': 3000, 'shelf_life_days': 1095},
        {'item_code': 'MEDICAL_004', 'category': '의약품', 'subcategory': '구급용품', 'item_name': '소독약', 'unit': '개', 'estimated_price': 4000, 'shelf_life_days': 1095},
        
        # 의류
        {'item_code': 'CLOTHING_001', 'category': '의류', 'subcategory': '방한용품', 'item_name': '담요', 'unit': '개', 'estimated_price': 15000, 'shelf_life_days': 3650},
        {'item_code': 'CLOTHING_002', 'category': '의류', 'subcategory': '방한용품', 'item_name': '핫팩', 'unit': '개', 'estimated_price': 500, 'shelf_life_days': 1095},
        {'item_code': 'CLOTHING_003', 'category': '의류', 'subcategory': '의류', 'item_name': '티셔츠', 'unit': '개', 'estimated_price': 10000, 'shelf_life_days': 3650},
    ]
    
    # UUID 추가
    for item in relief_items_data:
        item['id'] = str(uuid.uuid4())
        item['description'] = f"{item['category']} > {item['subcategory']} > {item['item_name']}"
        item['created_at'] = fake.date_time_between(start_date='-1y', end_date='now')
        item['updated_at'] = fake.date_time_between(start_date='-6m', end_date='now')
    
    return pd.DataFrame(relief_items_data)

# 구호품 마스터 데이터 생성
relief_items_df = create_relief_items_dataframe()
print("\nRelief Items DataFrame:")
print(relief_items_df.head())
print(f"Shape: {relief_items_df.shape}")
print(f"Categories: {relief_items_df['category'].value_counts()}")
```

### 3.3 대피소 데이터 (shelters)

```python
def create_shelters_dataframe(users_df, num_shelters=50):
    """
    대피소 데이터프레임 생성
    """
    # 공무원 사용자 ID 목록
    public_officers = users_df[users_df['user_type'] == 'public_officer']['id'].tolist()
    
    # 서울시 구별 좌표 (예시)
    seoul_districts = [
        {'name': '강남구', 'lat': 37.5173, 'lng': 127.0473},
        {'name': '강동구', 'lat': 37.5301, 'lng': 127.1238},
        {'name': '강북구', 'lat': 37.6398, 'lng': 127.0256},
        {'name': '강서구', 'lat': 37.5509, 'lng': 126.8495},
        {'name': '관악구', 'lat': 37.4784, 'lng': 126.9516},
        {'name': '광진구', 'lat': 37.5384, 'lng': 127.0822},
        {'name': '구로구', 'lat': 37.4954, 'lng': 126.8874},
        {'name': '금천구', 'lat': 37.4569, 'lng': 126.8956},
        {'name': '노원구', 'lat': 37.6541, 'lng': 127.0568},
        {'name': '도봉구', 'lat': 37.6688, 'lng': 127.0471},
    ]
    
    disaster_types = ['지진', '화재', '홍수', '태풍', '기타']
    shelter_types = ['구민회관', '체육관', '학교', '커뮤니티센터', '공원']
    statuses = ['운영중', '포화', '폐쇄']
    
    shelters_data = []
    
    for i in range(num_shelters):
        district = random.choice(seoul_districts)
        shelter_type = random.choice(shelter_types)
        capacity = random.randint(50, 300)
        current_occupancy = random.randint(0, int(capacity * 1.1))  # 가끔 초과 수용
        
        # 수용률에 따른 상태 결정
        if current_occupancy >= capacity:
            status = '포화'
        elif current_occupancy == 0:
            status = random.choice(['운영중', '폐쇄'])
        else:
            status = '운영중'
        
        shelter = {
            'id': str(uuid.uuid4()),
            'shelter_id': f"SH_{i:03d}",
            'manager_id': random.choice(public_officers),
            'shelter_name': f"{district['name']} {shelter_type}",
            'location_address': f"서울시 {district['name']} {fake.street_address()}",
            'latitude': district['lat'] + random.uniform(-0.01, 0.01),
            'longitude': district['lng'] + random.uniform(-0.01, 0.01),
            'disaster_type': random.choice(disaster_types),
            'capacity': capacity,
            'current_occupancy': current_occupancy,
            'has_disabled_facility': random.choice([True, False]),
            'has_pet_zone': random.choice([True, False]),
            'status': status,
            'contact_person': fake.name(),
            'contact_phone': fake.phone_number(),
            'created_at': fake.date_time_between(start_date='-1y', end_date='-1m'),
            'updated_at': fake.date_time_between(start_date='-1m', end_date='now')
        }
        shelters_data.append(shelter)
    
    return pd.DataFrame(shelters_data)

# 대피소 데이터 생성
shelters_df = create_shelters_dataframe(users_df, 50)
print("\nShelters DataFrame:")
print(shelters_df.head())
print(f"Shape: {shelters_df.shape}")
print(f"Disaster types: {shelters_df['disaster_type'].value_counts()}")
print(f"Status: {shelters_df['status'].value_counts()}")
```

## 4. AI/ML 모델을 위한 시계열 데이터 생성

### 4.1 대피소 통계 시계열 데이터 (shelter\_statistics)

```python
def create_shelter_statistics_dataframe(shelters_df, start_date='2024-01-01', end_date='2024-12-31'):
    """
    대피소 통계 시계열 데이터 생성 (LSTM 모델용)
    """
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    statistics_data = []
    
    for _, shelter in shelters_df.iterrows():
        shelter_id = shelter['id']
        base_occupancy = shelter['current_occupancy']
        capacity = shelter['capacity']
        
        for i, date in enumerate(date_range):
            # 계절성 패턴 (겨울에 더 많은 수용)
            seasonal_factor = 20 * np.sin(2 * np.pi * i / 365.25 + np.pi)  # 겨울에 peak
            
            # 주간 패턴 (주말에 약간 감소)
            weekly_factor = -5 if date.weekday() >= 5 else 0
            
            # 재난 발생 시뮬레이션 (가끔 급증)
            disaster_factor = 0
            if random.random() < 0.05:  # 5% 확률로 재난 발생
                disaster_factor = random.randint(30, 100)
            
            # 트렌드 (시간에 따른 변화)
            trend = (i / len(date_range)) * 10
            
            # 노이즈
            noise = np.random.normal(0, 5)
            
            # 최종 수용 인원 계산
            occupancy = base_occupancy + seasonal_factor + weekly_factor + disaster_factor + trend + noise
            occupancy = max(0, min(int(occupancy), int(capacity * 1.2)))  # 0과 최대 수용량의 120% 사이
            
            # 요청 및 충족 건수
            total_requests = np.random.poisson(max(1, occupancy // 10))
            fulfilled_requests = min(total_requests, int(total_requests * random.uniform(0.7, 1.0)))
            pending_requests = total_requests - fulfilled_requests
            
            # 날씨 데이터 시뮬레이션
            base_temp = 15 + 10 * np.sin(2 * np.pi * i / 365.25)  # 계절별 온도
            weather_data = {
                'temperature': round(base_temp + np.random.normal(0, 3), 1),
                'humidity': round(random.uniform(30, 90), 1),
                'precipitation': round(max(0, np.random.exponential(2)), 1),
                'wind_speed': round(random.uniform(0, 15), 1)
            }
            
            # 재난 심각도
            disaster_severity = {
                'level': random.randint(1, 5),
                'type': shelter['disaster_type'],
                'affected_area_km2': round(random.uniform(1, 50), 2)
            }
            
            # 일일 소비량 (구호품별)
            daily_consumption = {
                'food_items': random.randint(occupancy * 2, occupancy * 4),
                'water_bottles': random.randint(occupancy * 3, occupancy * 6),
                'hygiene_items': random.randint(occupancy // 2, occupancy),
                'medical_items': random.randint(0, occupancy // 10)
            }
            
            stat = {
                'id': str(uuid.uuid4()),
                'shelter_id': shelter_id,
                'statistics_date': date.date(),
                'occupancy_count': occupancy,
                'occupancy_rate': round(occupancy / capacity, 4),
                'total_requests': total_requests,
                'fulfilled_requests': fulfilled_requests,
                'pending_requests': pending_requests,
                'avg_fulfillment_time_hours': round(random.uniform(2, 48), 2),
                'daily_consumption': json.dumps(daily_consumption),
                'weather_data': json.dumps(weather_data),
                'disaster_severity': json.dumps(disaster_severity),
                'created_at': datetime.combine(date.date(), datetime.min.time())
            }
            statistics_data.append(stat)
    
    return pd.DataFrame(statistics_data)

# 대피소 통계 시계열 데이터 생성 (처음 5개 대피소만)
shelter_stats_df = create_shelter_statistics_dataframe(shelters_df.head(5))
print("\nShelter Statistics DataFrame:")
print(shelter_stats_df.head())
print(f"Shape: {shelter_stats_df.shape}")
print(f"Date range: {shelter_stats_df['statistics_date'].min()} to {shelter_stats_df['statistics_date'].max()}")
```

### 4.2 소비 패턴 데이터 (consumption\_patterns)

```python
def create_consumption_patterns_dataframe(shelters_df, relief_items_df, start_date='2024-01-01', end_date='2024-12-31'):
    """
    시간별 소비 패턴 데이터 생성 (LSTM 모델용)
    """
    date_range = pd.date_range(start=start_date, end=end_date, freq='H')
    consumption_data = []
    
    # 주요 구호품만 선택 (식량, 물, 위생용품)
    main_items = relief_items_df[relief_items_df['category'].isin(['식량', '생활용품'])].head(10)
    selected_shelters = shelters_df.head(3)  # 처음 3개 대피소만
    
    # 시간대별 소비 패턴 정의
    hourly_consumption_pattern = {
        'food': [0.2, 0.1, 0.1, 0.1, 0.1, 0.3, 0.8, 1.0, 0.6, 0.4, 0.5, 1.2,
                1.0, 0.7, 0.5, 0.4, 0.6, 1.5, 1.2, 0.8, 0.6, 0.5, 0.4, 0.3],
        'water': [0.3, 0.2, 0.1, 0.1, 0.2, 0.4, 1.0, 1.2, 0.8, 0.6, 0.7, 1.0,
                 0.8, 0.6, 0.5, 0.6, 0.8, 1.2, 1.0, 0.8, 0.6, 0.5, 0.4, 0.3],
        'hygiene': [0.1, 0.05, 0.05, 0.05, 0.1, 0.3, 0.5, 0.8, 0.4, 0.2, 0.3, 0.4,
                   0.3, 0.2, 0.2, 0.2, 0.3, 0.6, 0.5, 0.4, 0.3, 0.2, 0.2, 0.1]
    }
    
    for _, shelter in selected_shelters.iterrows():
        for _, item in main_items.iterrows():
            base_consumption = random.randint(5, 20)  # 기본 소비량
            
            # 카테고리별 패턴 선택
            if item['category'] == '식량':
                pattern = hourly_consumption_pattern['food']
            elif item['subcategory'] == '위생용품':
                pattern = hourly_consumption_pattern['hygiene']
            else:
                pattern = hourly_consumption_pattern['water']
            
            for dt in date_range[:24*7]:  # 1주일치만 생성 (데이터 크기 제한)
                hour_factor = pattern[dt.hour]
                
                # 요일별 패턴 (주말에 약간 감소)
                day_factor = 0.8 if dt.weekday() >= 5 else 1.0
                
                # 계절별 패턴
                seasonal_factor = 1.0 + 0.3 * np.sin(2 * np.pi * dt.dayofyear / 365.25)
                
                # 최종 소비량 계산
                consumed = int(base_consumption * hour_factor * day_factor * seasonal_factor * random.uniform(0.7, 1.3))
                consumed = max(0, consumed)
                
                remaining = max(0, random.randint(50, 200) - consumed)
                
                # 외부 요인
                external_factors = {
                    'weather_condition': random.choice(['맑음', '흐림', '비', '눈']),
                    'special_event': random.choice([None, '급식', '의료진방문', '물자배송']) if random.random() < 0.1 else None,
                    'occupancy_level': random.choice(['낮음', '보통', '높음'])
                }
                
                consumption = {
                    'id': str(uuid.uuid4()),
                    'shelter_id': shelter['id'],
                    'relief_item_id': item['id'],
                    'consumption_date': dt.date(),
                    'consumed_quantity': consumed,
                    'remaining_quantity': remaining,
                    'consumption_rate': round(consumed / (consumed + remaining) if (consumed + remaining) > 0 else 0, 4),
                    'day_of_week': dt.weekday() + 1,
                    'hour_of_day': dt.hour,
                    'external_factors': json.dumps(external_factors),
                    'recorded_at': dt
                }
                consumption_data.append(consumption)
    
    return pd.DataFrame(consumption_data)

# 소비 패턴 데이터 생성
consumption_patterns_df = create_consumption_patterns_dataframe(shelters_df, relief_items_df)
print("\nConsumption Patterns DataFrame:")
print(consumption_patterns_df.head())
print(f"Shape: {consumption_patterns_df.shape}")
```

## 5. 추천 알고리즘을 위한 사용자 행동 데이터

### 5.1 사용자 행동 로그 (user\_behaviors)

```python
def create_user_behaviors_dataframe(users_df, shelters_df, relief_items_df, num_sessions_per_user=10):
    """
    사용자 행동 로그 데이터 생성 (추천 알고리즘용)
    """
    behaviors_data = []
    
    # 일반 사용자만 선택
    general_users = users_df[users_df['user_type'] == 'general_user'].head(100)  # 처음 100명만
    
    action_types = ['view', 'click', 'search', 'filter', 'donate', 'bookmark']
    entity_types = ['shelter', 'relief_item', 'donation']
    
    for _, user in general_users.iterrows():
        user_id = user['id']
        
        # 사용자별 선호도 시뮬레이션
        preferred_categories = random.sample(['식량', '생활용품', '의약품', '의류'], k=random.randint(1, 3))
        preferred_disaster_types = random.sample(['지진', '화재', '홍수', '태풍'], k=random.randint(1, 2))
        
        for session in range(num_sessions_per_user):
            session_id = f"sess_{user_id}_{session}"
            session_start = fake.date_time_between(start_date='-6m', end_date='now')
            
            # 세션 내 행동 수 (1-15개)
            num_actions = np.random.poisson(5) + 1
            
            for action_idx in range(num_actions):
                action_time = session_start + timedelta(minutes=action_idx * random.randint(1, 10))
                
                # 행동 타입 결정 (view가 가장 많음)
                action_type = np.random.choice(action_types, p=[0.4, 0.25, 0.15, 0.1, 0.05, 0.05])
                
                # 대상 엔티티 타입 결정
                entity_type = np.random.choice(entity_types, p=[0.5, 0.3, 0.2])
                
                # 대상 엔티티 ID 결정
                if entity_type == 'shelter':
                    # 선호하는 재난 타입의 대피소 선택 확률 높임
                    available_shelters = shelters_df[shelters_df['disaster_type'].isin(preferred_disaster_types)]
                    if len(available_shelters) == 0:
                        available_shelters = shelters_df
                    target_entity_id = random.choice(available_shelters['id'].tolist())
                elif entity_type == 'relief_item':
                    # 선호하는 카테고리의 구호품 선택 확률 높임
                    available_items = relief_items_df[relief_items_df['category'].isin(preferred_categories)]
                    if len(available_items) == 0:
                        available_items = relief_items_df
                    target_entity_id = random.choice(available_items['id'].tolist())
                else:
                    target_entity_id = str(uuid.uuid4())  # 가상의 기부 ID
                
                # 행동 상세 정보
                action_details = {
                    'page_url': f"/{entity_type}/{target_entity_id}",
                    'referrer': random.choice(['direct', 'search', 'recommendation', 'social']),
                    'device_type': random.choice(['desktop', 'mobile', 'tablet']),
                    'browser': random.choice(['chrome', 'firefox', 'safari', 'edge'])
                }
                
                if action_type == 'search':
                    action_details['search_query'] = random.choice(preferred_categories + ['긴급', '재난', '도움'])
                elif action_type == 'filter':
                    action_details['filter_criteria'] = {
                        'category': random.choice(preferred_categories),
                        'location': random.choice(['서울', '경기', '인천']),
                        'urgency': random.choice(['높음', '중간', '낮음'])
                    }
                
                behavior = {
                    'id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'action_type': action_type,
                    'target_entity_type': entity_type,
                    'target_entity_id': target_entity_id,
                    'action_details': json.dumps(action_details),
                    'session_id': session_id,
                    'ip_address': fake.ipv4(),
                    'user_agent': fake.user_agent(),
                    'action_timestamp': action_time,
                    'duration_seconds': random.randint(5, 300)
                }
                behaviors_data.append(behavior)
    
    return pd.DataFrame(behaviors_data)

# 사용자 행동 데이터 생성
user_behaviors_df = create_user_behaviors_dataframe(users_df, shelters_df, relief_items_df)
print("\nUser Behaviors DataFrame:")
print(user_behaviors_df.head())
print(f"Shape: {user_behaviors_df.shape}")
print(f"Action types: {user_behaviors_df['action_type'].value_counts()}")
```

### 5.2 사용자 선호도 데이터 (user\_preferences)

```python
def create_user_preferences_dataframe(users_df, user_behaviors_df):
    """
    사용자 선호도 데이터 생성
    """
    preferences_data = []
    
    # 일반 사용자만 선택
    general_users = users_df[users_df['user_type'] == 'general_user']
    
    for _, user in general_users.iterrows():
        user_id = user['id']
        
        # 해당 사용자의 행동 데이터 분석
        user_actions = user_behaviors_df[user_behaviors_df['user_id'] == user_id]
        
        # 선호 카테고리 (행동 빈도 기반)
        preferred_categories = random.sample(['식량', '생활용품', '의약품', '의류'], k=random.randint(1, 4))
        category_weights = {cat: random.uniform(0.1, 1.0) for cat in preferred_categories}
        
        # 선호 지역
        preferred_locations = random.sample(['강남구', '강서구', '마포구', '종로구', '영등포구'], k=random.randint(1, 3))
        
        # 기부 빈도 패턴
        donation_frequency = {
            'frequency_type': random.choice(['weekly', 'monthly', 'quarterly', 'irregular']),
            'avg_amount': random.randint(10000, 100000),
            'preferred_day': random.choice(['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']),
            'preferred_time': random.choice(['morning', 'afternoon', 'evening'])
        }
        
        # 상호작용 패턴
        interaction_patterns = {
            'avg_session_duration': random.randint(300, 1800),  # 5-30분
            'pages_per_session': random.randint(3, 15),
            'conversion_rate': random.uniform(0.01, 0.1),  # 1-10%
            'preferred_device': random.choice(['desktop', 'mobile', 'tablet']),
            'active_hours': random.sample(list(range(24)), k=random.randint(6, 12))
        }
        
        preference = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'preferred_categories': json.dumps(category_weights),
            'preferred_locations': json.dumps(preferred_locations),
            'max_budget': random.randint(50000, 500000),
            'donation_frequency': json.dumps(donation_frequency),
            'interaction_patterns': json.dumps(interaction_patterns),
            'last_updated': fake.date_time_between(start_date='-1m', end_date='now')
        }
        preferences_data.append(preference)
    
    return pd.DataFrame(preferences_data)

# 사용자 선호도 데이터 생성
user_preferences_df = create_user_preferences_dataframe(users_df, user_behaviors_df)
print("\nUser Preferences DataFrame:")
print(user_preferences_df.head())
print(f"Shape: {user_preferences_df.shape}")
```

## 6. 기부 및 매칭 데이터 생성

### 6.1 기부 데이터 (donations, donation\_items)

```python
def create_donations_dataframe(users_df, relief_items_df, num_donations=500):
    """
    기부 및 기부 품목 데이터 생성
    """
    # 일반 사용자만 선택
    general_users = users_df[users_df['user_type'] == 'general_user']
    
    donations_data = []
    donation_items_data = []
    
    statuses = ['등록', '매칭중', '배송중', '완료', '취소']
    status_weights = [0.1, 0.2, 0.3, 0.35, 0.05]  # 완료가 가장 많음
    
    for i in range(num_donations):
        user_id = random.choice(general_users['id'].tolist())
        status = np.random.choice(statuses, p=status_weights)
        
        # 기부 생성
        donation_id = f"DON_{i:05d}"
        created_at = fake.date_time_between(start_date='-6m', end_date='now')
        
        # 상태에 따른 완료 시간 설정
        completed_at = None
        if status == '완료':
            completed_at = created_at + timedelta(days=random.randint(1, 14))
        
        donation = {
            'id': str(uuid.uuid4()),
            'donation_id': donation_id,
            'user_id': user_id,
            'status': status,
            'total_budget': random.randint(20000, 200000),
            'notes': fake.text(max_nb_chars=100) if random.random() < 0.3 else None,
            'created_at': created_at,
            'updated_at': fake.date_time_between(start_date=created_at, end_date='now'),
            'completed_at': completed_at
        }
        donations_data.append(donation)
        
        # 기부 품목 생성 (1-5개)
        num_items = random.randint(1, 5)
        selected_items = relief_items_df.sample(n=num_items)
        
        for _, item in selected_items.iterrows():
            donation_item = {
                'id': str(uuid.uuid4()),
                'donation_id': donation['id'],
                'relief_item_id': item['id'],
                'quantity': random.randint(1, 50),
                'unit_price': item['estimated_price'] * random.uniform(0.8, 1.2),  # 가격 변동
                'created_at': created_at
            }
            donation_items_data.append(donation_item)
    
    return pd.DataFrame(donations_data), pd.DataFrame(donation_items_data)

# 기부 데이터 생성
donations_df, donation_items_df = create_donations_dataframe(users_df, relief_items_df)
print("\nDonations DataFrame:")
print(donations_df.head())
print(f"Shape: {donations_df.shape}")
print(f"Status distribution: {donations_df['status'].value_counts()}")

print("\nDonation Items DataFrame:")
print(donation_items_df.head())
print(f"Shape: {donation_items_df.shape}")
```

## 7. 데이터 관계성 검증 및 분석

### 7.1 데이터 무결성 검증

```python
def validate_data_integrity():
    """
    생성된 데이터의 무결성 검증
    """
    print("=== 데이터 무결성 검증 ===")
    
    # 1. 외래키 관계 검증
    print("\n1. 외래키 관계 검증:")
    
    # 대피소의 manager_id가 공무원 사용자인지 확인
    public_officers = set(users_df[users_df['user_type'] == 'public_officer']['id'])
    shelter_managers = set(shelters_df['manager_id'])
    invalid_managers = shelter_managers - public_officers
    print(f"   - 대피소 관리자 중 공무원이 아닌 사용자: {len(invalid_managers)}개")
    
    # 기부자가 일반 사용자인지 확인
    general_users = set(users_df[users_df['user_type'] == 'general_user']['id'])
    donors = set(donations_df['user_id'])
    invalid_donors = donors - general_users
    print(f"   - 기부자 중 일반 사용자가 아닌 사용자: {len(invalid_donors)}개")
    
    # 2. 데이터 범위 검증
    print("\n2. 데이터 범위 검증:")
    
    # 대피소 수용률 검증
    over_capacity = shelters_df[shelters_df['current_occupancy'] > shelters_df['capacity']]
    print(f"   - 수용량 초과 대피소: {len(over_capacity)}개")
    
    # 음수 값 검증
    negative_occupancy = shelters_df[shelters_df['current_occupancy'] < 0]
    print(f"   - 음수 수용 인원: {len(negative_occupancy)}개")
    
    # 3. 시계열 데이터 연속성 검증
    print("\n3. 시계열 데이터 연속성:")
    
    # 대피소별 통계 데이터 날짜 연속성
    for shelter_id in shelter_stats_df['shelter_id'].unique()[:3]:
        shelter_dates = shelter_stats_df[shelter_stats_df['shelter_id'] == shelter_id]['statistics_date']
        date_gaps = pd.to_datetime(shelter_dates).sort_values().diff().dt.days
        max_gap = date_gaps.max()
        print(f"   - 대피소 {shelter_id[:8]}... 최대 날짜 간격: {max_gap}일")

validate_data_integrity()
```

### 7.2 AI/ML 모델용 데이터 준비

```python
def prepare_lstm_training_data(shelter_stats_df, consumption_patterns_df):
    """
    LSTM 모델 학습용 데이터 준비
    """
    print("\n=== LSTM 모델 학습용 데이터 준비 ===")
    
    # 1. 시계열 특성 추출
    lstm_features = []
    
    for shelter_id in shelter_stats_df['shelter_id'].unique():
        shelter_data = shelter_stats_df[shelter_stats_df['shelter_id'] == shelter_id].copy()
        shelter_data = shelter_data.sort_values('statistics_date')
        
        # 날짜 특성 추가
        shelter_data['day_of_week'] = pd.to_datetime(shelter_data['statistics_date']).dt.dayofweek
        shelter_data['month'] = pd.to_datetime(shelter_data['statistics_date']).dt.month
        shelter_data['day_of_year'] = pd.to_datetime(shelter_data['statistics_date']).dt.dayofyear
        
        # 이동 평균 특성
        shelter_data['occupancy_ma_7'] = shelter_data['occupancy_count'].rolling(window=7, min_periods=1).mean()
        shelter_data['occupancy_ma_30'] = shelter_data['occupancy_count'].rolling(window=30, min_periods=1).mean()
        
        # 변화율 특성
        shelter_data['occupancy_change'] = shelter_data['occupancy_count'].pct_change().fillna(0)
        
        # 날씨 데이터 파싱
        weather_df = pd.json_normalize(shelter_data['weather_data'].apply(json.loads))
        shelter_data = pd.concat([shelter_data.reset_index(drop=True), weather_df], axis=1)
        
        lstm_features.append(shelter_data)
    
    lstm_df = pd.concat(lstm_features, ignore_index=True)
    
    print(f"LSTM 학습용 데이터 형태: {lstm_df.shape}")
    print(f"특성 컬럼: {lstm_df.select_dtypes(include=[np.number]).columns.tolist()}")
    
    return lstm_df

def prepare_recommendation_training_data(user_behaviors_df, user_preferences_df):
    """
    추천 알고리즘 학습용 데이터 준비
    """
    print("\n=== 추천 알고리즘 학습용 데이터 준비 ===")
    
    # 1. 사용자-아이템 상호작용 매트릭스
    user_item_matrix = user_behaviors_df.pivot_table(
        index='user_id',
        columns='target_entity_id',
        values='duration_seconds',
        aggfunc='sum',
        fill_value=0
    )
    
    print(f"사용자-아이템 매트릭스 형태: {user_item_matrix.shape}")
    
    # 2. 사용자 특성 벡터
    user_features = []
    
    for _, user_pref in user_preferences_df.iterrows():
        user_id = user_pref['user_id']
        
        # 선호도 데이터 파싱
        preferred_categories = json.loads(user_pref['preferred_categories'])
        interaction_patterns = json.loads(user_pref['interaction_patterns'])
        
        # 행동 통계
        user_actions = user_behaviors_df[user_behaviors_df['user_id'] == user_id]
        
        feature_vector = {
            'user_id': user_id,
            'max_budget': user_pref['max_budget'],
            'total_actions': len(user_actions),
            'unique_items_viewed': user_actions['target_entity_id'].nunique(),
            'avg_session_duration': interaction_patterns.get('avg_session_duration', 0),
            'conversion_rate': interaction_patterns.get('conversion_rate', 0),
            'food_preference': preferred_categories.get('식량', 0),
            'hygiene_preference': preferred_categories.get('생활용품', 0),
            'medical_preference': preferred_categories.get('의약품', 0)
        }
        
        user_features.append(feature_vector)
    
    user_features_df = pd.DataFrame(user_features)
    
    print(f"사용자 특성 데이터 형태: {user_features_df.shape}")
    print(f"특성 컬럼: {user_features_df.columns.tolist()}")
    
    return user_item_matrix, user_features_df

# AI/ML 모델용 데이터 준비
lstm_data = prepare_lstm_training_data(shelter_stats_df, consumption_patterns_df)
user_item_matrix, user_features_df = prepare_recommendation_training_data(user_behaviors_df, user_preferences_df)
```

## 8. 데이터 저장 및 활용 가이드

### 8.1 CSV 파일로 저장

```python
def save_dataframes_to_csv():
    """
    생성된 데이터프레임을 CSV 파일로 저장
    """
    import os
    
    # 저장 디렉토리 생성
    output_dir = 'generated_data'
    os.makedirs(output_dir, exist_ok=True)
    
    # 기본 테이블
    users_df.to_csv(f'{output_dir}/users.csv', index=False, encoding='utf-8-sig')
    relief_items_df.to_csv(f'{output_dir}/relief_items.csv', index=False, encoding='utf-8-sig')
    shelters_df.to_csv(f'{output_dir}/shelters.csv', index=False, encoding='utf-8-sig')
    donations_df.to_csv(f'{output_dir}/donations.csv', index=False, encoding='utf-8-sig')
    donation_items_df.to_csv(f'{output_dir}/donation_items.csv', index=False, encoding='utf-8-sig')
    
    # AI/ML 특화 테이블
    shelter_stats_df.to_csv(f'{output_dir}/shelter_statistics.csv', index=False, encoding='utf-8-sig')
    consumption_patterns_df.to_csv(f'{output_dir}/consumption_patterns.csv', index=False, encoding='utf-8-sig')
    user_behaviors_df.to_csv(f'{output_dir}/user_behaviors.csv', index=False, encoding='utf-8-sig')
    user_preferences_df.to_csv(f'{output_dir}/user_preferences.csv', index=False, encoding='utf-8-sig')
    
    # 모델 학습용 데이터
    lstm_data.to_csv(f'{output_dir}/lstm_training_data.csv', index=False, encoding='utf-8-sig')
    user_features_df.to_csv(f'{output_dir}/user_features.csv', index=False, encoding='utf-8-sig')
    
    print(f"모든 데이터프레임이 '{output_dir}' 디렉토리에 저장되었습니다.")
    
    # 파일 크기 정보
    for filename in os.listdir(output_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(output_dir, filename)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  - {filename}: {size_mb:.2f} MB")

# 데이터 저장
save_dataframes_to_csv()
```

### 8.2 데이터 활용 예시

```python
def demonstrate_data_usage():
    """
    생성된 데이터 활용 예시
    """
    print("\n=== 데이터 활용 예시 ===")
    
    # 1. 대피소별 수용률 분석
    print("\n1. 대피소별 수용률 분석:")
    occupancy_analysis = shelters_df.groupby('disaster_type').agg({
        'occupancy_rate': ['mean', 'std', 'min', 'max'],
        'capacity': 'sum',
        'current_occupancy': 'sum'
    }).round(3)
    print(occupancy_analysis)
    
    # 2. 시계열 트렌드 분석
    print("\n2. 월별 수용 인원 트렌드:")
    shelter_stats_df['month'] = pd.to_datetime(shelter_stats_df['statistics_date']).dt.month
    monthly_trend = shelter_stats_df.groupby('month')['occupancy_count'].mean().round(1)
    print(monthly_trend)
    
    # 3. 사용자 행동 패턴 분석
    print("\n3. 시간대별 사용자 활동:")
    user_behaviors_df['hour'] = pd.to_datetime(user_behaviors_df['action_timestamp']).dt.hour
    hourly_activity = user_behaviors_df.groupby('hour').size()
    peak_hours = hourly_activity.nlargest(3)
    print(f"가장 활발한 시간대: {peak_hours.index.tolist()}시")
    
    # 4. 기부 패턴 분석
    print("\n4. 기부 완료율:")
    completion_rate = (donations_df['status'] == '완료').mean() * 100
    print(f"기부 완료율: {completion_rate:.1f}%")
    
    # 5. 구호품 인기도 분석
    print("\n5. 인기 구호품 TOP 5:")
    popular_items = donation_items_df.groupby('relief_item_id')['quantity'].sum().nlargest(5)
    for item_id, quantity in popular_items.items():
        item_name = relief_items_df[relief_items_df['id'] == item_id]['item_name'].iloc[0]
        print(f"  - {item_name}: {quantity}개")

demonstrate_data_usage()
```

## 9. 결론 및 다음 단계

### 9.1 생성된 데이터 요약

이 가이드를 통해 다음과 같은 데이터프레임을 생성했습니다:

1. **기본 마스터 데이터**

   * `users_df`: 사용자 정보 (1,000명)

   * `relief_items_df`: 구호품 마스터 (21개 품목)

   * `shelters_df`: 대피소 정보 (50개)

2. **운영 데이터**

   * `donations_df`: 기부 정보 (500건)

   * `donation_items_df`: 기부 품목 상세

3. **AI/ML 특화 데이터**

   * `shelter_stats_df`: 대피소 일별 통계 (시계열)

   * `consumption_patterns_df`: 시간별 소비 패턴

   * `user_behaviors_df`: 사용자 행동 로그

   * `user_preferences_df`: 사용자 선호도

4. **모델 학습용 데이터**

   * `lstm_data`: LSTM 모델 학습용 특성 데이터

   * `user_features_df`: 추천 알고리즘용 사용자 특성

### 9.2 다음 단계 권장사항

1. **데이터 품질 개선**

   * 실제 재난 데이터를 참고하여 더 현실적인 패턴 구현

   * 지역별, 계절별 특성을 더 정교하게 반영

2. **모델 개발**

   * LSTM 모델: 다변량 시계열 예측 구현

   * 추천 알고리즘: 협업 필터링 및 콘텐츠 기반 필터링 구현

3. **데이터 확장**

   * 더 많은 대피소와 사용자 데이터 생성

   * 실시간 스트리밍 데이터 시뮬레이션

4. **성능 최적화**

   * 대용량 데이터 처리를 위한 파티셔닝 구현

   * 인덱싱 및 쿼리 최적화

이 데이터를 기반으로 이어드림 플랫폼의 AI/ML 모델을 효과적으로 학습시키고, 실제 서비스에서 정확한 예측과 추천을 제공할 수 있습니다.
