#!/usr/bin/env python3
"""CSV용 가상 데이터 생성기 - 개선된 버전

`tools/generate_fake_data.py`의 생성 함수를 재사용하여 각 테이블을 CSV로 저장합니다.
CSV는 UTF-8-sig(Excel에서 바로 열기 용이)로 저장됩니다.
JSON 생성 스크립트와 옵션/로직을 정렬했습니다.
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
    parser = argparse.ArgumentParser(description='이어드림 플랫폼 가상 데이터 생성기 CSV 버전 (ML/DL 학습용)')
    
    # 기본 추천값 계산
    recommended = gen.calculate_recommended_counts()
    
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
    parser.add_argument('--out', type=str, default='output_csv', help='출력 폴더')
    parser.add_argument('--real_shelter_csv', type=str, default=None, 
                       help='실제 대피소 CSV 파일 경로')
    parser.add_argument('--no_auto_adjust', action='store_true',
                       help='실제 대피소 수 기준 자동 규모 조정을 비활성화합니다')
    
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    fake = gen.Faker('ko_KR')
    if args.seed is not None:
        fake.seed_instance(args.seed)

    print("🚀 이어드림 플랫폼 CSV 데이터 생성 시작")
    print("=" * 50)
    
    # 단계별 데이터 생성 (JSON 버전과 동일한 로직)
    print(f"👥 사용자 데이터 생성 중... ({args.users}명)")
    users = gen.generate_users(fake, args.users)
    
    print(f"📦 구호품 데이터 생성 중... ({args.relief_items}개)")
    relief_items = gen.generate_relief_items(fake, args.relief_items)
    
    print(f"🏠 대피소 데이터 처리 중...")
    shelters = gen.generate_shelters(fake, args.shelters, users, args.real_shelter_csv)
    
    # 실제 대피소 수에 따라 조정
    actual_shelter_count = len(shelters)
    if actual_shelter_count > 1000 and not args.no_auto_adjust:
        adjusted_requests = min(args.requests, int(actual_shelter_count * 0.15))
        adjusted_matches = min(args.matches, int(actual_shelter_count * 0.1))
        adjusted_incidents = min(args.incidents, max(50, actual_shelter_count // 100))
        adjusted_consumptions = min(args.consumptions, int(actual_shelter_count * 0.05))
        print(f"📊 실제 대피소 수({actual_shelter_count})에 맞춰 데이터 규모 조정")
    else:
        adjusted_requests = args.requests
        adjusted_matches = args.matches
        adjusted_incidents = args.incidents
        adjusted_consumptions = args.consumptions
    
    print(f"💝 기부 의사 데이터 생성 중... ({args.wishes}개)")
    wishes = gen.generate_user_donation_wishes(fake, args.wishes, users, relief_items)
    
    print(f"📋 대피소 요청 데이터 생성 중... ({adjusted_requests}개)")
    requests = gen.generate_shelter_relief_requests(fake, adjusted_requests, shelters, relief_items, wishes)
    
    print(f"🤝 매칭 데이터 생성 중... ({adjusted_matches}개)")
    matches = gen.generate_donation_matches(fake, adjusted_matches, wishes, requests, users, shelters, relief_items)
    
    print(f"⚠️ 재난 사건 데이터 생성 중... ({adjusted_incidents}개)")
    incidents = gen.generate_disaster_incidents(fake, adjusted_incidents, shelters)
    
    print(f"📈 소비 정보 데이터 생성 중... ({adjusted_consumptions}개)")
    consumptions = gen.generate_consumption_info(fake, adjusted_consumptions, shelters, incidents, relief_items, matches)

    # CSV 저장
    print(f"\n💾 CSV 데이터 저장 중... ({args.out}/)")
    out = args.out
    save_csv(users, os.path.join(out, 'users.csv'))
    save_csv(shelters, os.path.join(out, 'shelters.csv'))
    save_csv(relief_items, os.path.join(out, 'relief_items.csv'))
    save_csv(wishes, os.path.join(out, 'user_donation_wishes.csv'))
    save_csv(requests, os.path.join(out, 'shelter_relief_requests.csv'))
    save_csv(matches, os.path.join(out, 'donation_matches.csv'))
    save_csv(incidents, os.path.join(out, 'disaster_incidents.csv'))
    save_csv(consumptions, os.path.join(out, 'consumption_info.csv'))

    print("\n✅ CSV 데이터 생성 완료!")
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


if __name__ == '__main__':
    main()
