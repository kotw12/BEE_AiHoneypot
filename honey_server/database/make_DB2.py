import json
import sqlite3
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('API_KEY'))

system_instruction = "You are a helpful assistant that generates mock data in strictly JSON format."

user_prompt = """
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
    "id": id 고유 값(오래된 주문 내역이 삭제된 것을 상정하여 168624부터 시작),
    "order_id": order_id 값 (orders 배열의 id),
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

response = client.responses.create(
    model="gpt-4o",
    input=[
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt}
    ]
)
data_output = response.output_text


def init_db(db_name="honeypot.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        real_name TEXT,
        password_hash TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        ip_address TEXT,
        role TEXT,
        zipcode TEXT,
        phone_number TEXT,
        last_login TEXT,
        total_purchase_amount INTEGER DEFAULT 0,
        purchase_count INTEGER DEFAULT 0,
        recent_purchase TEXT,
        membership_level TEXT,
        total_points INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        price INTEGER NOT NULL,
        stock_quantity INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        total_price INTEGER NOT NULL,
        order_status TEXT,
        shipping_address TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS order_details (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price INTEGER NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    );
    """)
    conn.commit()
    return conn

def insert_fake_data(conn, json_string):
    cursor = conn.cursor()
    
    cleaned_string = json_string.strip()
    if cleaned_string.startswith("```json"):
        cleaned_string = cleaned_string[7:]
    elif cleaned_string.startswith("```"):
        cleaned_string = cleaned_string[3:]
        
    if cleaned_string.endswith("```"):
        cleaned_string = cleaned_string[:-3]
        
    cleaned_string = cleaned_string.strip()
    
    try:
        data = json.loads(cleaned_string)
    except json.JSONDecodeError as e:
        print("JSON 파싱 에러 발생:", e)
        print("--- API 응답 원본 ---")
        print(cleaned_string)
        return

    if "users" in data:
        users = [(
            u.get("id"), u.get("username"), u.get("real_name"), u.get("password_hash"), 
            u.get("email"), u.get("ip_address"), u.get("role"), u.get("zipcode"), 
            u.get("phone_number"), u.get("last_login"), u.get("total_purchase_amount", 0), 
            u.get("purchase_count", 0), u.get("recent_purchase"), u.get("membership_level"), 
            u.get("total_points", 0)
        ) for u in data["users"]]
        cursor.executemany("""
            INSERT OR IGNORE INTO users 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, users)

    if "products" in data:
        products = [(p.get("id"), p.get("name"), p.get("description"), p.get("price"), p.get("stock_quantity")) for p in data["products"]]
        cursor.executemany("INSERT OR IGNORE INTO products VALUES (?, ?, ?, ?, ?)", products)

    if "orders" in data:
        orders = [(o.get("id"), o.get("user_id"), o.get("total_price"), o.get("order_status"), o.get("shipping_address")) for o in data["orders"]]
        cursor.executemany("INSERT OR IGNORE INTO orders VALUES (?, ?, ?, ?, ?)", orders)

    if "order_details" in data:
        details = [(od.get("id"), od.get("order_id"), od.get("product_id"), od.get("quantity"), od.get("unit_price")) for od in data["order_details"]]
        cursor.executemany("INSERT INTO order_details (id, order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?, ?)", details)

    conn.commit()
    print("데이터 DB 삽입 완료")


if __name__ == "__main__":
    db_conn = init_db()
    
    if 'data_output' in locals() or 'data_output' in globals():
        insert_fake_data(db_conn, data_output)
    else:
        print("data_output 변수가 정의되지 않았습니다.")
        
    db_conn.close()