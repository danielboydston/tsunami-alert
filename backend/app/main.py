from typing import Annotated, List
from fastapi import Depends, FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from .db import engine
import logging
import aiohttp, asyncio
import re, json
from .models import Earthquake, Bulletin, FetchResponse
from .db import engine
from sqlalchemy import desc
from datetime import datetime, timedelta
from .bulletin_html_parser import BulletinHTMLParser

app = FastAPI(
    title="Tsunami Alert API",
    description="Know when an official Tsunami Threat has been issued for your location",
    version="0.0.1"
)

origins = [
    "http://localhost:8001",
    "https://localhost:8001",
    "http://fleet.airwarrior.net",
    "https://fleet.airwarrior.net"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

log_level = logging.DEBUG
logging.basicConfig(format='[%(asctime)s %(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=log_level)

#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
async def main():
    return {"detail": "Welcome to Tsunami Alert!"}


async def recent_all(http_session, url):
    event_items = []
    resp = await getURL(http_session, url)
    if resp.status_ok:
        event_text = resp.content_text
        event_text = event_text.strip()
        #event_text = re.sub(r'[\n\t]', '', event_text)
        event_text = re.sub(r'^\(', '', event_text)
        event_text = re.sub(r'\)$', '', event_text)
        # Remove trailing commas
        event_text = re.sub(r'("(?:\\?.)*?")|,\s*([]}])', r'\1\2', event_text)
        events = json.loads(event_text)
        event_items = events['items']
    return event_items


async def getURL(http_session: aiohttp.ClientSession, url: str) -> FetchResponse:
    """Get URL contents"""
    async with http_session.get(url) as resp:
        text = await resp.text()
        return FetchResponse(status_ok= resp.ok, status_code=resp.status, status_reason=resp.reason, content_text=text)
                                   

@app.get("/find-new")
async def find_new_events():
    """
    Find any new bulletins that have been issued since the last recorded bulletin
    """
    base_url = "https://tsunami.gov"
    event_url = "/php/esri.php?r=t&format=json"
    logging.debug(f"polling {base_url} for new events")
    async with aiohttp.ClientSession() as http_session:
        events = await recent_all(http_session, f"{base_url}{event_url}")
        with Session(engine) as db_session:
            for event in events:
                # Search for the event in the database
                    
                quake: Earthquake = db_session.exec(select(Earthquake).where(Earthquake.event_id == event['id']).order_by(desc(Earthquake.last_update))).first()
                if quake:
                    for b in event['bulletins']:
                        bulletin_found = False
                        for qb in quake.bulletin_list:
                            if b['WMOID'] == qb.wmo_id and int(b['bulletinNumber']) == qb.number:
                                bulletin_found = True
                                break
                        if not bulletin_found:
                            db_session.add(Bulletin(earthquake=quake, issue_time=event['issueTime'], number=b['bulletinNumber'], wmo_id=b['WMOID'], link=b['link']))
                            
                            logging.debug(f"Bulletin {b['WMOID']} #{b['bulletinNumber']} added to quake {quake.location}")
                    

                else:
                    origin_time = datetime.strptime(event['originTime'], "%Y-%m-%d %H:%M:%S.0")
                    issue_time = datetime.strptime(event['issueTime'], "%Y-%m-%d %H:%M:%S.0")
                    q = Earthquake(
                        wmo_id=event['msgID'], 
                        event_id=event['id'],
                        depth=event['depth'],
                        depth_type=event['depthType'],
                        latitude=event['lat'],
                        longitude=event['lon'],
                        magnitude=event['magnitude'],
                        magnitude_type=event['magnitudeType'],
                        origin_time=origin_time,
                        location=event['location'],
                        last_update=origin_time,
                        source_domain=base_url
                    )
                    logging.debug(f"added quake info. ID: {event['id']}, location: {event['location']}, magnitude: {event['magnitude']}, origin time: {event['originTime']}")
                    for b in event['bulletins']:
                        
                        q.bulletin_list.append(Bulletin(issue_time=issue_time, number=b['bulletinNumber'], wmo_id=b['WMOID'], link=b['link'], earthquake=q))
                        
                        logging.debug(f"  added bulletin {b['WMOID']} #{b['bulletinNumber']}")
                    db_session.add(q)
                        
            db_session.commit()   
    logging.debug("poll complete")
    return True


async def get_bulletin_text():
    date_threshold = datetime.utcnow() - timedelta(days=365)
    task_list = []
    logging.debug(f"checking for bulletins needing text pulled")
    async with aiohttp.ClientSession() as http_session:
        with Session(engine) as db_session:
            bulletins = db_session.exec(select(Bulletin).where(Bulletin.bulletin_text == None).where(Bulletin.issue_time > date_threshold)).all()
            for b in bulletins:
                task_list.append(b.get_text(http_session=http_session))

            bulletin_results = await asyncio.gather(*task_list, return_exceptions=True)

            for i in range(len(bulletin_results)):
                if bulletin_results[i]:
                    logging.debug(f"Retrieved bulletin text for {bulletins[i].earthquake.location} {bulletins[i].wmo_id} #{bulletins[i].number}")
                    db_session.add(bulletins[i])
                else:
                    logging.error(f"Failed to retrieve bulletin text: {bulletin_results[i].status_response}")
                
            db_session.commit()
    logging.debug(f"finished bulletins text pull")
 
@app.get("/bulletins/analyze")
async def analyze_bulletins():
    logging.debug(f"Analyzing Bulletins")
    section_re = re.compile(r'([A-Z ]+)(?:...UPDATED)?\n-{2,}\n([\s\S]+?)(?:(?:\n{3})|(?:\n\${2}))')
    item_re = re.compile(r'\* ([^*]+)')
    no_threat_re = re.compile(r'(?:there\s+is\s+no\s+tsunami\s+(?:(?:threat)|(?:danger)))|(?:the\s+earthquake\s+is\s+not\s+expected\s+to\s+generate\s+a\s+tsunami)|(?:the\s+tsunami\s+threat\s+from\s+this\s+earthquake\s+has\s+now\s+passed)',flags=re.IGNORECASE)
    threat_re = re.compile(r'tsunami\s+waves\s+are\s+(?:(?:forecast)|(?:possible))(?:[\s\S]+within\s+(\d+) (\w+))*', flags=re.IGNORECASE)
    threat_list = []
    no_threat_list = []
    indeterminate_threat_list = []
    with Session(engine) as db_session:
        bulletins = db_session.exec(select(Bulletin).where(Bulletin.status_id == 1)).all()
        for b in bulletins:
            sections = re.finditer(section_re, b.bulletin_text)
            for section in sections:
                item_count = 0
                title, body = section.group(1,2)
                
                items = re.finditer(item_re, body)
                if title == "EVALUATION":
                    threat_detected = False
                    no_threat_detected = False
                    for item in items:
                        item_text = item.group(1)
                        threat_match = re.search(threat_re, item_text)
                        if threat_match:
                            threat_detected = True
                            distance, distance_unit = threat_match.group(1,2)
                            if distance:
                                logging.debug(f"Distance threat from epicenter: {distance} {distance_unit}")
                            
                        no_threat_match = re.search(no_threat_re, item_text)
                        if no_threat_match:
                            no_threat_detected = True

                    if threat_detected and no_threat_detected:
                        logging.debug(f"Bulletin ID {b.id} Threat indeterminate - both true")
                        indeterminate_threat_list.append(b)
                    elif not threat_detected and not no_threat_detected:
                        logging.debug(f"Bulletin ID {b.id} Threat indeterminate - both false")
                        indeterminate_threat_list.append(b)
                    elif threat_detected:
                        logging.debug(f"Bulletin ID {b.id} Threat Detected")
                        threat_list.append(b)
                    elif no_threat_detected:
                        no_threat_list.append(b)
                        logging.debug(f"Bulletin ID {b.id} No Threat Detected")
                    else:
                        logging.error(f"Bulletin ID {b.id} Unexpected result")
                        
                 
            
                    
    #logging.debug(section_dict)
            
    logging.debug(f"Finished analyzing bulletins")
    return {"threat_list": threat_list, "no_threat_list": no_threat_list, "indeterminate": indeterminate_threat_list}


async def collect_data():
    sleep_duration = 60
    while True:
        try:
            await find_new_events()
            await get_bulletin_text()
        
        except Exception as e:
            logging.error(f"Error encountered: {e}")

        await asyncio.sleep(sleep_duration) 

asyncio.create_task(collect_data())

