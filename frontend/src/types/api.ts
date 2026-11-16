export interface User { id: string; email: string; email_verified_at: string|null; username: string; display_name: string | null; }
export interface Preferences {
  default_mode: "mind-dump" | "reflection"; memory_allowed: boolean; reflection_allowed: boolean;
  notification_enabled: boolean; notification_email_enabled: boolean; save_history: boolean; save_context_allowed: boolean;
  dark_mode: boolean; reduced_motion: boolean; text_size: "small" | "comfortable" | "large"; onboarding_complete: boolean;
}
export interface Conversation { id: string; started_at: string; ended_at: string | null; initial_mode: string; }
export interface Message { id: string; conversation_id: string; sender: string; content: string; created_at: string; active_mode: string; memory_allowed: boolean; photo_data?: string|null; }
export interface Capture { id: string; content: string; category: string; analysis_allowed: boolean; created_at: string; photo_data?: string|null; }
export interface PassportItem { id: string; section: "matters" | "support"; title: string; description: string; use_in_conversations: boolean; use_for_patterns: boolean; allow_reflections: boolean; created_at: string; }
export interface Reflection { id: string; content_text: string; hypothesis_id: string | null; status: string; created_at: string; }
export interface Pattern { id: string; statement_text: string; status: string; user_correction: string | null; evidence: {id: string; content: string; conversation_id: string}[]; }
export interface HistoryEntry { id: string; type: "conversation" | "quick-capture" | "reflection"; title: string; text: string; created_at: string; href: string; }
export interface HistoryData { items: HistoryEntry[]; total: number; counts: Record<string, number>; }
export interface ReviewedReflection extends Reflection {evidence:{message_id:string;quote:string;explanation:string;conversation_id:string;created_at:string}[];}
export interface Reminder {id:string;title:string;scheduled_at:string;status:"scheduled"|"completed";delivery_status:"pending"|"sending"|"sent"|"local-file"|"failed";destination:"reflection"|"notebook"|"conversation";reflection_id:string|null;}
export interface PreviewSchedule {enabled:boolean;cadence_days:7|14|30;next_run_at:string|null;last_run_at:string|null;last_status:string;last_reflection_id:string|null;}
