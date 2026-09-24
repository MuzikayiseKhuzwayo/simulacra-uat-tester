"""Synthetic Persona repository and generator for Simulacra UAT."""

import uuid
from typing import Sequence
from src.simulacra.models import (
    AttentionSpan,
    DeviceType,
    PatienceLevel,
    Persona,
    ReadingSpeed,
    RiskTolerance,
    TechnicalSkill,
)

PRESET_PERSONAS: list[Persona] = [
    Persona(
        persona_id="persona_sarah_smb",
        name="Sarah Jenkins",
        role="Small Business Owner",
        age=44,
        technical_skill=TechnicalSkill.LOW,
        patience=PatienceLevel.LOW,
        attention_span=AttentionSpan.LOW,
        reading_speed=ReadingSpeed.AVERAGE,
        risk_tolerance=RiskTolerance.CAUTIOUS,
        biases=[
            "Hates complex multi-step forms",
            "Expects obvious, single-click navigation",
            "Easily confused by technical jargon",
            "Abandons immediately when hit with unexpected errors",
        ],
        primary_goal="Complete primary onboarding and verify core feature works",
        device_type=DeviceType.DESKTOP,
        viewport_width=1280,
        viewport_height=800,
    ),
    Persona(
        persona_id="persona_marcus_exec",
        name="Marcus Vance",
        role="VP of Operations / Enterprise Buyer",
        age=39,
        technical_skill=TechnicalSkill.MEDIUM,
        patience=PatienceLevel.LOW,
        attention_span=AttentionSpan.LOW,
        reading_speed=ReadingSpeed.FAST,
        risk_tolerance=RiskTolerance.MODERATE,
        biases=[
            "Skips long marketing copy looking for clear pricing & ROI",
            "Abandons if registration takes longer than 90 seconds",
            "Hostile to forced demo bookings instead of self-serve trials",
            "Values security badges, compliance notices, and customer logos",
        ],
        primary_goal="Inspect pricing tiers and sign up for a free trial",
        device_type=DeviceType.DESKTOP,
        viewport_width=1440,
        viewport_height=900,
    ),
    Persona(
        persona_id="persona_priya_dev",
        name="Priya Sharma",
        role="Senior Developer",
        age=28,
        technical_skill=TechnicalSkill.HIGH,
        patience=PatienceLevel.HIGH,
        attention_span=AttentionSpan.HIGH,
        reading_speed=ReadingSpeed.FAST,
        risk_tolerance=RiskTolerance.ADVENTUROUS,
        biases=[
            "Prioritizes technical documentation and code samples over marketing",
            "Tests form validations with edge case inputs",
            "Inspects responsiveness and clean DOM layout",
            "Quickly notices misleading claims or fake metrics",
        ],
        primary_goal="Locate API/developer docs and test product workflows",
        device_type=DeviceType.DESKTOP,
        viewport_width=1920,
        viewport_height=1080,
    ),
    Persona(
        persona_id="persona_carl_elderly",
        name="Carl Miller",
        role="Retired Accountant",
        age=67,
        technical_skill=TechnicalSkill.LOW,
        patience=PatienceLevel.MEDIUM,
        attention_span=AttentionSpan.MEDIUM,
        reading_speed=ReadingSpeed.SLOW,
        risk_tolerance=RiskTolerance.CAUTIOUS,
        biases=[
            "Reads terms and instructions very carefully before clicking",
            "Skeptical of credit card prompts and upsells",
            "Struggles with low-contrast buttons and small fonts",
            "Expects persistent back buttons and clear undo options",
        ],
        primary_goal="Navigate through product information and understand privacy/terms",
        device_type=DeviceType.DESKTOP,
        viewport_width=1280,
        viewport_height=800,
    ),
    Persona(
        persona_id="persona_maya_mobile",
        name="Maya Lin",
        role="Digital Native / Mobile Consumer",
        age=23,
        technical_skill=TechnicalSkill.MEDIUM,
        patience=PatienceLevel.LOW,
        attention_span=AttentionSpan.LOW,
        reading_speed=ReadingSpeed.FAST,
        risk_tolerance=RiskTolerance.MODERATE,
        biases=[
            "Browses exclusively with fast thumb scrolling",
            "Expects large, unmistakable tap targets",
            "Rage-clicks on laggy or unresponsive buttons",
            "Prefers visual card layouts over dense tables",
        ],
        primary_goal="Explore product offerings and complete mobile conversion",
        device_type=DeviceType.MOBILE,
        viewport_width=390,
        viewport_height=844,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    ),
    Persona(
        persona_id="persona_david_qa",
        name="David O'Connor",
        role="Accessibility & Usability Auditor",
        age=34,
        technical_skill=TechnicalSkill.HIGH,
        patience=PatienceLevel.MEDIUM,
        attention_span=AttentionSpan.HIGH,
        reading_speed=ReadingSpeed.AVERAGE,
        risk_tolerance=RiskTolerance.CAUTIOUS,
        biases=[
            "Probes forms for missing error messages and broken state transitions",
            "Checks if navigation menus collapse or trap focus",
            "Flagging confusing button labels like 'Submit' vs 'Continue'",
            "Monitors page load latency and layout shifts",
        ],
        primary_goal="Audit workflow transitions, error boundaries, and user feedback",
        device_type=DeviceType.DESKTOP,
        viewport_width=1366,
        viewport_height=768,
    ),
]


