#!/usr/bin/env python3
"""가상 데이터 생성기 - 개선된 버전

Faker(ko_KR)을 사용해 첨부된 데이터 스키마에 맞춘 가상 데이터를 생성하여
JSON 파일로 출력합니다. 실제 대피소 데이터와 연계하여 유기적인 데이터를 생성합니다.

사용법:
  python tools\\generate_fake_data_improved.py --real_shelter_csv "tools\\대피소추가_API\\shelter_schema_전국.csv"

출력: 프로젝트 루트의 output/ 폴더에 각 테이블별 json 파일 생성
"""
import argparse
import json
import os
import random
import math
from datetime import datetime, timedelta, timezone
from faker import Faker


KO_LAT_MIN, KO_LAT_MAX = 33.0, 38.6
KO_LON_MIN, KO_LON_MAX = 124.6, 131.9


def now_iso():
    # timezone-aware UTC ISO8601, 기존 출력과 호환되도록 Z 접미 유지
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def rand_coords():
    return round(random.uniform(KO_LAT_MIN, KO_LAT_MAX), 6), round(random.uniform(KO_LON_MIN, KO_LON_MAX), 6)


def make_id(prefix, i):
    return f"{prefix}_{i:06d}"


def calculate_distance(lat1, lon1, lat2, lon2):
    """두 지점 간의 거리를 계산 (단위: km)"""
    R = 6371  # 지구 반지름 (km)
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def generate_users(fake, count):
    """사용자 데이터 생성 - public_officer와 general_user 비율 조정"""
    users = []
    # public_officer는 0.1%, general_user는 99.9%
    officer_count = max(1, int(count * 0.001))
    
    for i in range(1, count + 1):
        uid = make_id('user', i)
        name = fake.name()
        email = fake.safe_email()
        phone = fake.phone_number()
        zipcode = fake.postcode()
        addr = fake.street_address()
        road_addr = fake.address().split('\n')[0]
        created = fake.date_time_between(start_date='-2y', end_date='now')
        
        # 관리자/일반 사용자 비율 조정
        user_type = 'public_officer' if i <= officer_count else 'general_user'
        
        users.append({
            'user_id': uid,
            'email': email,
            'user_type': user_type,
            'name': name,
            'phone_number': phone,
            'zipcode': zipcode,
            'road_address': road_addr,
            'address_detail': addr,
            'preferred_categories': '',  # 기부 이력에 따라 나중에 업데이트
            'created_at': created.isoformat(),
            'updated_at': created.isoformat(),
            'last_login_at': (created + timedelta(days=random.randint(0, 365))).isoformat(),
        })
    return users


def generate_relief_items(fake, count):
    """구호품 데이터 생성 - 재난 상황에 맞춘 다양한 카테고리"""
    base_categories = [
        ('식량', ['즉석식품', '통조림', '가공식품', '음료수', '이유식', '건조식품', '비상식량']),
        ('생활용품', ['화장지', '위생용품', '세제', '샴푸', '칫솔', '수건', '비누', '기저귀']),
        ('의류', ['아우터', '내의', '양말', '신발', '모자', '장갑', '우의', '담요']),
        ('의약품', ['기본구급', '상처치료', '해열제', '소화제', '감기약', '연고', '붕대', '소독약']),
        ('침구류', ['이불', '베개', '매트리스', '수면용품', '침낭', '요', '텐트', '방수포']),
        ('전자용품', ['휴대폰충전기', '손전등', '라디오', '배터리', '보조배터리', '선풍기', '전열기구']),
        ('주방용품', ['일회용식기', '컵', '물통', '보온병', '가스버너', '라이터', '냄비', '젓가락']),
        ('개인위생', ['마스크', '손소독제', '생리용품', '면도기', '휴지', '물티슈', '샤워용품']),
        ('교육/오락', ['학용품', '도서', '장난감', '색연필', '공책', '게임', '퍼즐', '체육용품']),
        ('반려동물', ['사료', '간식', '목줄', '배변패드', '장난감', '이동장', '의료용품', '급수대'])
    ]
    
    items = []
    i = 1
    
    # 각 카테고리별로 골고루 생성
    for category, subcategories in base_categories:
        for subcategory in subcategories:
            if i > count:
                break
            item_id = make_id('relief_item', i)
            name = f"{subcategory} 세트"
            if subcategory in ['즉석식품', '통조림']:
                name = f"{subcategory} (10개입)"
            elif subcategory in ['화장지', '기저귀']:
                name = f"{subcategory} (대용량)"
            
            items.append({
                'item_id': item_id,
                'item_code': f"{category[:2].upper()}_{i:03d}",
                'category': category,
                'subcategory': subcategory,
                'item_name': name,
                'description': f"{category} > {subcategory} > {name}",
                'unit': random.choice(['개', '박스', '세트', '팩', '병']),
                'created_at': now_iso(),
                'updated_at': now_iso(),
            })
            i += 1
            if i > count:
                break
    
    # 부족한 만큼 추가 생성
    while len(items) < count and i <= count:
        category, subcategories = random.choice(base_categories)
        subcategory = random.choice(subcategories)
        item_id = make_id('relief_item', i)
        items.append({
            'item_id': item_id,
            'item_code': f"{category[:2].upper()}_{i:03d}",
            'category': category,
            'subcategory': subcategory,
            'item_name': f"{subcategory} (추가분)",
            'description': f"{category} > {subcategory}",
            'unit': random.choice(['개', '박스', '세트']),
            'created_at': now_iso(),
            'updated_at': now_iso(),
        })
        i += 1
    
    return items[:count]


