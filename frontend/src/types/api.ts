/**
 * Typed API response interfaces matching the backend's output shapes.
 * Generated from backend/routes/upload.py, analysis.py and bridge_logic.py.
 */

// ─── Core scoring types ──────────────────────────────────────────────────

export interface ROIScores {
  A5: number;      // Auditory cortex (0–1)
  LO: number;      // Lateral occipital (0–1)
  Area45: number;  // Broca's area / CTA (0–1)
  TPJ: number;     // Temporoparietal junction / social (0–1)
}

export interface HookDetails {
  strength: 'Strong' | 'Moderate' | 'Weak';
  curiosity_gap_detected: boolean;
  question_detected: boolean;
}

export interface AuthenticityDetails {
  authenticity_level: 'High' | 'Moderate' | 'Low';
  brand_intrusion: 'Low' | 'High';
}

export interface SentimentForecast {
  positive_sentiment_pct: number;
  negative_sentiment_pct: number;
  neutral_sentiment_pct: number;
  backlash_risk: 'Low' | 'Moderate' | 'High';
  shareability_index: number;
  sellout_probability: number;
}

export interface CTAAnalysis {
  cta_activation_score: number;
  cognitive_load: 'Optimal' | 'High';
  timing_recommendation: string;
}

export interface StageGate {
  passed: boolean;
  message: string;
  W_attn: number;
  threshold: number;
}

// ─── Brain response ──────────────────────────────────────────────────────

export interface CorticalResponse {
  visual_cortex: number;
  auditory_cortex: number;
  language_center: number;
  amygdala: number;
  prefrontal_cortex: number;
  reward_center: number;
  social_cognition: number;
  memory_formation: number;
  overall_response_strength: number;
}

export interface EmotionalImpact {
  primary_emotion: 'excitement' | 'curiosity' | 'neutral';
  emotional_intensity: number;
}

export interface EngagementPrediction {
  overall_engagement: number;
  retention_prediction: 'high' | 'moderate' | 'low';
}

export interface TemporalSegment {
  segment: number;
  A5: number;
  LO: number;
  Area45: number;
  TPJ: number;
}

export interface TemporalDynamics {
  segments: TemporalSegment[];
}

export interface TRIBEBrainResponse {
  cortical_response: CorticalResponse;
  emotional_impact: EmotionalImpact;
  engagement_prediction: EngagementPrediction;
  temporal_dynamics: TemporalDynamics;
  mode: 'real' | 'simulated' | 'heuristic';
}

// ─── MiroFish simulation ─────────────────────────────────────────────────

export interface AgentGroup {
  label: string;
  count: number;
  sentiment: number;
  share_rate: number;
  engagement: number;
}

export interface MiroFishSimulation {
  final_sentiment: number;
  backlash_prediction: string;
  viral_coefficient: number;
  persona_breakdown: AgentGroup[];
  peak_reach?: number;
  seven_day_curve?: number[];
  mode?: string;
}

// ─── Main analysis response ───────────────────────────────────────────────

export interface Analysis {
  video_id: string;
  hook_score: number;
  hook_details: HookDetails;
  authenticity_score: number;
  authenticity_details: AuthenticityDetails;
  sentiment_forecast: SentimentForecast;
  cta_analysis: CTAAnalysis;
  viral_potential: number;
  success_probability: number;
  risk_score: number;
  recommendations: string[];
  mirofish_simulation: MiroFishSimulation;
  tribev2_brain_response: TRIBEBrainResponse;
  stage_gate: StageGate;
  transcript: string;
  full_transcript?: string;
  created_at: string;
  // Script/YouTube-specific
  analysis_type?: 'video' | 'script' | 'youtube';
  source?: 'file_upload' | 'text_input' | 'youtube_url';
  script_title?: string | null;
  youtube_metadata?: YouTubeMetadata;
}

export interface YouTubeMetadata {
  title: string;
  channel: string;
  view_count?: number;
  like_count?: number;
  published_at?: string;
  thumbnail_url?: string;
}

// ─── Video record ────────────────────────────────────────────────────────

export interface Video {
  id: string;
  user_id: string;
  filename: string;
  status: 'uploading' | 'processing' | 'analyzed' | 'error';
  upload_time: string;
  duration?: number;
}

// ─── Upload response ─────────────────────────────────────────────────────

export interface UploadResponse {
  video_id: string;
  status: string;
  message: string;
}

// ─── Task status (WebSocket / polling) ──────────────────────────────────

export interface TaskStatus {
  status: 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
  stage?: string;
  detail?: string;
}

// ─── Script rewrite ──────────────────────────────────────────────────────

export type RewriteDimension = 'hook' | 'authenticity' | 'cta';

export interface RewriteResult {
  rewritten_script: string;
  explanation: string;
  estimated_improvements: {
    before_score: number;
    after_score: number;
    rationale: string;
  };
}

// ─── A/B testing ─────────────────────────────────────────────────────────

export interface ABTestVariant {
  roi: ROIScores;
  W_attn: number;
  stage_gate_passed: boolean;
  social?: {
    initial_attention_weight: number;
    viral_coefficient: number;
    peak_reach: number;
    seven_day_curve: number[];
  };
}

// ─── Model status ─────────────────────────────────────────────────────────

export interface ModelStatus {
  tribev2: { status: string; type: string; model: string; mode: string };
  mirofish: { status: string; type: string; mode: string };
}
