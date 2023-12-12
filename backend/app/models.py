from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from typing_extensions import Annotated

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, TEXT


class StatusCategory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    status_list: List["Status"] = Relationship(back_populates="category")


class Status(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category_id: int = Field(foreign_key="statuscategory.id")

    category: StatusCategory = Relationship(back_populates="status_list")
    earthquake_list: List["Earthquake"] = Relationship(back_populates="status")


class Earthquake(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  wmo_id: str
  event_id: str
  author: Optional[str]
  category: Optional[str]
  depth: int
  depth_type: str
  latitude: Annotated[Decimal, Field(max_digits=9, decimal_places=7)]
  longitude: Annotated[Decimal, Field(max_digits=10, decimal_places=7)]
  magnitude: Annotated[Decimal, Field(max_digits=3, decimal_places=1)]
  magnitude_type: str
  origin_time: datetime
  location: str
  last_update: datetime
  source_domain: str
  status_id: int = Field(foreign_key="status.id", default=1)

  bulletin_list: List["Bulletin"] = Relationship(back_populates="earthquake")
  status: Status = Relationship(back_populates="earthquake_list")


class BulletinStatus(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  name: str

  bulletin_list: List["Bulletin"] = Relationship(back_populates="status")


class Bulletin(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  earthquake_id: int = Field(foreign_key="earthquake.id")
  issue_time: datetime
  discovery_time: datetime = Field(default_factory=datetime.utcnow)
  number: int
  wmo_id: str
  event_php: Optional[str]
  event_url: Optional[str]
  link: str
  bulletin_text: Optional[str] = Field(sa_column=Column(TEXT))
  status_id: int = Field(foreign_key="bulletinstatus.id", default=1)
  
  earthquake: Earthquake = Relationship(back_populates="bulletin_list")
  status: BulletinStatus = Relationship(back_populates="bulletin_list")

  async def get_text(self, http_session):
    """Retrieve the bulleting text"""

    ok = False
    async with http_session.get(f"{self.earthquake.source_domain}{self.link}") as resp:
      ok = resp.ok
      if ok:
        self.bulletin_text = await resp.text()

    return ok


class Threat(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  bulletin_id: int = Field(foreign_key="bulletin.id")
  threat_radius: Optional[int]
  threat_radius_unit: Optional[str]
  wave_speed: Optional[int]
  wave_speed_unit: Optional[str]
  wave_height: Optional[int]
  wave_height_unit: Optional[str]
  status_id: int = Field(foreign_key="statuscategory.id")


class FetchResponse(SQLModel):
  status_ok: bool
  status_code: int
  status_reason: str
  content_text: str