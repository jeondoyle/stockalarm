import os
import requests
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

# 텔레그램으로 메시지 보내는 기능
def send_telegram_msg(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# 주식 분석하는 기능
def screen_stocks():
    # 깃허브에 저장해둔 비밀번호 가져오기
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("토큰이나 아이디가 없습니다!")
        return

    today = datetime.now().strftime("%Y%m%d")
    # 오늘 날짜 기준으로 가장 최근 영업일 찾기
    target_date = stock.get_nearest_business_day_in_inquiry_range(today)
    
    # 코스피, 코스닥 전 종목 가져오기
    tickers = stock.get_market_ticker_list(target_date, market="ALL")
    
    selected_stocks = []
    
    # 분석 시작 (시간이 좀 걸립니다)
    # 너무 오래 걸리지 않게 시가총액 상위 500개만 테스트하려면 tickers[:500] 으로 고치세요
    for ticker in tickers: 
        try:
            # 1년치 데이터 가져오기
            start_date = (datetime.now() - timedelta(days=400)).strftime("%Y%m%d")
            df = stock.get_market_ohlcv_by_date(start_date, target_date, ticker)
            
            if len(df) < 200: continue # 상장한 지 얼마 안 된 건 패스

            # 현재 가격, 거래량
            curr_price = df['종가'].iloc[-1]
            prev_vol = df['거래량'].iloc[-2]
            curr_vol = df['거래량'].iloc[-1]
            
            # 이동평균선 계산 (50일, 150일, 200일)
            ma50 = df['종가'].rolling(window=50).mean()
            ma150 = df['종가'].rolling(window=150).mean()
            ma200 = df['종가'].rolling(window=200).mean()
            
            # 52주 최고가, 최저가
            df_52w = df.iloc[-250:]
            high_52w = df_52w['고가'].max()
            low_52w = df_52w['저가'].min()

            # --- 조건 검사 ---
            # 1. 거래량이 어제보다 2배 이상인가?
            cond1 = curr_vol >= prev_vol * 2
            
            # 2. 정배열인가? (현재가 > 50일 > 150일 > 200일)
            cond2 = (curr_price > ma50.iloc[-1] > ma150.iloc[-1] > ma200.iloc[-1])
            
            # 3. 이동평균선이 위로 올라가고 있는가? (5일 전보다 높은지)
            cond3 = (ma50.iloc[-1] > ma50.iloc[-5]) and \
                    (ma150.iloc[-1] > ma150.iloc[-5]) and \
                    (ma200.iloc[-1] > ma200.iloc[-5])
            
            # 4. 바닥에서 30% 이상 올랐고, 천장에서 25% 이내인가?
            cond4 = curr_price >= low_52w * 1.3
            cond5 = curr_price >= high_52w * 0.75
            
            if cond1 and cond2 and cond3 and cond4 and cond5:
                name = stock.get_market_ticker_name(ticker)
                # 수급 확인 (외국인, 기관이 샀는지)
                investor = stock.get_market_net_purchases_of_equities_by_ticker(target_date, target_date, ticker)
                # 외국인이나 기관 둘 중 하나라도 샀으면 통과
                if investor['외국인'].iloc[0] > 0 or investor['기관합계'].iloc[0] > 0:
                    selected_stocks.append(f"{name} ({ticker})")
                    
        except:
            continue

    # 결과 보내기
    if selected_stocks:
        msg = f"🚀 {today} 추천 종목 리스트\n\n" + "\n".join(selected_stocks)
    else:
        msg = f"🔔 {today} 조건에 맞는 종목이 없습니다."
    
    send_telegram_msg(token, chat_id, msg)

if __name__ == "__main__":
    screen_stocks()