import os
import requests
import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# 1. 텔레그램 전송 함수
def send_telegram_msg(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("🚨 토큰이 없습니다!")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"전송 실패: {e}")

def screen_stocks():
    # [1차 생존신고] 시작하자마자 메시지 보냄
    print("분석 시작...")
    send_telegram_msg("🔔 [1단계] 주식 분석 봇이 깨어났습니다! (데이터 수집 시작)")

    try:
        # 시가총액 상위 20개만 테스트 (속도 엄청 빠름)
        df_krx = fdr.StockListing('KRX')
        df_krx = df_krx.sort_values(by='MarCap', ascending=False)
        top20 = df_krx.head(20)
        
        send_telegram_msg(f"🔔 [2단계] 종목 리스트 확보 완료! ({len(top20)}개 분석 중...)")
        
    except Exception as e:
        send_telegram_msg(f"🚨 [2단계 실패] 목록 가져오기 에러: {e}")
        return

    selected_stocks = []
    
    # 20개 종목 반복 분석
    for index, row in top20.iterrows():
        try:
            code = row['Code']
            name = row['Name']
            
            # 차트 데이터 가져오기 (최근 100일)
            df = fdr.DataReader(code)
            
            if len(df) < 60: continue # 데이터 너무 적으면 패스

            # 간단한 조건: 어제보다 오늘 올랐으면 추천 (테스트용)
            curr_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2]
            
            if curr_price > prev_price:
                # 상승률 계산
                rate = (curr_price - prev_price) / prev_price * 100
                selected_stocks.append(f"{name} (+{rate:.1f}%)")
                print(f"발견: {name}")

        except Exception as e:
            print(f"에러({name}): {e}")
            continue

    # [3차 생존신고] 결과 전송
    if selected_stocks:
        msg = "🚀 [3단계 완료] 오늘의 상승 종목(테스트)\n\n" + "\n".join(selected_stocks)
    else:
        msg = "🔔 [3단계 완료] 오늘은 상승한 종목이 없네요."
    
    send_telegram_msg(msg)
    print("최종 완료")

if __name__ == "__main__":
    screen_stocks()
