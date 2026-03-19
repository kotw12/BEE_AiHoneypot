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
if not api_key:
    # If the environment variable isn't set, provide a placeholder for the user to fill in
    # api_key = "sk-..." 
    pass

client = OpenAI(api_key=api_key)

# 1. GPT API에 사용할 프롬프트 작성
# 벌꿀을 판매하는 가상의 허니팟 환경을 위한 실제 같은 한국 고객 정보 생성 요구
SYSTEM_PROMPT = "You are a helpful assistant that generates mock data in strictly JSON format."

USER_PROMPT = """
너는 공격자(해커)를 속이기 위한 허니팟(벌꿀 판매 회사 서버)에 들어갈 가짜 고객 데이터를 생성하는 역할을 맡고 있어.
다음 규격에 맞는 가짜 한국인 고객 데이터 10개를 생성해서 오직 JSON 배열(Array) 형식으로만 반환해줘. 다른 설명이나 마크다운(```json 등)은 절대 포함하지 마.

[생성할 데이터 속성]
- "username": 해커가 흥미를 가질 만한 한국식 영문 이니셜이나 벌꿀, 곰 등과 관련된 영문+숫자 혼합 아이디 (예: honeybear88, admin_test, park_js99)
- "email": 아이디와 어울리는 이메일 주소 (예: honeybear88@honey.local 또는 개인 이메일 형식)
- "password_hash": 공격자가 평문 비밀번호를 유추하려고 시도할 만한 취약한 비밀번호(예: 123456, password, honey123 등)의 MD5 또는 SHA1 해시값 (예: MD5이면 32자리, SHA1이면 40자리 16진수 문자열). 실제 평문은 알려주지 말고 해시값만 넣어.
- "role": "user" (문자열)

[출력 형식 예시]
[
  {
    "username": "sweetbee99",
    "email": "sweetbee99@honey.local",
    "password_hash": "5d41402abc4b2a76b9719d911017c592",
    "role": "user"
  }
]
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
        users = json.loads(content)
        
        # SQLite 데이터베이스에 연결
        # conn = sqlite3.connect(DB_PATH)
        # c = conn.cursor()
        # 
        # count = 0
        # for user in users:
        #     # users 테이블에 값 삽입
        #     c.execute(
        #         "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
        #         (user["username"], user["email"], user["password_hash"], user["role"])
        #     )
        #     count += 1
        #     
        # conn.commit()
        # conn.close()
        # 
        # print(f"[+] 성공적으로 {count} 명의 가짜 사용자 정보를 {DB_PATH.name} 에 추가했습니다!")
        # for u in users:
        #     print(f"  - 생성된 유저: {u['username']} | 이메일: {u['email']}")

        print("생성된 사용자 정보 (테스트용):")
        print(json.dumps(users, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"[-] 데이터 생성 및 삽입 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    generate_and_insert_users()
