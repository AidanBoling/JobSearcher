from flask_sqlalchemy import SQLAlchemy
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, Text
from datetime import datetime, timezone
from models.base import Base

db = SQLAlchemy(model_class=Base)


class TimestampMixin:
    created: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    # updated: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class JobPost(TimestampMixin, db.Model):    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_title: Mapped[str] = mapped_column(String(250))
    company_name: Mapped[str] = mapped_column(String(250))
    salary: Mapped[Optional[str]] = mapped_column(String(250))
    workplace_type: Mapped[Optional[str]] = mapped_column(String(250))
    employment_type: Mapped[str] = mapped_column(String(250))
    level: Mapped[Optional[str]] = mapped_column(String(250))
    description: Mapped[Optional[str]] = mapped_column(Text)
    job_board: Mapped[str] = mapped_column(String(250))
    post_id: Mapped[int] = mapped_column(Integer)
    post_link: Mapped[str] = mapped_column(String(250))
    posted_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    company_location: Mapped[Optional[str]] = mapped_column(String(250))
    company_other: Mapped[Optional[str]] = mapped_column(String(500))
    
    def __repr__(self):
        return f'<Job: {self.post_title} ({self.id})>'

# job_board, title, post_id, post_link, salary, description, posted_date, company_name, company_location, company_other

# Later TODO (probably): set up list of job_boards db, make relational. Useful for marking duplicates??

# Later TODO: Add "job type" and "location" columns