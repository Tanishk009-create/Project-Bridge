export type ConversationMode = "Mind Dump" | "Deep Reflection";

export interface TimelineEntry {
  id: number;
  date: string;
  time: string;
  title: string;
  detail: string;
  type: "Conversation" | "Quick Capture" | "Reflection" | "Pattern";
}

export interface PassportItem {
  id: number;
  title: string;
  description: string;
}
