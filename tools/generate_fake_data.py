#!/usr/bin/env python3
"""가상 데이터 생성기

Faker(ko_KR)을 사용해 첨부된 데이터 스키마에 맞춘 가상 데이터를 생성하여
JSON 파일로 출력합니다.

사용법:
  python tools\\generate_fake_data.py --users 50 --shelters 20 --relief_items 30

출력: 프로젝트 루트의 output/ 폴더에 각 테이블별 json 파일 생성
"""
import argparse
import json
import os
import random
from datetime import datetime, timedelta
from faker import Faker


KO_LAT_MIN, KO_LAT_MAX = 33.0, 38.6
KO_LON_MIN, KO_LON_MAX = 124.6, 131.9


def now_iso():
    return datetime.utcnow().isoformat() + "Z"


def rand_coords():
    return round(random.uniform(KO_LAT_MIN, KO_LAT_MAX), 6), round(random.uniform(KO_LON_MIN, KO_LON_MAX), 6)


def make_id(prefix, i):
    return f"{prefix}_{i:04d}"


def generate_users(fake, count):
    users = []
    for i in range(1, count + 1):
        uid = make_id('user', i)
        name = fake.name()
        email = fake.safe_email()
        phone = fake.phone_number()
        zipcode = fake.postcode()
        addr = fake.street_address()
        road_addr = fake.address().split('\n')[0]
        created = fake.date_time_between(start_date='-2y', end_date='now')
        users.append({
            'user_id': uid,
            'email': email,
            'user_type': random.choice(['public_officer', 'general_user']),
            'name': name,
            'phone_number': phone,
            'zipcode': zipcode,
            'road_address': road_addr,
            'address_detail': addr,
            'preferred_categories': '',
            'created_at': created.isoformat(),
            'updated_at': created.isoformat(),
            'last_login_at': (created + timedelta(days=random.randint(0, 365))).isoformat(),
        })
    return users


def generate_relief_items(fake, count):
    base_categories = [
        ('식량', ['즉석식품', '통조림', '가공식품']),
        ('생활용품', ['화장지', '위생용품', '세제']),
        ('의류', ['아우터', '내의', '양말']),
        ('의약품', ['기본구급', '상처치료']),
    ]
    items = []
    i = 1
    for c, subs in base_categories:
        for sub in subs:
            if i > count:
                break
            item_id = make_id('relief_item', i)
            name = f"{c} > {sub} > 예시품목 {i}"
            items.append({
                'item_id': item_id,
                'item_code': f"{c[:3].upper()}_{i:03d}",
                'category': c,
                'subcategory': sub,
                'item_name': name,
                'description': f"{c} > {sub} > 설명",
                'unit': random.choice(['개', '박스', '세트']),
                'created_at': now_iso(),
                'updated_at': now_iso(),
            })
            i += 1
            if i > count:
                break
    # if still less than count, add synthetic items
    while len(items) < count:
        i = len(items) + 1
        item_id = make_id('relief_item', i)
        items.append({
            'item_id': item_id,
            'item_code': f"MISC_{i:03d}",
            'category': '기타',
            'subcategory': '기타',
            'item_name': f"기타품목 {i}",
            'description': '기타',
            'unit': '개',
            'created_at': now_iso(),
            'updated_at': now_iso(),
        })
    return items


def generate_shelters(fake, count, users):
    shelters = []
    for i in range(1, count + 1):
        sid = make_id('shelter', i)
        manager = random.choice(users)['user_id'] if users else make_id('user', 1)
        lat, lon = rand_coords()
        total_capacity = random.randint(50, 1000)
        current = random.randint(0, total_capacity)
        created = fake.date_time_between(start_date='-2y', end_date='now')
        shelters.append({
            'shelter_id': sid,
            'manager_id': manager,
            'shelter_name': fake.company() + ' 대피소',
            'disaster_type': random.choice(['지진', '홍수', '태풍', '화재']),
            'status': random.choice(['운영중', '포화', '폐쇄']),
            'address': fake.address().split('\n')[0],
            'latitude': lat,
            'longitude': lon,
            'total_capacity': total_capacity,
            'current_occupancy': current,
            'occupancy_rate': round(current / total_capacity, 2) if total_capacity else 0,
            'has_disabled_facility': random.choice([True, False]),
            'has_pet_zone': random.choice([True, False]),
            'amenities': ','.join(random.sample(['의료실', '급식실', '샤워실', '휴게실'], k=2)),
            'contact_person': fake.name(),
            'contact_phone': fake.phone_number(),
            'contact_email': fake.safe_email(),
            'total_requests': random.randint(0, 200),
            'fulfilled_requests': 0,
            'pending_requests': 0,
            'created_at': created.isoformat(),
            'updated_at': created.isoformat(),
        })
    return shelters


