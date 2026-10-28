/**
 * EventWise — Unified API Contracts (TypeScript)
 *
 * Fully typed request & response interfaces and entity models matching backend Pydantic models.
 * Zero `any` types.
 */

/* ==========================================================================
   Common & Shared Primitives
   ========================================================================== */

export type ISO8601Timestamp = string;
export type UUIDString = string;

export interface MessageResponse {
  success: boolean;
  message: string;
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/* ==========================================================================
   Entity Models
   ========================================================================== */

export interface User {
  id: UUIDString;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: ISO8601Timestamp;
  updated_at: ISO8601Timestamp;
}

export type EventStatus = "draft" | "planning" | "confirmed" | "completed" | "cancelled";

export type EventType =
  "wedding" | "conference" | "birthday" | "corporate" | "social" | "workshop" | "community" | "other";

export interface Event {
  id: UUIDString;
  title: string;
  description: string;
  event_type: EventType;
  location: string;
  start_date: ISO8601Timestamp;
  end_date: ISO8601Timestamp;
  estimated_guest_count: number;
  total_budget: number;
  currency: string;
  status: EventStatus;
  owner_id: UUIDString;
  created_at: ISO8601Timestamp;
  updated_at: ISO8601Timestamp;
}

export type BudgetItemStatus = "planned" | "deposit_paid" | "paid" | "cancelled";

export interface BudgetItem {
  id: UUIDString;
  event_id: UUIDString;
  category: string;
  name: string;
  estimated_cost: number;
  actual_cost: number | null;
  paid_amount: number;
  status: BudgetItemStatus;
  vendor_id: UUIDString | null;
  notes: string;
  created_at: ISO8601Timestamp;
  updated_at: ISO8601Timestamp;
}

export type TaskStatus = "pending" | "in_progress" | "completed" | "delayed";

export interface TimelineTask {
  id: UUIDString;
  event_id: UUIDString;
  title: string;
  description: string;
  start_time: ISO8601Timestamp;
  end_time: ISO8601Timestamp;
  assigned_to: string | null;
  status: TaskStatus;
  category: string;
  order_index: number;
  created_at: ISO8601Timestamp;
  updated_at: ISO8601Timestamp;
}

export interface VendorChecklistItem {
  id: UUIDString;
  event_id: UUIDString;
  vendor_category: string;
  task_name: string;
  is_completed: boolean;
  due_date: ISO8601Timestamp | null;
  assigned_vendor_id: UUIDString | null;
  assigned_vendor_name: string | null;
  notes: string;
  created_at: ISO8601Timestamp;
  updated_at: ISO8601Timestamp;
}

export type IdeaSource = "ai" | "user";

export interface Idea {
  id: UUIDString;
  event_id: UUIDString;
  category: string;
  title: string;
  description: string;
  tags: string[];
  votes: number;
  is_selected: boolean;
  source: IdeaSource;
  created_at: ISO8601Timestamp;
  updated_at: ISO8601Timestamp;
}

export type GuestRsvpStatus = "pending" | "attending" | "declined" | "tentative";

export interface Guest {
  id: UUIDString;
  event_id: UUIDString;
  full_name: string;
  email: string;
  phone: string | null;
  rsvp_status: GuestRsvpStatus;
  dietary_restrictions: string[];
  plus_ones: number;
  table_number: number | null;
  notes: string;
  created_at: ISO8601Timestamp;
  updated_at: ISO8601Timestamp;
}

export interface ConceptBoardEntity {
  id: UUIDString;
  event_id: UUIDString;
  theme_title: string;
  theme_description: string;
  color_palette: string[];
  mood_keywords: string[];
  vibe_description: string;
  image_prompts: string[];
  image_urls: string[];
  typography_suggestions: string[];
  decor_notes: string;
  created_at: ISO8601Timestamp;
  updated_at: ISO8601Timestamp;
}

/* ==========================================================================
   Endpoint 1: Auth (POST /auth/signup, /auth/login, /auth/refresh)
   ========================================================================== */

export interface SignupRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

export interface TokenRefreshResponse {
  tokens: AuthTokens;
}

/* ==========================================================================
   Endpoint 2: Events (CRUD /events)
   ========================================================================== */

export interface EventListParams {
  page?: number;
  page_size?: number;
  status?: EventStatus;
  search?: string;
}

export type EventListResponse = PaginatedResult<Event>;

export interface CreateEventRequest {
  title: string;
  description: string;
  event_type: EventType;
  location: string;
  start_date: ISO8601Timestamp;
  end_date: ISO8601Timestamp;
  estimated_guest_count: number;
  total_budget: number;
  currency?: string;
  status?: EventStatus;
}

export interface UpdateEventRequest {
  title: string;
  description: string;
  event_type: EventType;
  location: string;
  start_date: ISO8601Timestamp;
  end_date: ISO8601Timestamp;
  estimated_guest_count: number;
  total_budget: number;
  currency: string;
  status: EventStatus;
}

export interface PatchEventRequest {
  title?: string;
  description?: string;
  event_type?: EventType;
  location?: string;
  start_date?: ISO8601Timestamp;
  end_date?: ISO8601Timestamp;
  estimated_guest_count?: number;
  total_budget?: number;
  currency?: string;
  status?: EventStatus;
}

export interface EventDetailResponse {
  event: Event;
  budget_summary: {
    total_budget: number;
    total_spent: number;
    remaining_budget: number;
  };
  timeline_summary: {
    total_tasks: number;
    completed_tasks: number;
  };
  guest_summary: {
    total_guests: number;
    confirmed_guests: number;
  };
}

/* ==========================================================================
   Endpoint 3: Budget (/events/{id}/budget)
   ========================================================================== */

export interface BudgetOverviewResponse {
  event_id: UUIDString;
  total_budget: number;
  total_allocated: number;
  total_spent: number;
  remaining_budget: number;
  currency: string;
  items: BudgetItem[];
}

export interface CreateBudgetItemRequest {
  category: string;
  name: string;
  estimated_cost: number;
  actual_cost?: number | null;
  paid_amount?: number;
  status?: BudgetItemStatus;
  vendor_id?: UUIDString | null;
  notes?: string;
}

export interface UpdateBudgetItemRequest {
  category?: string;
  name?: string;
  estimated_cost?: number;
  actual_cost?: number | null;
  paid_amount?: number;
  status?: BudgetItemStatus;
  vendor_id?: UUIDString | null;
  notes?: string;
}

/* ==========================================================================
   Endpoint 4: Timeline (/events/{id}/timeline)
   ========================================================================== */

export interface TimelineOverviewResponse {
  event_id: UUIDString;
  tasks: TimelineTask[];
  total_tasks: number;
  completed_tasks: number;
}

export interface CreateTimelineTaskRequest {
  title: string;
  description?: string;
  start_time: ISO8601Timestamp;
  end_time: ISO8601Timestamp;
  assigned_to?: string | null;
  status?: TaskStatus;
  category?: string;
  order_index?: number;
}

export interface UpdateTimelineTaskRequest {
  title?: string;
  description?: string;
  start_time?: ISO8601Timestamp;
  end_time?: ISO8601Timestamp;
  assigned_to?: string | null;
  status?: TaskStatus;
  category?: string;
  order_index?: number;
}

/* ==========================================================================
   Endpoint 5: Vendors Checklist (/events/{id}/checklist)
   ========================================================================== */

export interface VendorChecklistResponse {
  event_id: UUIDString;
  items: VendorChecklistItem[];
  total_items: number;
  completed_items: number;
}

export interface CreateVendorChecklistItemRequest {
  vendor_category: string;
  task_name: string;
  is_completed?: boolean;
  due_date?: ISO8601Timestamp | null;
  assigned_vendor_id?: UUIDString | null;
  assigned_vendor_name?: string | null;
  notes?: string;
}

export interface UpdateVendorChecklistItemRequest {
  vendor_category?: string;
  task_name?: string;
  is_completed?: boolean;
  due_date?: ISO8601Timestamp | null;
  assigned_vendor_id?: UUIDString | null;
  assigned_vendor_name?: string | null;
  notes?: string;
}

/* ==========================================================================
   Endpoint 6: AI (/events/{id}/generate-plan, /events/{id}/ideas, /events/{id}/chat)
   ========================================================================== */

export interface AIGeneratePlanRequest {
  user_prompt: string;
  tone?: "formal" | "casual" | "extravagant" | "minimalist" | "modern";
  focus_areas?: string[];
  max_budget?: number;
}

export interface SuggestedBudgetItem {
  category: string;
  name: string;
  estimated_cost: number;
  notes: string;
}

export interface SuggestedTimelineTask {
  title: string;
  description: string;
  relative_day: number;
  suggested_time: string;
  category: string;
}

export interface SuggestedVendorChecklistItem {
  vendor_category: string;
  task_name: string;
  recommended_lead_time_weeks: number;
  notes: string;
}

export interface AIGeneratePlanResponse {
  event_id: UUIDString;
  executive_summary: string;
  suggested_budget_allocation: SuggestedBudgetItem[];
  suggested_timeline: SuggestedTimelineTask[];
  suggested_vendor_checklist: SuggestedVendorChecklistItem[];
  key_recommendations: string[];
}

export interface AIGenerateIdeasRequest {
  category?: string;
  prompt?: string;
  count?: number;
}

export interface AIGenerateIdeasResponse {
  event_id: UUIDString;
  ideas: Idea[];
}

export type AIChatRole = "system" | "user" | "assistant";

export interface AIChatMessage {
  role: AIChatRole;
  content: string;
  timestamp?: ISO8601Timestamp;
}

export interface AIChatRequest {
  message: string;
  history?: AIChatMessage[];
}

export interface AIChatResponse {
  reply: string;
  model: string;
  suggested_actions: string[];
  tokens_used: number;
}

/* ==========================================================================
   Endpoint 7: Guests (CRUD /events/{id}/guests, POST /events/{id}/rsvp)
   ========================================================================== */

export interface GuestListParams {
  rsvp_status?: GuestRsvpStatus;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface GuestListResponse {
  items: Guest[];
  total: number;
  confirmed_count: number;
  declined_count: number;
  pending_count: number;
  total_attending_with_plus_ones: number;
}

export interface CreateGuestRequest {
  full_name: string;
  email: string;
  phone?: string | null;
  rsvp_status?: GuestRsvpStatus;
  dietary_restrictions?: string[];
  plus_ones?: number;
  table_number?: number | null;
  notes?: string;
}

export interface UpdateGuestRequest {
  full_name?: string;
  email?: string;
  phone?: string | null;
  rsvp_status?: GuestRsvpStatus;
  dietary_restrictions?: string[];
  plus_ones?: number;
  table_number?: number | null;
  notes?: string;
}

export interface RsvpSubmissionRequest {
  email: string;
  full_name?: string;
  rsvp_status: GuestRsvpStatus;
  plus_ones?: number;
  dietary_restrictions?: string[];
  notes?: string;
}

export interface RsvpSubmissionResponse {
  success: boolean;
  message: string;
  guest: Guest;
}

/* ==========================================================================
   Endpoint 8: Concept (POST /events/{id}/concept, /events/{id}/moodboard)
   ========================================================================== */

export interface CreateConceptRequest {
  theme_title: string;
  theme_description: string;
  mood_keywords: string[];
  color_palette: string[];
  vibe_description?: string;
  decor_notes?: string;
  typography_suggestions?: string[];
}

export interface GenerateMoodboardRequest {
  prompt_modifiers?: string[];
  style_preset?: string;
  color_focus?: string[];
  num_images?: number;
}

export interface ColorSwatch {
  name: string;
  hex_code: string;
  role: "primary" | "secondary" | "accent" | "neutral" | string;
}

export interface ScheduleMilestone {
  phase: string;
  activity: string;
  description: string;
}

export interface ConceptBoard {
  theme_name: string;
  vibe_summary: string;
  color_palette: ColorSwatch[];
  decor_motifs: string[];
  layout_ideas: string[];
  high_level_schedule: ScheduleMilestone[];
}

export interface SpatialDecorItem {
  zone: string;
  decor_elements: string[];
  lighting_and_ambiance: string;
  estimated_cost: number;
}

export interface DalleImagePrompt {
  target_zone: string;
  prompt: string;
  aspect_ratio: string;
  style_notes?: string;
}

export type GenAIImagePrompt = DalleImagePrompt;

export interface AIMoodboardResponse {
  concept_summary: string;
  total_decor_budget: number;
  spatial_decor_list: SpatialDecorItem[];
  image_prompts: DalleImagePrompt[];
}

export interface WhatIfScenarioRequest {
  adjusted_budget?: number;
  adjusted_guest_count?: number;
  vibe_adjustment?: string;
}

export interface SimulatedBudgetItem {
  category: string;
  allocated_amount: number;
  percentage: number;
  notes?: string;
}

export interface WhatIfScenarioResponse {
  event_id: string;
  baseline_budget: number;
  baseline_guest_count: number;
  scenario_budget: number;
  scenario_guest_count: number;
  cost_per_guest_baseline: number;
  cost_per_guest_scenario: number;
  budget_variance: number;
  plan: {
    event_type: string;
    guest_count: number;
    total_budget: number;
    location: string;
    items: SimulatedBudgetItem[];
    summary?: string;
  };
  analysis_summary: string;
}

/* ── AI Chat Contracts ───────────────────────────── */

export interface ToolExecutionRecord {
  tool_name: string;
  arguments: Record<string, unknown>;
  result_summary: string;
  status: "success" | "error";
}

export interface ChatTurnResponse {
  reply: string;
  tool_calls_executed: ToolExecutionRecord[];
  suggested_actions: string[];
}

export interface AIChatInputRequest {
  message: string;
  history?: Array<{ role: string; content: string }>;
  tool_call?: string;
}

/* ── Public Digital RSVP & FAQ Contracts ─────────── */

export interface PublicEventResponse {
  id: string;
  title: string;
  description: string;
  event_type: string;
  start_date?: string | null;
  end_date?: string | null;
  location: string;
}

export interface GuestFaqRequest {
  question: string;
  guest_name?: string;
}

export interface GuestFaqResponse {
  answer: string;
  event_title: string;
  suggested_questions: string[];
}
