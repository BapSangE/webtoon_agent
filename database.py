# database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# DB 연결 주소 (docker-compose 설정과 동일)
DATABASE_URL = "postgresql://user:qwer@localhost:5432/webtoon_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 1. 공공데이터 원본을 저장할 확장된 테이블 (황경중 지사 데이터 완벽 대응)
class Activist(Base):
    __tablename__ = "activists"

    id = Column(Integer, primary_key=True, index=True)
    movement_type = Column(String(50), index=True)     # 계열 (만주방면 등)
    name_ko = Column(String(100), index=True)          # name: 이름
    name_hanja = Column(String(100))                   # nameHanja: 한자 이름
    orders = Column(String(200))                       # orders: 서훈 내역
    address_birth = Column(String(200))                # addressBirth: 출신지/본적
    aliases = Column(String(200))                      # aliases: 이명/별명
    born_died = Column(String(100))                    # bornDied: 생몰년도
    place_of_origin = Column(String(200))              # placeOfOrigin: 출생지
    references = Column(Text)                          # references: 참고문헌
    content = Column(Text)                             # content: 상세 공적 내용
    activities = Column(Text)                          # activities: 활동 요약
    engaged_events = Column(String(200))               # engagedEvents: 관련 사건
    engaged_organizations = Column(String(200))        # engagedOrganizations: 관련 단체
    is_foreigner = Column(String(50))                  # isForeigner: 내외국인 여부
    
    raw_data = Column(JSONB)                           # 원본 JSON 데이터 전체

    # 연결 고리
    projects = relationship("WebtoonProject", back_populates="activist")

# 2. AI가 생성한 대본과 프롬프트를 저장할 테이블
class WebtoonProject(Base):
    __tablename__ = "webtoon_projects"

    project_id = Column(Integer, primary_key=True, index=True)
    activist_id = Column(Integer, ForeignKey("activists.id")) 
    character_appearance = Column(Text)                       
    storyboard_json = Column(JSONB)                           
    prompts_json = Column(JSONB)                              
    created_at = Column(DateTime, default=datetime.utcnow)    

    activist = relationship("Activist", back_populates="projects")

# 실행 시 빈 테이블을 DB에 실제로 생성
def init_db():
    Base.metadata.create_all(bind=engine)
    print("PostgreSQL 데이터베이스 테이블 세팅이 완료되었습니다.")

if __name__ == "__main__":
    init_db()