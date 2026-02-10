import os
import requests
import FinanceDataReader as fdr
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

def send_telegram_msg(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def screen_stocks():
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("Error: 텔레그램 토큰 없음")
        return

    today = datetime.now().strftime("%Y%m%d")
    print(f"[{today}] 분석을 시작합니다...")

    # 1. 시가총액 상위 500개 가져오기 (여기가 훨씬 튼튼해졌습니다!)
    # KRX 전체 종목 리스트를 가져와서 시가총액(MarCap) 순으로 정렬
    try:
        df_krx = fdr.StockListing('KRX')
        # 우선주 등 제외하고 정리
        df_krx = df_krx.dropna(subset=['MarCap']) 
        df_krx = df_krx.sort_values(by='MarCap', ascending=False)
        top500 = df_krx.head(500)
        print("시가총액 상위 500개 로딩 완료!")
    except Exception as e:
        print(f"목록 가져오기 실패: {e}")
        return

    selected_stocks = []
    
    # 2. 종목 분석 시작
    for index, row in top500.iterrows():
        try:
            ticker = row['Code'] # 종목코드
            name = row['Name']   # 종목명
            
            # 1년치 데이터 가져오기 (FDR 사용)
            # 오늘 날짜까지의 데이터를 가져옵니다.
            start_date_str = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
            df = fdr.DataReader(ticker, start_date_str)
            
            if len(df) < 200: continue 

            # 영어 컬럼명을 사용합니다 (Close, Volume 등)
            curr_price = df['Close'].iloc[-1]
            prev_vol = df['Volume'].iloc[-2]
            curr_vol = df['Volume'].iloc[-1]
            
            # 이동평균선
            ma50 = df['Close'].rolling(window=50).mean()
            ma150 = df['Close'].rolling(window=150).mean()
            ma200 = df['Close'].rolling(window=200).mean()
            
            # 52주 고가/저가
            df_52w = df.iloc[-250:]
            high_52w = df_52w['High'].max()
            low_52w = df_52w['Low'].min()

            # --- 조건 검사 ---
            # 1. 거래량 2배 이상 (0인 경우 방지)
            if prev_vol == 0: continue
            cond1 = curr_vol >= prev_vol * 2
            
            # 2. 정배열 (현재가 > 50 > 150 > 200)
            cond2 = (curr_price > ma50.iloc[-1] > ma150.iloc[-1] > ma200.iloc[-1])
            
            # 3. 이평선 상승 추세
            cond3 = (ma50.iloc[-1] > ma50.iloc[-5]) and \
                    (ma150.iloc[-1] > ma150.iloc[-5]) and \
                    (ma200.iloc[-1] > ma200.iloc[-5])
            
            # 4. 위치 조건
            cond4 = curr_price >= low_52w * 1.3
            cond5 = curr_price >= high_52w * 0.75
            
            if cond1 and cond2 and cond3 and cond4 and cond5:
                # 3. 수급 확인 (여기만 pykrx 사용 - 에러 나면 패스하도록 안전장치)
                try:
                    target_date = df.index[-1].strftime("%Y%m%d")
                    investor = stock.get_market_net_purchases_of_equities_by_ticker(target_date, target_date, ticker)
                    
                    foreigner = investor['외국인'].iloc[0]
                    institution = investor['기관합계'].iloc[0]
                    
                    if foreigner > 0 or institution > 0:
                        selected_stocks.append(f"{name} ({ticker})")
                        print(f"발견! -> {name}")
                except:
                    # 수급 데이터 못 가져와도 차트가 좋으면 일단 추천
                    selected_stocks.append(f"{name} ({ticker}) - 수급정보 없음")

        except Exception as e:
            continue

    # 결과 전송
    if selected_stocks:
        msg = f"🚀 {today} 추천 종목 (Top 500)\n\n" + "\n".join(selected_stocks)
    else:
        msg = f"🔔 {today} 조건에 맞는 종목이 없습니다."
    
    send_telegram_msg(token, chat_id, msg)
    print("전송 완료")

if __name__ == "__main__":
    screen_stocks()