def generate_shelters(fake, count, users, real_shelter_csv_path=None):
    """
    대피소 데이터 생성 - 실제 API 데이터가 있으면 그것만 사용, 없으면 가상 데이터 생성
    """
    shelters = []
    
    # 실제 API 데이터가 있으면 그것만 사용
    if real_shelter_csv_path and os.path.exists(real_shelter_csv_path):
        try:
            import pandas as pd
            real_df = pd.read_csv(real_shelter_csv_path, encoding='utf-8-sig')
            print(f"✅ 실제 대피소 데이터 {len(real_df)}개를 사용합니다 (가상 데이터 생성 안함)")
            
            # public_officer만 manager로 할당
            public_officers = [u for u in users if u['user_type'] == 'public_officer']
            if not public_officers:
                public_officers = [users[0]] if users else []  # fallback
            
            for _, row in real_df.iterrows():
                # manager_id를 public_officer 중에서 할당
                manager = random.choice(public_officers)['user_id'] if public_officers else make_id('user', 1)
                
                shelters.append({
                    'shelter_id': row['shelter_id'],
                    'manager_id': manager,
                    'shelter_name': row['shelter_name'],
                    'disaster_type': row['disaster_type'],
                    'status': row['status'],
                    'address': row['address'],
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude']),
                    'total_capacity': int(row['total_capacity']),
                    'current_occupancy': 0,  # 요청에 따라 0으로 설정
                    'occupancy_rate': 0.0,   # 요청에 따라 0으로 설정
                    'has_disabled_facility': bool(row['has_disabled_facility']),
                    'has_pet_zone': bool(row['has_pet_zone']),
                    'amenities': str(row['amenities']),
                    'contact_person': str(row['contact_person']),
                    'contact_phone': str(row['contact_phone']),
                    'contact_email': str(row['contact_email']),
                    'total_requests': 0,      # 초기값 0
                    'fulfilled_requests': 0,  # 초기값 0
                    'pending_requests': 0,    # 초기값 0
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                })
                
        except Exception as e:
            print(f"❌ 실제 대피소 데이터 로드 실패: {e}")
            print(f"가상 데이터 {count}개로 대체 생성합니다")
            shelters = generate_fake_shelters(fake, count, users)
    else:
        print(f"실제 대피소 데이터가 없어 가상 데이터 {count}개를 생성합니다")
        shelters = generate_fake_shelters(fake, count, users)
    
    print(f"총 대피소 데이터: {len(shelters)}개")
    return shelters


def generate_fake_shelters(fake, count, users):
    """가상 대피소 데이터만 생성하는 함수"""
    shelters = []
    public_officers = [u for u in users if u['user_type'] == 'public_officer']
    if not public_officers:
        public_officers = [users[0]] if users else []
        
    for i in range(1, count + 1):
        sid = make_id('shelter', i)
        manager = random.choice(public_officers)['user_id'] if public_officers else make_id('user', 1)
        lat, lon = rand_coords()
        total_capacity = random.randint(50, 1000)
        created = fake.date_time_between(start_date='-2y', end_date='now')
        
        shelters.append({
            'shelter_id': sid,
            'manager_id': manager,
            'shelter_name': fake.company() + ' 대피소',
            'disaster_type': random.choice(['지진', '홍수', '태풍', '화재', '한파', '폭염']),
            'status': random.choice(['운영중', '포화', '폐쇄']),
            'address': fake.address().split('\n')[0],
            'latitude': lat,
            'longitude': lon,
            'total_capacity': total_capacity,
            'current_occupancy': 0,   # 요청에 따라 0으로 설정
            'occupancy_rate': 0.0,    # 요청에 따라 0으로 설정
            'has_disabled_facility': random.choice([True, False]),
            'has_pet_zone': random.choice([True, False]),
            'amenities': ','.join(random.sample(['의료실', '급식실', '샤워실', '휴게실'], k=2)),
            'contact_person': fake.name(),
            'contact_phone': fake.phone_number(),
            'contact_email': fake.safe_email(),
            'total_requests': 0,      # 초기값 0
            'fulfilled_requests': 0,  # 초기값 0  
            'pending_requests': 0,    # 초기값 0
            'created_at': created.isoformat(),
            'updated_at': created.isoformat(),
        })
    
    return shelters


