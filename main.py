import os
import requests
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# --- [설정] 텔레그램 봇 ---
def send_telegram_msg(msg):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass

# --- [설정] 비상용 종목 리스트 (데이터 수집 실패 시 사용) ---
# 삼성전자, 하이닉스, 네이버, 카카오, 현대차, 기아 등 시총 상위 20개
EMERGENCY_STOCKS = [
    ['005930', '삼성전자'], ['000660', 'SK하이닉스'], ['373220', 'LG에너지솔루션'],
    ['207940', '삼성바이오로직스'], ['005380', '현대차'], ['000270', '기아'],
    ['068270', '셀트리온'], ['005490', 'POSCO홀딩스'], ['035420', 'NAVER'],
    ['035720', '카카오'], ['006400', '삼성SDI'], ['051910', 'LG화학'],
    ['028260', '삼성물산'], ['105560', 'KB금융'], ['055550', '신한지주'],
    ['012330', '현대모비스'], ['032830', '삼성생명'], ['086790', '하나금융지주'],
    ['034020', '두산에너빌리티'], ['042660', '한화오션']
]

def get_target_stocks():
    # 1순위: 실시간 시가총액 상위 200개 가져오기 시도
    try:
        df = fdr.StockListing('KOSPI') # KRX 대신 KOSPI로 변경 (더 안정적)
        # Mar
