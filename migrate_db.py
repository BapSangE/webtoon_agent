# migrate_db.py
import requests
import xmltodict
from database import SessionLocal, Activist, init_db

# 검색할 10개 독립운동 계열 딕셔너리
movement_dict = {
    "3.1운동": "AA", "3.1운동지원": "AB", "계몽운동": "AC",
    "광복군": "AE", "국내항일": "AG", "만주방면": "AJ",
    "의병": "AN", "의열투쟁": "AO", "임시정부": "AR", "학생운동": "AU"
}

def fetch_and_parse_data(movement_code: str):
    """특정 계열의 독립운동가 명단을 API에서 끝까지 가져와 하나의 리스트로 반환합니다."""
    url = "https://search.i815.or.kr/openApiData.do"
    all_items = []
    last_page_data = None # 무한 루프 방지를 위한 변수
    
    for num in range(1, 2000):
        params = {
            "type": "4", 
            "movementFamily": movement_code,
            "isForeigner": "0",
            "page": num
        }
        
        try:
            # 1. 화면에 진행 상황 실시간 출력
            print(f"  -> {num}페이지 수집 중 (API 요청 대기)...", end='\r') 
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                parsed_dict = xmltodict.parse(response.text)
                items = parsed_dict.get('root', {}).get('item', None)
                
                # 2. 정상적인 종료 조건
                if not items:
                    print(f"\n  -> {num-1}페이지에서 데이터가 끝나 수집을 정상 완료했습니다.")
                    break 
                
                # 3. 비정상 무한 루프 방어 조건
                current_page_data = str(items)
                if current_page_data == last_page_data:
                    print(f"\n  -> {num}페이지부터 동일한 데이터가 반복 감지되어 수집을 강제 중단합니다.")
                    break
                last_page_data = current_page_data
                
                # 데이터 누적
                if isinstance(items, dict):
                    all_items.append(items)
                elif isinstance(items, list):
                    all_items.extend(items)
                    
            else:
                print(f"\nAPI 호출 실패 (코드 {movement_code}, 페이지 {num}): {response.status_code}")
                break
                
        except Exception as e:
            print(f"\nAPI 통신 중 에러 발생 (코드 {movement_code}, 페이지 {num}): {e}")
            break
            
    return all_items

def run_migration():
    """모든 계열을 순회하며 DB에 데이터를 적재합니다."""
    # 1. DB 뼈대 생성
    init_db()
    
    # 2. DB 세션 열기
    db = SessionLocal()
    total_inserted = 0
    
    try:
        for movement_name, code in movement_dict.items():
            print(f"\n[{movement_name}] 데이터 수집 시작...")
            
            items = fetch_and_parse_data(code)
            
            if not items:
                print(f"[{movement_name}] 수집된 데이터가 없습니다.")
                continue
                
            print(f"  => 총 {len(items)}명의 인물 데이터를 DB에 적재합니다.")
            
            inserted_count = 0
            for item in items:
                name = item.get('name', '이름불명')
                
                # 중복 데이터 검사
                exists = db.query(Activist).filter(
                    Activist.name_ko == name,
                    Activist.movement_type == movement_name
                ).first()
                
                if not exists:
                    new_activist = Activist(
                        movement_type=movement_name,
                        name_ko=name,
                        name_hanja=item.get('nameHanja') or '',
                        orders=item.get('orders') or '',
                        address_birth=item.get('addressBirth') or '',
                        aliases=item.get('aliases') or '',
                        born_died=item.get('bornDied') or '',
                        place_of_origin=item.get('placeOfOrigin') or '',
                        references=item.get('references') or '',
                        content=item.get('content') or '',
                        activities=item.get('activities') or '',
                        engaged_events=item.get('engagedEvents') or '',
                        engaged_organizations=item.get('engagedOrganizations') or '',
                        is_foreigner=item.get('isForeigner') or '',
                        raw_data=item 
                    )
                    db.add(new_activist)
                    inserted_count += 1
            
            # DB 확정(Commit)
            db.commit()
            total_inserted += inserted_count
            print(f"[{movement_name}] DB 적재 완료 (새로 추가됨: {inserted_count}건)")
            
        print(f"\n마이그레이션 전체 완료! 총 {total_inserted}건의 데이터 저장됨.")
        
    except Exception as e:
        db.rollback()
        print(f"마이그레이션 중 오류 발생: {e}")
    finally:
        db.close()

# 이 스크립트가 직접 실행될 때만 아래 함수를 가동 (매우 중요)
if __name__ == "__main__":
    run_migration()