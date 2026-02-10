import os
import requests

def test_telegram():
    # 1. 비밀번호 가져오기
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    print("--- 텔레그램 연결 테스트 시작 ---")
    
    # 2. 비밀번호가 제대로 들어왔는지 확인 (보안상 앞 5자리만 출력)
    if token:
        print(f"토큰 확인: {token[:5]}... (OK)")
    else:
        print("🚨 오류: 토큰(TELEGRAM_TOKEN)이 없습니다!")
        return

    if chat_id:
        print(f"채팅 ID 확인: {chat_id} (OK)")
    else:
        print("🚨 오류: 채팅 ID(TELEGRAM_CHAT_ID)가 없습니다!")
        return

    # 3. 메시지 보내보기
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    msg = "🔔 테스트 메시지입니다! 이게 보이면 성공입니다."
    payload = {"chat_id": chat_id, "text": msg}
    
    try:
        response = requests.post(url, json=payload)
        
        # 4. 결과 확인 (여기가 핵심!)
        print(f"응답 코드: {response.status_code}")
        print(f"텔레그램 답변: {response.text}")
        
        if response.status_code == 200:
            print("✅ 전송 성공! 핸드폰을 확인하세요.")
        else:
            print("❌ 전송 실패! 위 '텔레그램 답변'을 읽어보세요.")
            # 실패하면 강제로 에러를 내서 빨간불이 뜨게 함
            raise Exception("텔레그램 전송 실패")
            
    except Exception as e:
        print(f"에러 발생: {e}")
        raise e

if __name__ == "__main__":
    test_telegram()
