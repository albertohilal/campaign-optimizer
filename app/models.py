"""Database models for Campaign Optimizer."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnalysisReport(Base):
    """Persisted campaign analysis report."""

    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    customer_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    account_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    period_label: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        repr=False,
    )

    findings_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        repr=False,
    )

    recommendations_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        repr=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
    )