import os
import requests
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# --- 1. 텔레그램 전송 함수 ---
def send_telegram_msg(msg):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("토큰 없음")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass

# --- 2. 메인 분석 함수 ---
def screen_stocks():
    print("--- 주식 분석 시작 ---")
    
    # [데이터 수집 1] 전 종목 리스트 가져오기 (KRX 전체)
    try:
        # 네이버 금융 등에서 KRX 전체 리스트를 긁어옵니다.
        df_krx = fdr.StockListing('KRX')
        
        # 데이터가 잘 왔는지 확인
        if df_krx.empty:
            send_telegram_msg("🚨 종목 리스트를 가져오지 못했습니다. (빈 데이터)")
            return

        # 시가총액(MarCap) 순으로 정렬해서 상위 250개만 자르기 (200개 목표지만 여유 있게)
        # 컬럼 이름이 가끔 바뀔 수 있어 안전하게 처리
        if 'MarCap' in df_krx.columns:
            df_krx = df_krx.sort_values(by='MarCap', ascending=False)
        
        top_stocks = df_krx.head(250) # 상위 250개 추출
        print(f"대상 종목: {len(top_stocks)}개 로딩 완료")
        
    except Exception as e:
        send_telegram_msg(f"🚨 리스트 확보 실패: {e}")
        return

    selected_stocks = []
    today = datetime.now().strftime("%Y-%m-%d")

    # [데이터 수집 2] 개별 종목 분석 loop
    for index, row in top_stocks.iterrows():
        try:
            code = row['Code'] # 종목코드
            name = row['Name'] # 종목명
            
            # 최근 1년치 차트 데이터 가져오기
            df = fdr.DataReader(code, "2025-01-01") 
            
            if len(df) < 120: continue # 상장된 지 얼마 안 된 종목 패스

            # --- 기술적 분석 지표 계산 ---
            curr_price = df['Close'].iloc[-1]   # 현재가
            prev_vol = df['Volume'].iloc[-2]    # 전일 거래량
            curr_vol = df['Volume'].iloc[-1]    # 현재 거래량
            
            # 이동평균선 (50일, 150일, 200일)
            ma50 = df['Close'].rolling(50).mean().iloc[-1]
            ma150 = df['Close'].rolling(150).mean().iloc[-1]
            ma200 = df['Close'].rolling(200).mean().iloc[-1]
            
            # 52주 신고가/신저가
            high_52 = df['High'].iloc[-250:].max()
            low_52 = df['Low'].iloc[-250:].min()

            # --- [필터링 조건] ---
            # 1. 거래량: 전일 대비 2배 이상 터졌는가? (단, 0인 경우 제외)
            if prev_vol > 0 and curr_vol < prev_vol * 2: continue
            if prev_vol == 0: continue

            # 2. 정배열: 현재가 > 50일선 > 150일선 > 200일선
            if not (curr_price > ma50 > ma150 > ma200): continue

            # 3. 위치: 바닥에서 30% 이상 상승했고, 고점 대비 25% 이내인가?
            if curr_price < low_52 * 1.3: continue
            if curr_price < high_52 * 0.75: continue

            # --- 조건 만족 시 결과 담기 ---
            rate = (curr_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100
            selected_stocks.append(f"🔥 *{name}* ({code})\n  └ {rate:.1f}% 상승 / 거래량 폭발")
            print(f"발견: {name}")

        except Exception as e:
            continue

    # --- 3. 결과 전송 ---
    if selected_stocks:
        # 메시지가 너무 길면 나눠서 보내기 (텔레그램 제한)
        header = f"🚀 [{today}] 상위 250개 중 포착된 종목\n\n"
        final_msg = header + "\n".join(selected_stocks)
        
        if len(final_msg) > 4000: # 너무 길면 자름
            final_msg = final_msg[:4000] + "\n...(내용이 너무 길어 생략됨)"
            
        send_telegram_msg(final_msg)
    else:
        send_telegram_msg(f"🔔 [{today}] 조건에 맞는 종목이 없습니다.\n(상위 250개 분석 완료)")
    
    print("분석 종료")

if __name__ == "__main__":
    screen_stocks()
