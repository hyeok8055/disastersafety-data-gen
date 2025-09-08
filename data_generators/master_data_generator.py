# 마스터 데이터 생성 모듈
# 사용자, 대피소, 구호품 기본 데이터 생성

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import sys
import os

# 설정 파일 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.data_config import *

class MasterDataGenerator:
    def __init__(self, seed=42):
        self.fake = Faker('ko_KR')
        self.config = DataConfig()
        Faker.seed(seed)
        random.seed(seed)
        np.random.seed(seed)
    
    def generate_users(self):
        """사용자 테이블 데이터 생성"""
        users = []
        
        for i in range(self.config.USER_COUNT):
            user = {
                'user_id': f'user_{i+1:06d}',
                'username': self.fake.user_name(),
                'email': self.fake.email(),
                'password_hash': self.fake.sha256(),
                'full_name': self.fake.name(),
                'phone': self.fake.phone_number(),
                'address': self.fake.address().replace('\n', ' '),
                'role': random.choice(self.config.USER_ROLES),
                'is_verified': random.choice([True, False]),
                'created_at': self.fake.date_time_between(start_date='-2y', end_date='now'),
                'updated_at': datetime.now(),
                'last_login': self.fake.date_time_between(start_date='-30d', end_date='now') if random.random() > 0.1 else None
            }
            users.append(user)
        
        return pd.DataFrame(users)
    
    def generate_shelters(self):
        """대피소 테이블 데이터 생성"""
        shelters = []
        
        for i in range(self.config.SHELTER_COUNT):
            shelter = {
                'shelter_id': f'shelter_{i+1:04d}',
                'name': f'{self.fake.city()}{random.choice(["초등학교", "중학교", "고등학교", "체육관", "커뮤니티센터"])}',
                'address': self.fake.address().replace('\n', ' '),
                'latitude': round(random.uniform(33.0, 38.5), 6),
                'longitude': round(random.uniform(125.0, 131.0), 6),
                'capacity': random.randint(50, 500),
                'current_occupancy': 0,  # 초기값
                'disaster_type': random.choice(self.config.DISASTER_TYPES),
                'status': random.choice(['active', 'inactive', 'maintenance']),
                'contact_phone': self.fake.phone_number(),
                'manager_name': self.fake.name(),
                'region': random.choice(self.config.REGIONS),
                'facilities': ','.join(random.sample(['wifi', 'generator', 'medical_room', 'kitchen', 'shower', 'parking'], k=random.randint(2, 4))),
                'created_at': self.fake.date_time_between(start_date='-1y', end_date='now'),
                'updated_at': datetime.now()
            }
            shelters.append(shelter)
        
        return pd.DataFrame(shelters)
    
    def generate_relief_items(self):
        """구호품 테이블 데이터 생성"""
        relief_items = []
        item_id = 1
        
        for category, items in self.config.RELIEF_CATEGORIES.items():
            for item_name in items:
                relief_item = {
                    'item_id': f'item_{item_id:05d}',
                    'name': item_name,
                    'category': category,
                    'unit': random.choice(['개', 'kg', 'L', '박스', '팩']),
                    'description': f'{item_name} - {category} 카테고리 구호품',
                    'standard_price': round(random.uniform(1000, 50000), -2),  # 100원 단위
                    'weight_per_unit': round(random.uniform(0.1, 5.0), 2),
                    'volume_per_unit': round(random.uniform(0.01, 1.0), 3),
                    'shelf_life_days': random.randint(30, 1095) if category == 'food' else None,
                    'is_perishable': category == 'food',
                    'storage_requirements': random.choice(['room_temp', 'refrigerated', 'frozen']) if category == 'food' else 'room_temp',
                    'created_at': self.fake.date_time_between(start_date='-6m', end_date='now'),
                    'updated_at': datetime.now()
                }
                relief_items.append(relief_item)
                item_id += 1
        
        # 추가 구호품 생성 (목표 수량까지)
        while len(relief_items) < self.config.RELIEF_ITEM_COUNT:
            category = random.choice(list(self.config.RELIEF_CATEGORIES.keys()))
            relief_item = {
                'item_id': f'item_{item_id:05d}',
                'name': f'{self.fake.word()}_{category}',
                'category': category,
                'unit': random.choice(['개', 'kg', 'L', '박스', '팩']),
                'description': f'추가 {category} 카테고리 구호품',
                'standard_price': round(random.uniform(1000, 50000), -2),
                'weight_per_unit': round(random.uniform(0.1, 5.0), 2),
                'volume_per_unit': round(random.uniform(0.01, 1.0), 3),
                'shelf_life_days': random.randint(30, 1095) if category == 'food' else None,
                'is_perishable': category == 'food',
                'storage_requirements': random.choice(['room_temp', 'refrigerated', 'frozen']) if category == 'food' else 'room_temp',
                'created_at': self.fake.date_time_between(start_date='-6m', end_date='now'),
                'updated_at': datetime.now()
            }
            relief_items.append(relief_item)
            item_id += 1
        
        return pd.DataFrame(relief_items)
    
    def generate_shelter_inventories(self, shelters_df, relief_items_df):
        """대피소 재고 테이블 데이터 생성"""
        inventories = []
        
        for _, shelter in shelters_df.iterrows():
            # 각 대피소마다 랜덤하게 구호품 재고 생성
            num_items = random.randint(10, 30)
            selected_items = relief_items_df.sample(n=num_items)
            
            for _, item in selected_items.iterrows():
                inventory = {
                    'inventory_id': f'inv_{len(inventories)+1:06d}',
                    'shelter_id': shelter['shelter_id'],
                    'item_id': item['item_id'],
                    'current_quantity': random.randint(0, 1000),
                    'minimum_threshold': random.randint(10, 100),
                    'maximum_capacity': random.randint(500, 2000),
                    'last_updated': self.fake.date_time_between(start_date='-30d', end_date='now'),
                    'expiry_date': (datetime.now() + timedelta(days=random.randint(30, 365))) if item['is_perishable'] else None
                }
                inventories.append(inventory)
        
        return pd.DataFrame(inventories)
    
    def generate_all_master_data(self):
        """모든 마스터 데이터 생성 및 반환"""
        print("사용자 데이터 생성 중...")
        users_df = self.generate_users()
        
        print("대피소 데이터 생성 중...")
        shelters_df = self.generate_shelters()
        
        print("구호품 데이터 생성 중...")
        relief_items_df = self.generate_relief_items()
        
        print("대피소 재고 데이터 생성 중...")
        inventories_df = self.generate_shelter_inventories(shelters_df, relief_items_df)
        
        return {
            'users': users_df,
            'shelters': shelters_df,
            'relief_items': relief_items_df,
            'shelter_inventories': inventories_df
        }

if __name__ == "__main__":
    generator = MasterDataGenerator()
    data = generator.generate_all_master_data()
    
    # 데이터 요약 출력
    for table_name, df in data.items():
        print(f"\n{table_name}: {len(df)} 레코드 생성")
        print(f"컬럼: {list(df.columns)}")
        print(f"샘플 데이터:\n{df.head(2)}")