def get_preset_personas() -> list[Persona]:
    """Return a deep copy list of preset synthetic user personas."""
    return [persona.model_copy(deep=True) for persona in PRESET_PERSONAS]


get_default_personas = get_preset_personas


def get_persona_by_id(persona_id: str) -> Persona | None:
    """Find a preset persona by its identifier."""
    for persona in PRESET_PERSONAS:
        if persona.persona_id == persona_id:
            return persona.model_copy(deep=True)
    return None


def generate_cohort(
    count: int = 5,
    custom_goal: str | None = None,
    domain_context: str | None = None,
) -> list[Persona]:
    """Generate a cohort of diverse synthetic user personas for testing.

    If count <= len(PRESET_PERSONAS), picks from the diverse preset pool.
    If count > len(PRESET_PERSONAS), generates parameterized variations with
    different combinations of technical skill, patience, and device types.
    """
    cohort: list[Persona] = []
    presets = get_preset_personas()

    # First draw from archetypes
    for i in range(min(count, len(presets))):
        p = presets[i]
        if custom_goal:
            p = p.model_copy(update={"primary_goal": custom_goal})
        cohort.append(p)

    # If more personas are requested, generate algorithmic variations
    names_pool = [
        ("Liam Chen", "E-Commerce Manager", TechnicalSkill.MEDIUM, PatienceLevel.LOW),
        ("Elena Rostova", "Operations Analyst", TechnicalSkill.HIGH, PatienceLevel.MEDIUM),
        ("Kofi Mensah", "Independent Consultant", TechnicalSkill.LOW, PatienceLevel.MEDIUM),
        ("Aisha Al-Mansoor", "Procurement Officer", TechnicalSkill.MEDIUM, PatienceLevel.LOW),
        ("Oliver Smith", "Freelance Designer", TechnicalSkill.HIGH, PatienceLevel.LOW),
        ("Fatima Zahra", "Customer Support Lead", TechnicalSkill.MEDIUM, PatienceLevel.HIGH),
        ("Lucas Silva", "Sales Representative", TechnicalSkill.LOW, PatienceLevel.LOW),
        ("Chloe Martin", "Healthcare Administrator", TechnicalSkill.LOW, PatienceLevel.MEDIUM),
    ]

    index = 0
    while len(cohort) < count:
        name, role, skill, patience = names_pool[index % len(names_pool)]
        unique_id = f"persona_gen_{uuid.uuid4().hex[:8]}"
        device = DeviceType.MOBILE if index % 3 == 0 else DeviceType.DESKTOP
        vp_w = 390 if device == DeviceType.MOBILE else 1280
        vp_h = 844 if device == DeviceType.MOBILE else 800

        goal = custom_goal or f"Explore {domain_context or 'application'} and complete user workflow"
        biases = [
            "Expects fast load times and clean UI",
            "Values clear error messages when something goes wrong",
            "Dislikes visual clutter and nested submenus",
        ]
        if patience == PatienceLevel.LOW:
            biases.append("Prone to rage-clicking when buttons take > 1s to respond")

        cohort.append(
            Persona(
                persona_id=unique_id,
                name=f"{name} #{len(cohort)+1}",
                role=role,
                age=25 + (index * 7) % 45,
                technical_skill=skill,
                patience=patience,
                attention_span=AttentionSpan.LOW if patience == PatienceLevel.LOW else AttentionSpan.MEDIUM,
                reading_speed=ReadingSpeed.AVERAGE,
                risk_tolerance=RiskTolerance.MODERATE,
                biases=biases,
                primary_goal=goal,
                device_type=device,
                viewport_width=vp_w,
                viewport_height=vp_h,
            )
        )
        index += 1

    return cohort
