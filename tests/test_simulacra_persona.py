"""Unit tests for Persona generation and Archetype registry."""

from src.simulacra.models import PatienceLevel, TechnicalSkill
from src.simulacra.persona import (
    generate_cohort,
    get_default_personas,
    get_persona_by_id,
    get_preset_personas,
)


def test_preset_personas_integrity():
    presets = get_preset_personas()
    assert len(presets) >= 6
    ids = [p.persona_id for p in presets]
    assert len(ids) == len(set(ids)), "Persona IDs must be unique"

    sarah = get_persona_by_id("persona_sarah_smb")
    assert sarah is not None
    assert sarah.name == "Sarah Jenkins"
    assert sarah.technical_skill == TechnicalSkill.LOW
    assert sarah.patience == PatienceLevel.LOW


def test_generate_cohort_small():
    cohort = generate_cohort(count=3, custom_goal="Test mobile checkout")
    assert len(cohort) == 3
    for p in cohort:
        assert p.primary_goal == "Test mobile checkout"


def test_generate_cohort_large_diversity():
    cohort = generate_cohort(count=12, domain_context="FinTech SaaS")
    assert len(cohort) == 12
    # Ensure diverse skills and devices
    skills = {p.technical_skill for p in cohort}
    assert len(skills) > 1
    devices = {p.device_type for p in cohort}
    assert len(devices) > 1
