import sqlite3
import pathlib
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

# Find database path
DB_PATH = pathlib.Path(__file__).parent / "mock.db"
ENV_PATH = pathlib.Path(__file__).parent.parent / ".env"

# Load environment variables
load_dotenv(ENV_PATH)

# Retrieve OPENAI_API_KEY from environment or directly input here if needed
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

# 1. GPT API에 사용할 프롬프트 작성
# 벌꿀을 판매하는 가상의 허니팟 환경을 위한 실제 같은 한국 고객 정보 생성 요구
SYSTEM_PROMPT = "You are a helpful assistant that generates mock data in strictly JSON format."

USER_PROMPT = """
너는 공격자(해커)를 속이기 위한 허니팟(벌꿀 판매 회사 서버)에 들어갈 가짜 고객 데이터를 생성하는 역할을 맡고 있어.
이 사이트를 이용하는 실제 쇼핑몰 고객처럼 보이기 위해 상세한 정보가 필요해.
다음 조건에 맞춰 각 테이블별 허위 데이터를 10개씩 생성해. 데이터는 유기적으로 연결되어야 해.
결과는 반드시 오직 완전한 JSON 객체(Object) 형식으로만 반환해줘. 마크다운 기호(```json 등)나 다른 설명은 절대 추가하지 마.

[생성할 데이터 속성]
- users: [
    "id": id 고유값,
    "username": 한국인 이름 기반의 현실적인 영문/영문+숫자 아이디 (예: honeybear88, admin_test, park_js99),
    "real_name": 실명(한국어 형태의 이름),
    "password_hash": 공격자가 평문 비밀번호를 유추하려고 시도할 만한 취약한 비밀번호의 MD5 또는 SHA1 해시값 (예: 16진수 문자열). 실제 평문은 알려주지 말고 해시값만 넣어.
    "email": username을 활용한 실제 포털 도메인(naver.com, daum.net 등) 이메일,
    "ip_address": 임의의 외부 IPv4 주소,
    "role": "user" (문자열),
    "zipcode": 우편 번호 5자리 (예: 06234),
    "phone_number": 휴대전화 번호 (예: 010-1234-5678),
    "last_login": 2024년 부터 2026년 3월까지의 무작위 날짜 및 시간 (YYYY-MM-DD HH:MM:SS),
    "total_purchase_amount": 0에서 5000000 사이의 1000 단위 정수(값이 0인 user의 비율을 40%로 할 것),
    "purchase_count": 구매 횟수 (정수형, 예: 5, 12),
    "recent_purchase": 최근 구매 내역 ('지리산 야생화꿀', '프리미엄 밤꿀', '제주 유채꿀' 중 1개 선택),
    "membership_level": 총 구매 금액(total_purchase_amount)에 따라서 VIP, GOLD, STANDARD 등의 회원 등급 부여,
    "total_points": 보유 적립금
]
- products: [
    "id": id 고유 값,
    "name": 꿀 상품명 (예: 지리산 야생화꿀, 프리미엄 밤꿀, 제주 유채꿀 등),
    "description": 상품 설명,
    "price": 상품 가격 (1000 단위),
    "stock_quantity": 재고 수량
]
- orders: [
    "id": id 고유 값(오래된 주문 내역이 삭제된 것을 상정하여 118761부터 시작),
    "user_id": 유저 id (users 배열에 있는 id 사용),
    "total_price": 주문 금액,
    "order_status": 주문 상태(주문 완료, 배송 시작, 배송 완료, 주문 취소 등),
    "shipping_address": 주소(한글 도로명 주소, 필요에 따라 XX동 XX호까지 기재)
]
- order_details: [
    "id": order_id 값 (orders 배열의 id),
    "product_id": 물품 종류 (products 배열의 id), 
    "quantity": 주문 수량, 
    "unit_price": 물품 가격(product_id에 해당하는 물품의 price)
]

[출력 형식 예시]
{
  "users": [ { ... } ],
  "products": [ { ... } ],
  "orders": [ { ... } ],
  "order_details": [ { ... } ]
}
"""

def generate_and_insert_users():

    try:
        # GPT API 호출
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT}
            ],
            temperature=0.7 
        )
        
        content = response.choices[0].message.content.strip()
        
        # 마크다운(```json)이 포함된 경우 제거
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()

        # 파싱
        data = json.loads(content)
        users = data.get("users", [])
        
        # SQLite 데이터베이스에 연결
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        count = 0
        for user in users:
             # users 테이블에 값 삽입
             # 새 프롬프트에 맞춰 id, ip_address 등도 포함하도록 업데이트
             c.execute(
                 "INSERT INTO users (id, username, real_name, email, password_hash, role, zipcode, last_login, phone_number, ip_address, total_points, purchase_count, total_purchase_amount, recent_purchase, membership_level) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 (user.get("id"), user.get("username"), user.get("real_name", ""), user.get("email"), user.get("password_hash"), user.get("role", "user"), user.get("zipcode", ""), user.get("last_login", ""), user.get("phone_number", ""), user.get("ip_address", ""), user.get("total_points", 0), user.get("purchase_count", 0), user.get("total_purchase_amount", 0), user.get("recent_purchase", ""), user.get("membership_level", ""))
             )
             count += 1
             
        conn.commit()
        conn.close()
         
        print(f"[+] 성공적으로 {count} 명의 가짜 사용자 정보를 {DB_PATH.name} 에 추가했습니다!")
        for u in users:
            print(f"  - 생성된 유저: {u.get('username')} ({u.get('real_name', '알수없음')}) | 이메일: {u.get('email')}")

        print("\n--- 생성된 전체 데이터 (테스트용) ---")
        print(json.dumps(data, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"[-] 데이터 생성 및 삽입 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    generate_and_insert_users()
