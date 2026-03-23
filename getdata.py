# getdata.py
import requests
import xmltodict # 추가된 라이브러리 (pip install xmltodict 필요)

def fetch_activist_data(movement_code: str):
    """
    API를 호출하여 원본 XML과 파이썬 딕셔너리(JSON 형태)로 변환된 데이터를 모두 반환합니다.
    """
    # 실제 API 엔드포인트 URL로 교체 필요
    url = "https://search.i815.or.kr/openApiData.do"
    
    params = {
        "type": "4", # 인명사전 고정
        "movementFamily": movement_code,
        "isForeigner": "0",
        "page": "1"
    }

    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            xml_data = response.text
            
            # XML을 파이썬 딕셔너리로 자동 변환
            # API 응답이 정상적인 XML이 아닐 경우 에러가 날 수 있으므로 예외 처리가 포함되어야 안전합니다.
            try:
                dict_data = xmltodict.parse(xml_data)
            except Exception as parse_error:
                dict_data = {"error": f"XML 파싱 실패: {parse_error}"}
                
            return xml_data, dict_data
        else:
            return f"<error>API 호출 실패: 에러 코드 {response.status_code}</error>", None
            
    except Exception as e:
        return f"<error>서버 통신 중 오류 발생: {e}</error>", None