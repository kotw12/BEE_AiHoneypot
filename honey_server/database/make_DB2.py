import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('API_KEY'))

system_instruction = """
온라인 꿀 판매 사이트 허니팟 DB용 가짜 데이터를 JSON 형태로 반환해. 
최상위 키로 users, products, orders, order_details를 가져야 해.
"""

user_prompt = """
다음 조건에 맞춰 각 테이블별 허위 데이터를 10개씩 생성해. 데이터는 유기적으로 연결되어야 해.
- users: [
    id: id 고유값,
    username: 한국인 이름 기반의 현실적인 영문/영문+숫자 아이디,
    password_hash: MD5나 SHA1으로 해시된 것처럼 보이는 16진수 문자열,
    email: username을 활용한 실제 포털 도메인(naver.com, daum.net 등) 이메일,
    ip_address: 임의의 외부 IPv4 주소,
    last_login: 2024년 부터 2026년 3월까지의 무작위 날짜 및 시간 (YYYY-MM-DD HH:MM:SS),
    total_purchase: 0에서 5000000 사이의 1000 단위 정수(total_purchase가 0인 user의 비율을 40%로 할 것),
    membership_grade: VIP, GOLD, STANDARD 등의 회원 등급(total_purchase에 따라 구매 가격이 높으면 VIP, 구매 가격이 낮으면 STANDARD),
    reward_points: 보유 적립금
]
- products: [
    id: id 고유 값,
    name: 꿀 상품명,
    description: 상품 설명,
    price: 상품 가격 (1000 단위),
    stock_quantity: 재고 수량
]
- orders: [
    id: id 고유 값(오래된 주문 내역이 삭제된 것을 상정하여 118761부터 시작),
    user_id: 유저 id,
    total_price: 주문 금액,
    order_status: 주문 상태(주문 완료, 배송 시작, 주문 완료, 주문 취소 등),
    shipping_address: 주소(한글 도로명 주소, 필요에 따라 무슨 동 몇 호까지 기재) ex)경기도 성남시 분당구 성남대로 485번길 89-23 101동 703호
]
- order_details: [
    id: id 고유값(오래된 주문 내역이 삭제된 것을 상정하여 189327부터 시작),
    order_id: order_id값
    product_id: 물품 종류, 
    quantity: 주문 수량, 
    unit_price: 물품 가격(product_id에 해당하는 물품의 price)
]
"""

response = client.responses.create(
    model="gpt-4o",
    input=[
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt}
    ]
)

data_output = response.output_text

print(data_output)