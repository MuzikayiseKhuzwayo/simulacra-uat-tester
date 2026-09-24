"""Pydantic schemas for the Simulacra UAT FastAPI backend."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class LaunchSimulationRequest(BaseModel):
    target_url: str = Field(..., description="Target web application URL")
    campaign_title: str = Field("Live UAT Simulation", description="Campaign Title")
    primary_goal: str = Field(
        "Explore features, inspect pricing, sign up for a trial, and reach dashboard.",
        description="Goal for synthetic personas",
    )
    cohort_mode: str = Field("curated", description="'curated' or 'algorithmic'")
    selected_preset_indices: list[int] = Field(default_factory=lambda: [0, 1, 2])
    cohort_size: int = Field(5, description="Cohort size if algorithmic")
    max_steps: int = Field(12, ge=3, le=40)
    headless: bool = Field(True)
    capture_screenshots: bool = Field(True)


class PlaywrightFormFillRequest(BaseModel):
    campaign_id: str
    session_id: str
    headless: bool = True
    submit: bool = False


class TestPackRequest(BaseModel):
    requirement_id: str = "REQ-001"
    title: str = "Self-service Instant Invoicing"
    user_story: str = "As a small business owner, I want to create an invoice in 15 seconds so that I can bill clients immediately."
    acceptance_criteria: list[str] = Field(
        default_factory=lambda: [
            "AC-001 | Customer can specify client name and amount.",
            "AC-002 | Invoice is assigned a unique identifier upon creation.",
            "AC-003 | Status displays as Issued immediately.",
        ]
    )
