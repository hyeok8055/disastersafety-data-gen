import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
import random
from config.data_config import DataConfig

class DonationDataGenerator:
    def __init__(self):
        self.fake = Faker('ko_KR')
        self.config = DataConfig()
        
    def generate_donations(self, users_df, relief_items_df):
        """기부 테이블 데이터 생성"""
        donations = []
        
        for _ in range(self.config.DONATION_COUNT):
            donation_id = f"DON{str(len(donations) + 1).zfill(6)}"
            user_id = random.choice(users_df['user_id'].tolist())
            relief_item_id = random.choice(relief_items_df['item_id'].tolist())
            
            # 기부 수량 (1-100개)
            quantity = random.randint(1, 100)
            
            # 기부 날짜 (최근 6개월)
            donation_date = self.fake.date_between(start_date='-6M', end_date='today')
            
            # 기부 상태
            status = random.choice(['pending', 'confirmed', 'delivered', 'cancelled'])
            
            # 기부 메시지
            messages = [
                "재난 피해자들에게 도움이 되길 바랍니다.",
                "조금이나마 도움이 되었으면 좋겠습니다.",
                "빠른 복구를 위해 기부합니다.",
                "피해자분들께 힘이 되길 바랍니다.",
                "재난 극복을 위해 함께하겠습니다."
            ]
            message = random.choice(messages)
            
            donations.append({
                'donation_id': donation_id,
                'user_id': user_id,
                'item_id': relief_item_id,
                'quantity': quantity,
                'donation_date': donation_date,
                'status': status,
                'message': message,
                'created_at': donation_date,
                'updated_at': donation_date + timedelta(days=random.randint(0, 7))
            })
            
        return pd.DataFrame(donations)
    
    def generate_donation_requests(self, shelters_df, relief_items_df):
        """기부 요청 테이블 데이터 생성"""
        requests = []
        
        for _ in range(self.config.REQUEST_COUNT):
            request_id = f"REQ{str(len(requests) + 1).zfill(6)}"
            shelter_id = random.choice(shelters_df['shelter_id'].tolist())
            relief_item_id = random.choice(relief_items_df['item_id'].tolist())
            
            # 요청 수량 (10-500개)
            requested_quantity = random.randint(10, 500)
            
            # 우선순위
            priority = random.choice(['low', 'medium', 'high', 'urgent'])
            
            # 요청 날짜
            request_date = self.fake.date_between(start_date='-3M', end_date='today')
            
            # 마감일 (요청일로부터 1-30일 후)
            deadline = request_date + timedelta(days=random.randint(1, 30))
            
            # 상태
            status = random.choice(['active', 'partially_fulfilled', 'fulfilled', 'expired'])
            
            # 요청 사유
            reasons = [
                "재난으로 인한 긴급 구호품 부족",
                "대피소 수용 인원 증가로 인한 추가 필요",
                "기존 재고 소진으로 인한 보충 필요",
                "계절 변화에 따른 필수품 요청",
                "특수 상황 대응을 위한 긴급 요청"
            ]
            reason = random.choice(reasons)
            
            requests.append({
                'request_id': request_id,
                'shelter_id': shelter_id,
                'item_id': relief_item_id,
                'requested_quantity': requested_quantity,
                'priority': priority,
                'request_date': request_date,
                'deadline': deadline,
                'status': status,
                'reason': reason,
                'created_at': request_date,
                'updated_at': request_date + timedelta(days=random.randint(0, 5))
            })
            
        return pd.DataFrame(requests)
    
    def generate_donation_matches(self, donations_df, requests_df):
        """기부-요청 매칭 테이블 데이터 생성"""
        matches = []
        
        # 기부와 요청을 구호품별로 그룹화
        for relief_item_id in donations_df['item_id'].unique():
            item_donations = donations_df[donations_df['item_id'] == relief_item_id]
            item_requests = requests_df[requests_df['item_id'] == relief_item_id]
            
            # 매칭 생성 (일부만 매칭)
            for _ in range(min(len(item_donations), len(item_requests)) // 2):
                if len(item_donations) == 0 or len(item_requests) == 0:
                    break
                    
                donation = item_donations.sample(1).iloc[0]
                request = item_requests.sample(1).iloc[0]
                
                match_id = f"MAT{str(len(matches) + 1).zfill(6)}"
                
                # 매칭 수량 (기부 수량과 요청 수량 중 작은 값)
                matched_quantity = min(donation['quantity'], request['requested_quantity'])
                
                # 매칭 날짜 (기부일과 요청일 중 늦은 날짜 이후)
                match_date = max(donation['donation_date'], request['request_date'])
                if isinstance(match_date, str):
                    match_date = datetime.strptime(match_date, '%Y-%m-%d').date()
                    
                # 매칭 상태
                match_status = random.choice(['pending', 'confirmed', 'in_transit', 'delivered', 'failed'])
                
                # 매칭 점수 (0.0-1.0)
                match_score = round(random.uniform(0.6, 1.0), 2)
                
                matches.append({
                    'match_id': match_id,
                    'donation_id': donation['donation_id'],
                    'request_id': request['request_id'],
                    'matched_quantity': matched_quantity,
                    'match_date': match_date,
                    'match_status': match_status,
                    'match_score': match_score,
                    'created_at': match_date,
                    'updated_at': match_date + timedelta(days=random.randint(0, 3))
                })
                
                # 사용된 기부와 요청 제거
                item_donations = item_donations.drop(donation.name)
                item_requests = item_requests.drop(request.name)
                
        return pd.DataFrame(matches)
    
    def generate_shipments(self, matches_df, shelters_df):
        """배송 테이블 데이터 생성"""
        shipments = []
        
        # 확정된 매칭에 대해서만 배송 생성
        confirmed_matches = matches_df[matches_df['match_status'].isin(['confirmed', 'in_transit', 'delivered'])]
        
        for _, match in confirmed_matches.iterrows():
            shipment_id = f"SHIP{str(len(shipments) + 1).zfill(6)}"
            
            # 배송 시작일 (매칭일 이후)
            ship_date = match['match_date']
            if isinstance(ship_date, str):
                ship_date = datetime.strptime(ship_date, '%Y-%m-%d').date()
            ship_date = ship_date + timedelta(days=random.randint(1, 3))
            
            # 예상 배송일 (배송 시작일로부터 1-7일 후)
            estimated_delivery = ship_date + timedelta(days=random.randint(1, 7))
            
            # 실제 배송일 (일부만 배송 완료)
            actual_delivery = None
            if random.random() < 0.7:  # 70% 확률로 배송 완료
                actual_delivery = estimated_delivery + timedelta(days=random.randint(-1, 2))
            
            # 배송 상태
            if actual_delivery:
                status = 'delivered'
            elif random.random() < 0.8:
                status = 'in_transit'
            else:
                status = 'pending'
            
            # 배송업체
            carriers = ['한진택배', 'CJ대한통운', '로젠택배', '우체국택배', '롯데택배']
            carrier = random.choice(carriers)
            
            # 송장번호
            tracking_number = f"{carrier[:2].upper()}{random.randint(100000000, 999999999)}"
            
            shipments.append({
                'shipment_id': shipment_id,
                'match_id': match['match_id'],
                'carrier': carrier,
                'tracking_number': tracking_number,
                'ship_date': ship_date,
                'estimated_delivery': estimated_delivery,
                'actual_delivery': actual_delivery,
                'status': status,
                'created_at': ship_date,
                'updated_at': actual_delivery if actual_delivery else ship_date + timedelta(days=1)
            })
            
        return pd.DataFrame(shipments)
    
    def generate_all_donation_data(self, users_df, shelters_df, relief_items_df):
        """모든 기부 관련 데이터 생성"""
        print("기부 데이터 생성 중...")
        donations_df = self.generate_donations(users_df, relief_items_df)
        
        print("기부 요청 데이터 생성 중...")
        requests_df = self.generate_donation_requests(shelters_df, relief_items_df)
        
        print("매칭 데이터 생성 중...")
        matches_df = self.generate_donation_matches(donations_df, requests_df)
        
        print("배송 데이터 생성 중...")
        shipments_df = self.generate_shipments(matches_df, shelters_df)
        
        return {
            'donations': donations_df,
            'donation_requests': requests_df,
            'donation_matches': matches_df,
            'shipments': shipments_df
        }