# Honey - 3-Server AWS Architecture
# 프로젝트 최종 구조

## 폴더 구조

```
servers/
├── main_server/          # EC2 #1 - 퍼블릭 쇼핑몰 (Port 80)
│   ├── app.py
│   ├── templates/
│   │   ├── base.html
│   │   └── index.html
│   ├── requirements.txt
│   ├── .env.example
│   └── start.sh
│
├── honey_server/         # EC2 #2 - 허니팟 서버 (Port 8080)
│   ├── app.py
│   ├── routers/
│   │   ├── honey_pages.py    # 페이지 라우터
│   │   └── honey_api.py      # 취약한 API 엔드포인트들
│   ├── core/
│   │   ├── logger.py         # 로컬 로깅 + Monitor Server 전송
│   │   └── detector.py       # 공격 패턴 감지기
│   ├── database/
│   │   └── init_db.py        # 가짜 SQLite DB 초기화
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── board.html
│   │   ├── chat.html
│   │   └── decoy_admin.html
│   ├── requirements.txt
│   ├── .env.example
│   └── start.sh
│
└── monitor_server/       # EC2 #3 - SOC 모니터링 (Port 9000, Private)
    ├── app.py
    ├── templates/
    │   └── dashboard.html
    ├── requirements.txt
    ├── .env.example
    └── start.sh
```

## AWS 구성

```
Internet
    │
[Internet Gateway]
    │
[Public Subnet 10.0.1.0/24]
    ├── EC2 #1  Main Server   (Port 80) ← Elastic IP 할당
    ├── EC2 #2  Honey Server  (Port 8080) ← 퍼블릭/동일 서브넷
    └── [NAT Gateway]
              │
    [Private Subnet 10.0.2.0/24]
              └── EC2 #3  Monitor Server (Port 9000, Private IP만)
```

## Security Group 설정

### Main Server SG
| 포트 | 소스 | 이유 |
|------|------|------|
| 80   | 0.0.0.0/0 | 공개 웹 |
| 22   | 내 IP만   | SSH |

### Honey Server SG
| 포트 | 소스 | 이유 |
|------|------|------|
| 8080 | 0.0.0.0/0 | **의도적으로 공개** (포트스캔으로 발견되게) |
| 22   | 내 IP만   | SSH |

### Monitor Server SG
| 포트 | 소스 | 이유 |
|------|------|------|
| 9000 | Honey Server SG만 | 허니팟에서 로그 수신 |
| 9000 | 내 IP만            | SOC 대시보드 접속 |
| 22   | 내 IP만            | SSH |

## 배포 방법

### 1. 각 EC2에 코드 배포
```bash
# 예: honey_server 배포
scp -r servers/honey_server ubuntu@<HONEY_IP>:~/honey_server
ssh ubuntu@<HONEY_IP> 'cd ~/honey_server && chmod +x start.sh && ./start.sh'
```

### 2. .env 환경변수 설정
```bash
# honey_server/.env
MONITOR_URL=http://10.0.2.50:9000    # Monitor Server 프라이빗 IP
LOG_SECRET=your-secure-secret-here

# monitor_server/.env
SOC_USER=soc_admin
SOC_PASS=your-secure-password
LOG_SECRET=your-secure-secret-here
OPENAI_API_KEY=sk-...
```

## 공격 시나리오 흐름

```
1. 공격자 → http://<MAIN_IP>/          (포트 80, 메인 쇼핑몰)
2. nmap <MAIN_IP> → 8080/tcp open      (포트스캔으로 허니팟 발견)
3. 공격자 → http://<MAIN_IP>:8080/login (관리자 로그인 폼 발견)
4. SQLi: admin' --                      (/api/login 우회)
5. 공격자 ↔ /decoy-admin               (관리자 대시보드 접근)
6. LFI: ../../database/mock.db         (/api/admin/view_log 경로탈취)
7. RCE: 127.0.0.1 & sqlite3 db.dump   (/api/admin/network_test 명령주입)
8. DB 탈취 완료  ← FLAG 노출

※ 모든 공격은 실시간으로 Monitor Server(9000)에 POST되어 SOC 대시보드에 표시됨
```