def generate_user_donation_wishes(fake, count, users, relief_items):
    """기부 의사 데이터 생성 - general_user만 기부 가능
    - 구호품 카테고리 다양성 반영(가중치)
    - 계절성 반영(여름/겨울 수요 차등)
    - 아이템 단위/카테고리에 따른 수량 범위 정교화
    """
    wishes = []

    # general_user만 필터링
    general_users = [u for u in users if u['user_type'] == 'general_user']
    if not general_users:
        print("⚠️ general_user가 없어 기부 의사 데이터를 생성할 수 없습니다.")
        return []

    # 계절 판단 도우미
    def get_season(dt: datetime):
        m = dt.month
        if m in (12, 1, 2):
            return '겨울'
        if m in (3, 4, 5):
            return '봄'
        if m in (6, 7, 8):
            return '여름'
        return '가을'

    # 카테고리별 기본 가중치(현실 비율 가정)
    base_weights = {
        '식량': 0.32,
        '생활용품': 0.18,
        '의류': 0.08,
        '의약품': 0.15,
        '침구류': 0.06,
        '전자용품': 0.04,
        '주방용품': 0.05,
        '개인위생': 0.07,
        '교육/오락': 0.03,
        '반려동물': 0.02,
    }

    # 아이템 인덱싱
    items_by_category = {}
    for it in relief_items:
        items_by_category.setdefault(it['category'], []).append(it)

    # 사용자별 선호 카테고리 추적
    user_categories = {}

    def pick_category(weights: dict):
        total = sum(weights.values())
        r = random.random() * total
        acc = 0.0
        for k, w in weights.items():
            acc += w
            if r <= acc:
                return k
        return list(weights.keys())[-1]

    def quantity_range_for(item):
        cat = item['category']
        unit = item.get('unit', '')
        if cat in ['식량', '생활용품']:
            return (10, 120) if unit in ['개', '팩'] else (2, 20)
        if cat in ['의류', '침구류']:
            return (2, 40)
        if cat in ['전자용품', '주방용품']:
            return (1, 15)
        if cat in ['의약품']:
            return (5, 60)
        if cat in ['개인위생']:
            return (10, 100)
        if cat in ['교육/오락', '반려동물']:
            return (1, 20)
        return (1, 30)

    for i in range(1, count + 1):
        wid = make_id('wish', i)
        user = random.choice(general_users)
        user_id = user['user_id']

        created = fake.date_time_between(start_date='-6m', end_date='now')
        season = get_season(created)

        # 계절 보정치(겨울엔 침구/의류/의약품↑, 여름엔 생활용품/개인위생/음료↑)
        weights = dict(base_weights)
        if season == '겨울':
            weights['침구류'] *= 1.8
            weights['의류'] *= 1.4
            weights['의약품'] *= 1.2
        elif season == '여름':
            weights['개인위생'] *= 1.5
            weights['생활용품'] *= 1.2
            weights['식량'] *= 1.1

        # 사용자의 기존 선호가 있으면 해당 카테고리를 소폭 가중
        if user.get('preferred_categories'):
            for pc in user['preferred_categories'].split(','):
                if pc in weights:
                    weights[pc] *= 1.25

        # 카테고리 선택 후 아이템 선택
        chosen_category = pick_category(weights)
        pool = items_by_category.get(chosen_category) or relief_items
        item = random.choice(pool)

        # 수량 결정
        lo, hi = quantity_range_for(item)
        qty = random.randint(lo, hi)

        remaining = max(0, qty - random.randint(0, qty))

        # 사용자 선호 업데이트 후보군 저장
        user_categories.setdefault(user_id, set()).add(item['category'])

        wishes.append({
            'wish_id': wid,
            'user_id': user_id,
            'relief_item_id': item['item_id'],
            'quantity': qty,
            'status': random.choices(['대기중', '매칭완료', '배송중', '완료', '취소'], weights=[0.45, 0.2, 0.15, 0.15, 0.05])[0],
            'matched_request_ids': '',
            'total_matched_quantity': qty - remaining,
            'remaining_quantity': remaining,
            'created_at': created.isoformat(),
            'updated_at': created.isoformat(),
            'expires_at': (created + timedelta(days=random.randint(15, 120))).isoformat(),
        })

    # 사용자의 preferred_categories 업데이트
    for user in general_users:
        if user['user_id'] in user_categories:
            user['preferred_categories'] = ','.join(sorted(user_categories[user['user_id']]))

    return wishes


