#!/usr/bin/env python3
"""CSV용 가상 데이터 생성기

`tools/generate_fake_data.py`의 생성 함수를 재사용하여 각 테이블을 CSV로 저장합니다.
CSV는 UTF-8-sig(Excel에서 바로 열기 용이)로 저장됩니다.
"""
import os
import argparse
import random
import pandas as pd

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import generate_fake_data as gen


def save_csv(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(obj)
    # UTF-8 with BOM
    df.to_csv(path, index=False, encoding='utf-8-sig')


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
    parser.add_argument('--out', type=str, default='output_csv')
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    fake = gen.Faker('ko_KR')
    if args.seed is not None:
        fake.seed_instance(args.seed)

    users = gen.generate_users(fake, args.users)
    relief_items = gen.generate_relief_items(fake, args.relief_items)
    shelters = gen.generate_shelters(fake, args.shelters, users)
    wishes = gen.generate_user_donation_wishes(fake, args.wishes, users, relief_items)
    requests = gen.generate_shelter_relief_requests(fake, args.requests, shelters, relief_items)
    matches = gen.generate_donation_matches(fake, args.matches, wishes, requests, users, shelters, relief_items)
    incidents = gen.generate_disaster_incidents(fake, args.incidents, shelters)
    consumptions = gen.generate_consumption_info(fake, args.consumptions, shelters, incidents, relief_items)

    out = args.out
    save_csv(users, os.path.join(out, 'users.csv'))
    save_csv(shelters, os.path.join(out, 'shelters.csv'))
    save_csv(relief_items, os.path.join(out, 'relief_items.csv'))
    save_csv(wishes, os.path.join(out, 'user_donation_wishes.csv'))
    save_csv(requests, os.path.join(out, 'shelter_relief_requests.csv'))
    save_csv(matches, os.path.join(out, 'donation_matches.csv'))
    save_csv(incidents, os.path.join(out, 'disaster_incidents.csv'))
    save_csv(consumptions, os.path.join(out, 'consumption_info.csv'))

    print(f"CSV 생성 완료: {out} 폴더에 CSV 파일들을 생성했습니다.")


if __name__ == '__main__':
    main()