def generate_user_donation_wishes(fake, count, users, relief_items):
    wishes = []
    for i in range(1, count + 1):
        wid = make_id('wish', i)
        user = random.choice(users)['user_id']
        item = random.choice(relief_items)['item_id']
        qty = random.randint(1, 500)
        created = fake.date_time_between(start_date='-1y', end_date='now')
        remaining = max(0, qty - random.randint(0, qty))
        wishes.append({
            'wish_id': wid,
            'user_id': user,
            'relief_item_id': item,
            'quantity': qty,
            'status': random.choice(['대기중', '매칭완료', '배송중', '완료', '취소']),
            'matched_request_ids': '',
            'total_matched_quantity': qty - remaining,
            'remaining_quantity': remaining,
            'created_at': created.isoformat(),
            'updated_at': created.isoformat(),
            'expires_at': (created + timedelta(days=random.randint(1, 30))).isoformat(),
        })
    return wishes


def generate_shelter_relief_requests(fake, count, shelters, relief_items):
    requests = []
    for i in range(1, count + 1):
        rid = make_id('request', i)
        shelter = random.choice(shelters)['shelter_id']
        item = random.choice(relief_items)['item_id']
        requested = random.randint(10, 1000)
        current_stock = random.randint(0, requested)
        urgent = max(0, requested - current_stock - random.randint(0, 100))
        created = fake.date_time_between(start_date='-1y', end_date='now')
        requests.append({
            'request_id': rid,
            'shelter_id': shelter,
            'relief_item_id': item,
            'requested_quantity': requested,
            'current_stock': current_stock,
            'urgent_quantity': urgent,
            'urgency_level': random.choice(['높음', '중간', '낮음']),
            'needed_by': (created + timedelta(days=random.randint(0, 14))).isoformat(),
            'status': random.choice(['대기중', '매칭완료', '배송중', '완료', '취소']),
            'notes': fake.sentence(nb_words=6),
            'matched_wish_ids': '',
            'total_matched_quantity': 0,
            'remaining_quantity': requested - current_stock,
            'created_at': created.isoformat(),
            'updated_at': created.isoformat(),
        })
    return requests


def generate_donation_matches(fake, count, wishes, requests, users, shelters, relief_items):
    matches = []
    for i in range(1, count + 1):
        mid = make_id('match', i)
        wish = random.choice(wishes)
        req = random.choice(requests)
        matched_qty = min(wish['remaining_quantity'], req['remaining_quantity']) if (wish['remaining_quantity'] and req['remaining_quantity']) else random.randint(1, min(50, wish['quantity']))
        donor = wish['user_id']
        shelter = req['shelter_id']
        item = wish['relief_item_id']
        matched_at = fake.date_time_between(start_date='-1y', end_date='now')
        matches.append({
            'match_id': mid,
            'donation_wish_id': wish['wish_id'],
            'relief_request_id': req['request_id'],
            'matched_quantity': matched_qty,
            'donor_id': donor,
            'shelter_id': shelter,
            'relief_item_id': item,
            'status': random.choice(['매칭완료', '배송중', '배송완료', '검수완료', '취소']),
            'matched_at': matched_at.isoformat(),
            'delivery_scheduled_at': (matched_at + timedelta(days=1)).isoformat(),
            'delivery_completed_at': (matched_at + timedelta(days=1, hours=3)).isoformat(),
            'verified_at': (matched_at + timedelta(days=1, hours=4)).isoformat(),
            'delivery_company': random.choice(['한진택배', 'CJ대한통운', '우체국택배']),
            'tracking_number': f"TRK{random.randint(100000,999999)}",
            'delivery_address': fake.address().split('\n')[0],
            'created_at': now_iso(),
            'updated_at': now_iso(),
        })
    return matches


def generate_disaster_incidents(fake, count, shelters):
    incidents = []
    for i in range(1, count + 1):
        iid = make_id('incident', i)
        lat, lon = rand_coords()
        related = ','.join([s['shelter_id'] for s in random.sample(shelters, k=min(len(shelters), random.randint(0, 3)))])
        damage_date = fake.date_between(start_date='-2y', end_date='today')
        incidents.append({
            'incident_id': iid,
            'disaster_year': str(damage_date.year),
            'ndms_disaster_type_code': f"NDMS_{random.randint(100,999)}",
            'disaster_serial_number': f"{random.randint(1000000,9999999)}",
            'region_code': f"RGN_{random.randint(1000,9999)}",
            'damage_date': damage_date.isoformat(),
            'damage_time': fake.time(),
            'damage_level': str(random.randint(1,5)),
            'dong_code': str(random.randint(10000,99999)),
            'detail_address': fake.address().split('\n')[0],
            'road_address_code': f"ROAD_{random.randint(100000,999999)}",
            'road_detail_address': fake.address().split('\n')[0],
            'latitude': lat,
            'longitude': lon,
            'affected_area': round(random.uniform(0.1, 200.0), 2),
            'estimated_affected_people': random.randint(1, 5000),
            'related_shelter_ids': related,
            'first_registered_at': now_iso(),
            'last_modified_at': now_iso(),
            'created_at': now_iso(),
            'updated_at': now_iso(),
        })
    return incidents


