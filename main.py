import os
import requests
import FinanceDataReader as fdr
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 텔레그램 전송 함수
def send_telegram_msg(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"전송 실패: {e}")

def screen_stocks():
    # 1. 텔레그램 설정
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    # 한국 시간 기준 날짜 설정 (서버는 UTC이므로 9시간 더함)
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime("%Y-%m-%d")
    today_compact = kst_now.strftime("%Y%m%d")

    print(f"[{today_str}] 주식 분석을 시작합니다...")

    # 2. 시가총액 상위 500