def generate_shelter_relief_requests(fake, count, shelters, relief_items, wishes=None):
    """대피소 구호품 요청 데이터 생성 - 현실적인 수요량 고려(고도화)
    - 대피소 수용규모/편의시설/재난유형/계절 반영
    - 카테고리별 요청량 범위 정교화
    """
    requests = []

    # 인덱싱
    items_by_category = {}
    for it in relief_items:
        items_by_category.setdefault(it['category'], []).append(it)

    # 기부 인기 아이템 가중치(아이템별 등장 횟수)
    wish_item_pop = {}
    if wishes:
        for w in wishes:
            wid = w.get('relief_item_id')
            if wid:
                wish_item_pop[wid] = wish_item_pop.get(wid, 0) + 1

    # 계절 판단 도우미
    def get_season(dt: datetime):
        m = dt.month
        if m in (12, 1, 2):
            return '겨울'
        if m in (3, 4, 5):
            return '봄'
        if m in (6, 7, 8):
            return '여름'
        return '가을'

    # 재난유형→선호 카테고리 맵
    disaster_pref = {
        '지진': {'의약품': 1.5, '침구류': 1.3, '식량': 1.2},
        '홍수': {'개인위생': 1.6, '생활용품': 1.3, '식량': 1.2},
        '태풍': {'식량': 1.3, '주방용품': 1.2, '전자용품': 1.1},
        '화재': {'의약품': 1.6, '의류': 1.3, '침구류': 1.2},
        '한파': {'침구류': 1.8, '의류': 1.4, '의약품': 1.2},
        '폭염': {'개인위생': 1.6, '식량': 1.2, '전자용품': 1.1},
    }

    base_weights = {
        '식량': 0.30,
        '생활용품': 0.17,
        '의류': 0.08,
        '의약품': 0.15,
        '침구류': 0.06,
        '전자용품': 0.05,
        '주방용품': 0.06,
        '개인위생': 0.08,
        '교육/오락': 0.03,
        '반려동물': 0.02,
    }

    def pick_category(weights: dict):
        total = sum(weights.values())
        r = random.random() * total
        acc = 0.0
        for k, w in weights.items():
            acc += w
            if r <= acc:
                return k
        return list(weights.keys())[-1]

    def requested_range_for(cat: str, capacity: int):
        base_need = max(10, int(capacity * 0.1))
        if cat in ['식량', '생활용품']:
            return (base_need, base_need * 5)
        if cat in ['의류', '침구류']:
            return (base_need // 2, base_need * 2)
        if cat in ['의약품', '개인위생']:
            return (base_need // 2, int(base_need * 2.5))
        if cat in ['주방용품', '전자용품']:
            return (max(5, base_need // 3), max(20, int(base_need * 1.2)))
        return (max(5, base_need // 3), base_need)

    for i in range(1, count + 1):
        rid = make_id('request', i)
        shelter = random.choice(shelters)
        capacity = shelter['total_capacity']

        created = fake.date_time_between(start_date='-3m', end_date='now')
        season = get_season(created)

        # 가중치 구성: 기본 + 재난유형 + 편의시설 + 계절
        weights = dict(base_weights)
        # 재난유형
        pref = disaster_pref.get(shelter.get('disaster_type', ''), {})
        for k, v in pref.items():
            if k in weights:
                weights[k] *= v
        # 편의시설
        if shelter.get('has_pet_zone'):
            weights['반려동물'] = weights.get('반려동물', 0.02) * 2.0
        if shelter.get('has_disabled_facility'):
            weights['의약품'] = weights.get('의약품', 0.12) * 1.3
        # 계절성
        if season == '겨울':
            weights['침구류'] = weights.get('침구류', 0.05) * 1.7
            weights['의류'] = weights.get('의류', 0.08) * 1.3
        elif season == '여름':
            weights['개인위생'] = weights.get('개인위생', 0.07) * 1.5
            weights['생활용품'] = weights.get('생활용품', 0.15) * 1.2

        # 카테고리 및 아이템 선택
        chosen_category = pick_category(weights)
        pool = items_by_category.get(chosen_category) or relief_items
        # 인기 아이템 우선 선택(겹침 증가)
        if pool and wish_item_pop:
            weights = [1 + wish_item_pop.get(it['item_id'], 0) for it in pool]
            total = sum(weights)
            r = random.random() * total
            acc = 0.0
            chosen = pool[-1]
            for it, w in zip(pool, weights):
                acc += w
                if r <= acc:
                    chosen = it
                    break
            item = chosen
        else:
            item = random.choice(pool)

        lo, hi = requested_range_for(chosen_category, capacity)
        requested = random.randint(lo, hi)
        current_stock = random.randint(0, max(0, requested // 3))
        urgent_gap = requested - current_stock
        urgent = max(0, urgent_gap - random.randint(0, urgent_gap))

        # 긴급도 계산(잔여 비율 기반)
        remain = max(0, requested - current_stock)
        remain_ratio = remain / max(1, requested)
        urgency_level = '높음' if remain_ratio >= 0.7 else ('중간' if remain_ratio >= 0.4 else '낮음')

        requests.append({
            'request_id': rid,
            'shelter_id': shelter['shelter_id'],
            'relief_item_id': item['item_id'],
            'requested_quantity': requested,
            'current_stock': current_stock,
            'urgent_quantity': urgent,
            'urgency_level': urgency_level,
            'needed_by': (created + timedelta(days=random.randint(1, 30))).isoformat(),
            'status': random.choices(['대기중', '매칭완료', '배송중', '완료', '취소'], weights=[0.5, 0.2, 0.15, 0.1, 0.05])[0],
            'notes': f"{shelter.get('disaster_type','일반')} 상황 대비 요청",
            'matched_wish_ids': '',
            'total_matched_quantity': 0,
            'remaining_quantity': remain,
            'created_at': created.isoformat(),
            'updated_at': created.isoformat(),
        })

    return requests


def generate_donation_matches(fake, count, wishes, requests, users, shelters, relief_items):
    """기부 매칭 데이터 생성 - 실제 wishes와 requests 연계"""
    matches = []
    
    # 매칭 가능한 wishes와 requests 필터링 (같은 relief_item_id)
    available_wishes = [w for w in wishes if w['remaining_quantity'] > 0 and w['status'] in ['대기중', '매칭완료']]
    available_requests = [r for r in requests if r['remaining_quantity'] > 0 and r['status'] in ['대기중', '매칭완료']]
    
    # 아이템별로 그룹화
    wishes_by_item = {}
    requests_by_item = {}
    
    for wish in available_wishes:
        item_id = wish['relief_item_id']
        if item_id not in wishes_by_item:
            wishes_by_item[item_id] = []
        wishes_by_item[item_id].append(wish)
    
    for request in available_requests:
        item_id = request['relief_item_id']
        if item_id not in requests_by_item:
            requests_by_item[item_id] = []
        requests_by_item[item_id].append(request)
    
    # 요청한 카운트까지 최대한 매칭 시도
    match_count = 0
    
    for i in range(1, count + 1):
        # 상한 없이 요청된 횟수까지 시도

        # 공통 아이템이 있는 경우에만 매칭
        common_items = set(wishes_by_item.keys()) & set(requests_by_item.keys())
        if not common_items:
            break
            
        item_id = random.choice(list(common_items))
        wish = random.choice(wishes_by_item[item_id])
        request = random.choice(requests_by_item[item_id])
        
        # 매칭 가능한 수량 계산
        max_quantity = min(wish['remaining_quantity'], request['remaining_quantity'])
        if max_quantity <= 0:
            continue
            
        matched_qty = random.randint(1, max_quantity)
        
        mid = make_id('match', i)
        matched_at = fake.date_time_between(start_date='-2m', end_date='now')
        
        # 배송 상태에 따른 날짜 계산
        delivery_scheduled = matched_at + timedelta(days=random.randint(1, 3))
        delivery_completed = delivery_scheduled + timedelta(hours=random.randint(4, 48))
        verified = delivery_completed + timedelta(hours=random.randint(1, 6))
        
        matches.append({
            'match_id': mid,
            'donation_wish_id': wish['wish_id'],
            'relief_request_id': request['request_id'],
            'matched_quantity': matched_qty,
            'donor_id': wish['user_id'],
            'shelter_id': request['shelter_id'],
            'relief_item_id': item_id,
            'status': random.choice(['매칭완료', '배송중', '배송완료', '검수완료', '취소']),
            'matched_at': matched_at.isoformat(),
            'delivery_scheduled_at': delivery_scheduled.isoformat(),
            'delivery_completed_at': delivery_completed.isoformat(),
            'verified_at': verified.isoformat(),
            'delivery_company': random.choice(['한진택배', 'CJ대한통운', '우체국택배', '롯데택배']),
            'tracking_number': f"TRK{random.randint(100000000,999999999)}",
            'delivery_address': [s for s in shelters if s['shelter_id'] == request['shelter_id']][0]['address'],
            'created_at': matched_at.isoformat(),
            'updated_at': matched_at.isoformat(),
        })
        
        # 매칭된 수량만큼 차감
        wish['remaining_quantity'] -= matched_qty
        request['remaining_quantity'] -= matched_qty
        
        match_count += 1
    
    return matches


def generate_disaster_incidents(fake, count, shelters):
    """재난 사건 데이터 생성 - 실제 대피소 위치를 사건 중심으로 고정
    - 사건 발생 지점 = 무작위로 선택한 실제(또는 가상) 대피소의 정확한 좌표
    - 주소 필드(detail_address/road_detail_address)도 해당 대피소 주소 사용
    - 영향 반경 내 관련 대피소 식별
    """
    incidents = []

    for i in range(1, count + 1):
        iid = make_id('incident', i)

        # 사건 위치: 실제 대피소 하나를 그대로 사용
        anchor = random.choice(shelters)
        incident_lat = float(anchor['latitude'])
        incident_lon = float(anchor['longitude'])

        # 영향 반경 설정 (현실 범위: 0.5km ~ 15km)
        impact_radius = random.uniform(0.5, 15.0)

        # 영향 반경 내의 대피소들 찾기 (anchor 포함 보장)
        related_shelters = []
        for shelter in shelters:
            distance = calculate_distance(incident_lat, incident_lon,
                                          float(shelter['latitude']), float(shelter['longitude']))
            if distance <= impact_radius:
                related_shelters.append(shelter['shelter_id'])
        if anchor['shelter_id'] not in related_shelters:
            related_shelters.append(anchor['shelter_id'])

        # 너무 많으면 15개로 샘플링
        if len(related_shelters) > 15:
            related_shelters = random.sample(related_shelters, 15)

        damage_date = fake.date_between(start_date='-10y', end_date='today')
        estimated_people = len(related_shelters) * random.randint(80, 600)

        # 주소 필드: 실제 대피소 주소를 그대로 사용
        anchor_addr = anchor.get('address', '')

        incidents.append({
            'incident_id': iid,
            'disaster_year': str(damage_date.year),
            'ndms_disaster_type_code': f"NDMS_{random.randint(100,999)}",
            'disaster_serial_number': f"{damage_date.strftime('%Y%m%d')}{random.randint(1000,9999)}",
            'region_code': f"RGN_{random.randint(10000,99999)}",
            'damage_date': damage_date.isoformat(),
            'damage_time': fake.time(),
            'damage_level': str(random.randint(1,5)),
            'dong_code': str(random.randint(10000,99999)),
            'detail_address': anchor_addr,
            'road_address_code': f"ROAD_{random.randint(100000,999999)}",
            'road_detail_address': anchor_addr,
            'latitude': round(incident_lat, 6),
            'longitude': round(incident_lon, 6),
            'affected_area': round(math.pi * impact_radius * impact_radius, 2),  # 원형 면적
            'estimated_affected_people': estimated_people,
            'related_shelter_ids': ','.join(related_shelters),
            'first_registered_at': damage_date.isoformat(),
            'last_modified_at': (damage_date + timedelta(hours=random.randint(1, 48))).isoformat(),
            'created_at': damage_date.isoformat(),
            'updated_at': damage_date.isoformat(),
        })

    return incidents


def generate_consumption_info(fake, count, shelters, incidents, relief_items, matches):
    """소비 정보 데이터 생성 - 실제 매칭 데이터 기반"""
    consumptions = []
    
    # 매칭 완료된 데이터만 소비 정보 생성
    completed_matches = [m for m in matches if m['status'] in ['배송완료', '검수완료']]
    
    for i in range(1, count + 1):
        cid = make_id('consumption', i)
        
        # 매칭된 데이터 기반으로 생성
        if completed_matches:
            match = random.choice(completed_matches)
            shelter_id = match['shelter_id']
            item_id = match['relief_item_id']
            base_quantity = match['matched_quantity']
        else:
            # fallback: 랜덤 생성
            shelter = random.choice(shelters)
            item = random.choice(relief_items)
            shelter_id = shelter['shelter_id']
            item_id = item['item_id']
            base_quantity = random.randint(10, 100)
        
        # 관련 재난 사건 찾기
        related_incident = None
        for incident in incidents:
            if shelter_id in incident['related_shelter_ids'].split(','):
                related_incident = incident['incident_id']
                break
        
        # LSTM 학습을 위해 최근 10년 범위에서 임의의 시작일 선택
        start_date = fake.date_between(start_date='-10y', end_date='-1d')
        duration = random.randint(1, 30)
        end_date = start_date + timedelta(days=duration)
        
        consumed = random.randint(int(base_quantity * 0.8), int(base_quantity * 1.2))
        daily_rate = round(consumed / max(1, duration), 2)
        
        # 대피소 정보 가져오기
        shelter_info = next((s for s in shelters if s['shelter_id'] == shelter_id), shelters[0])
        capacity = int(shelter_info.get('total_capacity', 0) or 0)
        upper = max(0, capacity)
        lower = 0 if capacity < 10 else 10
        if lower > upper:
            lower = upper
        occupancy = random.randint(lower, upper)
        occupancy_rate = round(occupancy / max(1, capacity), 2)
        
        # start_date 기반 계절 계산
        def _season_from_date(d):
            m = d.month
            if m in (12, 1, 2):
                return '겨울'
            if m in (3, 4, 5):
                return '봄'
            if m in (6, 7, 8):
                return '여름'
            return '가을'

        consumptions.append({
            'consumption_id': cid,
            'shelter_id': shelter_id,
            'disaster_incident_id': related_incident or '',
            'relief_item_id': item_id,
            'consumed_quantity': consumed,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'duration_days': duration,
            'daily_consumption_rate': daily_rate,
            'peak_consumption_day': random.randint(1, duration),
            'peak_consumption_quantity': random.randint(int(daily_rate), int(daily_rate * 2)),
            'remain_item': random.randint(0, int(base_quantity * 0.2)),
            'shelter_occupancy': occupancy,
            'occupancy_rate': occupancy_rate,
            'disaster_severity': random.choice(['낮음', '중간', '높음']),
            'weather_conditions': random.choice(['더위', '추위', '비', '눈', '일반']),
            'special_circumstances': ','.join(random.sample(['어린이 다수', '고령자 포함', '장애인 포함', '반려동물 포함'], k=random.randint(1, 3))),
            'waste_rate': round(random.uniform(0, 0.15), 3),
            'satisfaction_score': round(random.uniform(2.0, 5.0), 1),
            'adequacy_level': random.choice(['부족', '적정', '충분', '과다']),
            'restock_frequency': random.randint(0, 5),
            'seasonality': _season_from_date(start_date),
            'children_ratio': round(random.uniform(0, 0.4), 2),
            'elderly_ratio': round(random.uniform(0, 0.3), 2),
            'disabled_ratio': round(random.uniform(0, 0.15), 2),
            'accessibility_score': round(random.uniform(2.0, 5.0), 1),
            'distribution_efficiency': round(random.uniform(0.6, 1.0), 2),
            'recorded_by': shelter_info['manager_id'],
            'created_at': end_date.isoformat(),
            'updated_at': end_date.isoformat(),
        })
    
    return consumptions


def save_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def calculate_recommended_counts(shelter_count=22000, user_count=10000):
    """ML/DL 학습에 적합한 데이터 규모 계산"""
    
    # 기본 비율 설정 (실제 플랫폼 운영 시나리오 기반)
    recommendations = {
        'users': user_count,
        'shelters': '실제 데이터 사용' if shelter_count > 1000 else shelter_count,
        'relief_items': min(200, max(100, user_count // 50)),  # 100-200개 구호품
        'wishes': int(user_count * 0.3),  # 30% 사용자가 기부 의사 표현
        'requests': int(shelter_count * 0.15),  # 15% 대피소가 요청
        'matches': int(min(user_count * 0.2, shelter_count * 0.1)),  # 매칭 성공률 고려
        'incidents': max(50, min(500, shelter_count // 100)),  # 대피소 100개당 1개 재난
        'consumptions': int(shelter_count * 0.05),  # 5% 대피소의 소비 이력
    }
    
    return recommendations


def main():
    parser = argparse.ArgumentParser(description='이어드림 플랫폼 가상 데이터 생성기 (ML/DL 학습용)')
    
    # 기본 추천값 계산
    recommended = calculate_recommended_counts()
    
    parser.add_argument('--seed', type=int, default=None, help='랜덤 시드')
    parser.add_argument('--users', type=int, default=recommended['users'], 
                       help=f'사용자 수 (추천: {recommended["users"]})')
    parser.add_argument('--shelters', type=int, default=100, 
                       help='가상 대피소 수 (실제 데이터 없을 때만 사용)')
    parser.add_argument('--relief_items', type=int, default=recommended['relief_items'], 
                       help=f'구호품 종류 수 (추천: {recommended["relief_items"]})')
    parser.add_argument('--wishes', type=int, default=recommended['wishes'], 
                       help=f'기부 의사 수 (추천: {recommended["wishes"]})')
    parser.add_argument('--requests', type=int, default=recommended['requests'], 
                       help=f'구호품 요청 수 (추천: {recommended["requests"]})')
    parser.add_argument('--matches', type=int, default=recommended['matches'], 
                       help=f'매칭 수 (추천: {recommended["matches"]})')
    parser.add_argument('--incidents', type=int, default=recommended['incidents'], 
                       help=f'재난 사건 수 (추천: {recommended["incidents"]})')
    parser.add_argument('--consumptions', type=int, default=recommended['consumptions'], 
                       help=f'소비 정보 수 (추천: {recommended["consumptions"]})')
    parser.add_argument('--out', type=str, default='output', help='출력 폴더')
    parser.add_argument('--real_shelter_csv', type=str, default=None, 
                       help='실제 대피소 CSV 파일 경로')
    parser.add_argument('--no_auto_adjust', action='store_true',
                       help='실제 대피소 수 기준 자동 규모 조정을 비활성화합니다')
    
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    fake = Faker('ko_KR')
    if args.seed is not None:
        fake.seed_instance(args.seed)

    print("🚀 이어드림 플랫폼 데이터 생성 시작")
    print("=" * 50)
    
    # 1단계: 사용자 데이터 생성
    print(f"👥 사용자 데이터 생성 중... ({args.users}명)")
    users = generate_users(fake, args.users)
    general_users = [u for u in users if u['user_type'] == 'general_user']
    public_officers = [u for u in users if u['user_type'] == 'public_officer']
    print(f"   └─ 일반 사용자: {len(general_users)}명, 관리자: {len(public_officers)}명")
    
    # 2단계: 구호품 데이터 생성
    print(f"📦 구호품 데이터 생성 중... ({args.relief_items}개)")
    relief_items = generate_relief_items(fake, args.relief_items)
    
    # 3단계: 대피소 데이터 로드/생성
    print(f"🏠 대피소 데이터 처리 중...")
    shelters = generate_shelters(fake, args.shelters, users, args.real_shelter_csv)
    
    # 실제 대피소 수에 따라 요청/매칭 수 재조정
    actual_shelter_count = len(shelters)
    if actual_shelter_count > 1000 and not args.no_auto_adjust:  # 실제 데이터 사용 시 (옵션으로 비활성화 가능)
        adjusted_requests = min(args.requests, int(actual_shelter_count * 0.15))
        adjusted_matches = min(args.matches, int(actual_shelter_count * 0.1))
        adjusted_incidents = min(args.incidents, max(50, actual_shelter_count // 100))
        adjusted_consumptions = min(args.consumptions, int(actual_shelter_count * 0.05))
        
        print(f"📊 실제 대피소 수({actual_shelter_count})에 맞춰 데이터 규모 조정:")
        print(f"   └─ 요청: {adjusted_requests}, 매칭: {adjusted_matches}")
        print(f"   └─ 재난: {adjusted_incidents}, 소비이력: {adjusted_consumptions}")
    else:
        adjusted_requests = args.requests
        adjusted_matches = args.matches
        adjusted_incidents = args.incidents
        adjusted_consumptions = args.consumptions
    
    # 4단계: 기부 의사 데이터 생성 (general_user만)
    print(f"💝 기부 의사 데이터 생성 중... ({args.wishes}개)")
    wishes = generate_user_donation_wishes(fake, args.wishes, users, relief_items)
    
    # 5단계: 대피소 요청 데이터 생성
    print(f"📋 대피소 요청 데이터 생성 중... ({adjusted_requests}개)")
    requests = generate_shelter_relief_requests(fake, adjusted_requests, shelters, relief_items, wishes)
    
    # 6단계: 매칭 데이터 생성
    print(f"🤝 매칭 데이터 생성 중... ({adjusted_matches}개)")
    matches = generate_donation_matches(fake, adjusted_matches, wishes, requests, users, shelters, relief_items)
    
    # 7단계: 재난 사건 데이터 생성
    print(f"⚠️ 재난 사건 데이터 생성 중... ({adjusted_incidents}개)")
    incidents = generate_disaster_incidents(fake, adjusted_incidents, shelters)
    
    # 8단계: 소비 정보 데이터 생성
    print(f"📈 소비 정보 데이터 생성 중... ({adjusted_consumptions}개)")
    consumptions = generate_consumption_info(fake, adjusted_consumptions, shelters, incidents, relief_items, matches)

    # 데이터 저장
    print(f"\n💾 데이터 저장 중... ({args.out}/)")
    out = args.out
    save_json(users, os.path.join(out, 'users.json'))
    save_json(shelters, os.path.join(out, 'shelters.json'))
    save_json(relief_items, os.path.join(out, 'relief_items.json'))
    save_json(wishes, os.path.join(out, 'user_donation_wishes.json'))
    save_json(requests, os.path.join(out, 'shelter_relief_requests.json'))
    save_json(matches, os.path.join(out, 'donation_matches.json'))
    save_json(incidents, os.path.join(out, 'disaster_incidents.json'))
    save_json(consumptions, os.path.join(out, 'consumption_info.json'))

    print("\n✅ 데이터 생성 완료!")
    print("=" * 50)
    print(f"📁 출력 위치: {args.out}/")
    print(f"📊 총 데이터 현황:")
    print(f"   ├─ 사용자: {len(users):,}명")
    print(f"   ├─ 대피소: {len(shelters):,}개")
    print(f"   ├─ 구호품: {len(relief_items):,}개")
    print(f"   ├─ 기부의사: {len(wishes):,}개")
    print(f"   ├─ 요청: {len(requests):,}개")
    print(f"   ├─ 매칭: {len(matches):,}개")
    print(f"   ├─ 재난사건: {len(incidents):,}개")
    print(f"   └─ 소비이력: {len(consumptions):,}개")
    
    # ML/DL 학습용 데이터 품질 체크
    print(f"\n🎯 ML/DL 학습 데이터 품질:")
    print(f"   ├─ 매칭 성공률: {len(matches)/max(1,len(wishes))*100:.1f}%")
    print(f"   ├─ 대피소당 평균 요청: {len(requests)/max(1,len(shelters)):.1f}개")
    print(f"   └─ 사용자당 평균 기부: {len(wishes)/max(1,len(general_users)):.1f}개")


if __name__ == '__main__':
    main()