def generate_consumption_info(fake, count, shelters, incidents, relief_items):
    consumptions = []
    for i in range(1, count + 1):
        cid = make_id('consumption', i)
        shelter = random.choice(shelters)['shelter_id']
        incident = random.choice(incidents)['incident_id'] if incidents else ''
        item = random.choice(relief_items)['item_id']
        start = fake.date_between(start_date='-1y', end_date='today')
        duration = random.randint(1, 30)
        consumed = random.randint(1, 2000)
        daily = round(consumed / max(1, duration), 2)
        consumptions.append({
            'consumption_id': cid,
            'shelter_id': shelter,
            'disaster_incident_id': incident,
            'relief_item_id': item,
            'consumed_quantity': consumed,
            'start_date': start.isoformat(),
            'end_date': (start + timedelta(days=duration)).isoformat(),
            'duration_days': duration,
            'daily_consumption_rate': daily,
            'peak_consumption_day': random.randint(1, duration),
            'peak_consumption_quantity': random.randint(1, consumed),
            'remain_item': random.randint(0, 100),
            'shelter_occupancy': random.randint(10, 1000),
            'occupancy_rate': round(random.uniform(0, 1), 2),
            'disaster_severity': random.choice(['낮음', '중간', '높음']),
            'weather_conditions': random.choice(['더위', '추위', '비', '눈', '일반']),
            'special_circumstances': ','.join(random.sample(['어린이 다수', '고령자 포함', '장애인 포함', '반려동물 포함'], k=2)),
            'waste_rate': round(random.uniform(0, 0.2), 2),
            'satisfaction_score': round(random.uniform(1, 5), 1),
            'adequacy_level': random.choice(['부족', '적정', '충분', '과다']),
            'restock_frequency': random.randint(0, 10),
            'seasonality': random.choice(['봄', '여름', '가을', '겨울']),
            'children_ratio': round(random.uniform(0, 1), 2),
            'elderly_ratio': round(random.uniform(0, 1), 2),
            'disabled_ratio': round(random.uniform(0, 1), 2),
            'accessibility_score': round(random.uniform(1, 5), 1),
            'distribution_efficiency': round(random.uniform(0, 1), 2),
            'recorded_by': random.choice(shelters)['shelter_id'],
            'created_at': now_iso(),
            'updated_at': now_iso(),
        })
    return consumptions


def save_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--users', type=int, default=50)
    parser.add_argument('--shelters', type=int, default=20)
    parser.add_argument('--relief_items', type=int, default=30)
    parser.add_argument('--wishes', type=int, default=100)
    parser.add_argument('--requests', type=int, default=80)
    parser.add_argument('--matches', type=int, default=60)
    parser.add_argument('--incidents', type=int, default=10)
    parser.add_argument('--consumptions', type=int, default=40)
    parser.add_argument('--out', type=str, default='output')
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    fake = Faker('ko_KR')
    if args.seed is not None:
        fake.seed_instance(args.seed)

    users = generate_users(fake, args.users)
    relief_items = generate_relief_items(fake, args.relief_items)
    shelters = generate_shelters(fake, args.shelters, users)
    wishes = generate_user_donation_wishes(fake, args.wishes, users, relief_items)
    requests = generate_shelter_relief_requests(fake, args.requests, shelters, relief_items)
    matches = generate_donation_matches(fake, args.matches, wishes, requests, users, shelters, relief_items)
    incidents = generate_disaster_incidents(fake, args.incidents, shelters)
    consumptions = generate_consumption_info(fake, args.consumptions, shelters, incidents, relief_items)

    out = args.out
    save_json(users, os.path.join(out, 'users.json'))
    save_json(shelters, os.path.join(out, 'shelters.json'))
    save_json(relief_items, os.path.join(out, 'relief_items.json'))
    save_json(wishes, os.path.join(out, 'user_donation_wishes.json'))
    save_json(requests, os.path.join(out, 'shelter_relief_requests.json'))
    save_json(matches, os.path.join(out, 'donation_matches.json'))
    save_json(incidents, os.path.join(out, 'disaster_incidents.json'))
    save_json(consumptions, os.path.join(out, 'consumption_info.json'))

    print(f"생성 완료: {out} 폴더에 JSON 파일들을 생성했습니다.")


if __name__ == '__main__':
    main()
