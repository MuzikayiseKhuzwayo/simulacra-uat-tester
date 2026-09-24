/**
 * Simulacra UAT Platform - API Client
 */

export const API_BASE = "http://127.0.0.1:8000";

export interface PersonaPreset {
  persona_id: string;
  name: string;
  role: string;
  age: number;
  technical_skill: string;
  patience: string;
  attention_span: string;
  reading_speed: string;
  risk_tolerance: string;
  biases: string[];
  primary_goal: string;
  device_type: string;
}

export interface CampaignSummary {
  campaign_id: string;
  title: string;
  target_url: string;
  total_sessions: number;
  successful_sessions: number;
  success_rate_percent: number;
  average_sus_score: number;
  average_friction_score: number;
  total_rage_clicks: number;
  created_at: string;
}

export interface SessionRecord {
  session_id: string;
  campaign_id: string;
  persona_id: string;
  persona_name: string;
  task_success: boolean;
  duration_seconds: number;
  total_steps: number;
  rage_clicks_total: number;
  friction_score: number;
  exit_reason: string;
}

export interface TelemetryEvent {
  event_id: string;
  step_number: number;
  action_type: string;
  page_url: string;
  page_title: string;
  target_element: string;
  hesitation_ms: number;
  cognitive_reasoning: string;
  emotion: string;
  confidence: number;
  screenshot_path?: string;
  rage_click: boolean;
}

export interface SimulationStepEvent {
  type: string;
  current_persona: number;
  total_personas: number;
  persona_name: string;
  persona_role: string;
  step_number: number;
  max_steps: number;
  action_type: string;
  page_url: string;
  page_title: string;
  cognitive_reasoning: string;
  emotion: string;
  confidence: number;
  hesitation_ms: number;
  campaign_id?: string;
}

export interface QuantixFeedback {
  form_id: string;
  campaign_id: string;
  session_id: string;
  persona_name: string;
  primary_role: string;
  submitted_at: string;
  clarity_10_15s: number;
  visual_design: number;
  credibility: number;
  gut_reaction: string[];
  convincing_element: string;
  hesitation_trigger: string;
  signup_method: string;
  info_requested_feeling: string;
  signup_technical_issues: string;
  relevance_rating: number;
  clarity_rating: number;
  progression_rating: number;
  engagement_rating: number;
  time_expected_vs_actual: string;
  comfort_answering_profile: string;
  awkward_question: string;
  navigating_intuitiveness: number;
  speed_responsiveness: number;
  reliability: number;
  initial_dashboard_feeling: string[];
  aha_moment: string;
  emotional_sentiment: string;
  most_frustrating_moment: string;
  missing_feature_expected: string;
  prior_alternative_used: string;
  nps_recommendation: number;
  nps_reason: string;
  pmf_feeling: string;
  magic_wand_change: string;
  discovery_source: string;
  role_in_selecting_tools: string;
  problem_space_knowledge: string;
  tech_comfort: number;
  problem_urgency: string;
  team_size: string;
  related_tools_used: string[];
  one_sentence_pitch: string;
  expected_transformation: string;
}

export interface StandardFeedback {
  feedback_id: string;
  campaign_id: string;
  session_id: string;
  persona_name: string;
  overall_rating: number;
  sus_score: number;
  ces_score: number;
  nps_rating: number;
  sentiment_summary: string;
  verbatim_quote: string;
  what_worked_well: string[];
  confusing_elements: string[];
  friction_points: string[];
  recommendations: string[];
}

export interface HealthStatus {
  status: string;
  engine: string;
  version: string;
  browser_automation: string;
}

export async function checkHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}

export async function fetchPresetPersonas(): Promise<PersonaPreset[]> {
  const res = await fetch(`${API_BASE}/api/personas/presets`);
  return res.json();
}

export async function fetchCampaigns(): Promise<CampaignSummary[]> {
  const res = await fetch(`${API_BASE}/api/campaigns`);
  return res.json();
}

export async function fetchCampaign(id: string) {
  const res = await fetch(`${API_BASE}/api/campaigns/${id}`);
  return res.json();
}

export async function fetchSessions(campaignId: string): Promise<SessionRecord[]> {
  const res = await fetch(`${API_BASE}/api/campaigns/${campaignId}/sessions`);
  return res.json();
}

export async function fetchFeedbacks(campaignId: string): Promise<{
  standard_feedbacks: StandardFeedback[];
  quantix_feedbacks: QuantixFeedback[];
}> {
  const res = await fetch(`${API_BASE}/api/campaigns/${campaignId}/feedbacks`);
  return res.json();
}

export async function fetchSessionTelemetry(sessionId: string): Promise<TelemetryEvent[]> {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/telemetry`);
  return res.json();
}

export async function startDemoApp() {
  const res = await fetch(`${API_BASE}/api/demo/start`, { method: "POST" });
  return res.json();
}

export async function autofillGoogleForm(campaignId: string, sessionId: string) {
  const res = await fetch(`${API_BASE}/api/surveys/fill-google-form`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      campaign_id: campaignId,
      session_id: sessionId,
      headless: true,
      submit: false,
    }),
  });
  return res.json();
}

export async function generateTestPack(payload: {
  requirement_id: string;
  title: string;
  user_story: string;
  acceptance_criteria: string[];
}) {
  const res = await fetch(`${API_BASE}/api/testpack/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

/**
 * Launch simulation and stream SSE progress events.
 */
export async function streamSimulation(
  payload: {
    target_url: string;
    campaign_title: string;
    primary_goal: string;
    cohort_mode: string;
    selected_preset_indices: number[];
    cohort_size: number;
    max_steps: number;
    headless: boolean;
    capture_screenshots: boolean;
  },
  onEvent: (event: SimulationStepEvent) => void
) {
  const response = await fetch(`${API_BASE}/api/simulation/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.body) {
    throw new Error("ReadableStream not supported by browser.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const chunk of lines) {
      if (chunk.startsWith("data: ")) {
        try {
          const jsonStr = chunk.replace(/^data:\s*/, "");
          const data = JSON.parse(jsonStr);
          onEvent(data);
        } catch (e) {
          console.error("Error parsing SSE chunk:", e, chunk);
        }
      }
    }
  }
}
