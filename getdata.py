# getdata.py
import requests

def fetch_activist_data(api_key: str, search_date: str) -> list:
    """
    공공데이터 포털 API를 호출하여 독립운동가 데이터를 수집합니다.
    """
    # 실제 API 엔드포인트 URL로 교체해야 합니다.
    url = "https://search.i815.or.kr/openApiData.do"
    
    params = {
        "serviceKey": api_key,
        "pageNo": "1",
        "numOfRows": "10",
        "returnType": "json",
    }

    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            # data = response.json()
            # 실제 데이터 추출 로직 필요
            
            # 테스트용 가상 데이터 반환
            return [{"name": "API_테스트_인물", "activity": f"{search_date} 관련 활동 데이터"}]
        else:
            # UI가 없는 파일이므로 print나 에러 메시지를 반환값으로 처리합니다.
            print(f"API 호출 실패: 에러 코드 {response.status_code}")
            return []
            
    except Exception as e:
        print(f"서버 통신 중 오류 발생: {e}")
        return []