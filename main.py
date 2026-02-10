import os
import requests
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 텔레그램 전송 함수
def send_telegram_msg(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def screen_stocks():
    # 1. 텔레그램 설정 가져오기
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("Error: 텔레그램 토큰이나 ID가 설정되지 않았습니다.")
        return

    # 2. 가장 최근 영업일 찾기 (오류 수정된 부분)
    # 오늘부터 7일 전까지 데이터를 조회해서, 가장 마지막 날짜를 '기준일'로 잡습니다.
    today = datetime.now().strftime("%Y%m%d")
    start_check = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
    
    # 삼성전자(005930) 기준으로 날짜 확인 (가장 확실함)
    try:
        df_ref = stock.get_market_ohlcv_by_date(start_check, today, "005930")
        target_date = df_ref.index[-1].strftime("%Y%m%d")
        print(f"기준 날짜: {target_date}")
    except Exception as e:
        print("날짜 확인 중 오류 발생:", e)
        return

    # 3. 시가총액 상위 500개 가져오기
    df_cap = stock.get_market_cap(target_date, market="ALL")
    df_cap = df_cap.sort_values(by="시가총액", ascending=False)
    top500_tickers = df_cap.index[:500].tolist()
    
    selected_stocks = []
    
    print("분석 시작...")
    
    # 4. 종목 분석
    for ticker in top500_tickers: 
        try:
            # 400일치 데이터 가져오기
            start_date = (datetime.now() - timedelta(days=400)).strftime("%Y%m%d")
            df = stock.get_market_ohlcv_by_date(start_date, target_date, ticker)
            
            if len(df) < 200: continue 

            # 데이터 정리
            curr_price = df['종가'].iloc[-1]
            prev_vol = df['거래량'].iloc[-2]
            curr_vol = df['거래량'].iloc[-1]
            
            # 이동평균선
            ma50 = df['종가'].rolling(window=50).mean()
            ma150 = df['종가'].rolling(window=150).mean()
            ma200 = df['종가'].rolling(window=200).mean()
            
            # 52주 고가/저가
            df_52w = df.iloc[-250:]
            high_52w = df_52w['고가'].max()
            low_52w = df_52w['저가'].min()

            # --- 조건 검사 ---
            # 1. 거래량 2배 이상
            cond1 = curr_vol >= prev_vol * 2
            
            # 2. 정배열 (현재가 > 50 > 150 > 200)
            cond2 = (curr_price > ma50.iloc[-1] > ma150.iloc[-1] > ma200.iloc[-1])
            
            # 3. 이평선 상승 추세
            cond3 = (ma50.iloc[-1] > ma50.iloc[-5]) and \
                    (ma150.iloc[-1] > ma150.iloc[-5]) and \
                    (ma200.iloc[-1] > ma20
