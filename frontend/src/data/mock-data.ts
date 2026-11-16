import type { PassportItem, TimelineEntry } from "@/types";

export const passportValues: PassportItem[] = [
  { id: 1, title: "Being dependable", description: "I value being reliable and showing up for the people I care about." },
  { id: 2, title: "Doing work I’m proud of", description: "I feel most fulfilled when I can work on meaningful and challenging things." },
  { id: 3, title: "Having space to think", description: "I need quiet time to process my thoughts and make sense of things." },
];

export const supportPreferences: PassportItem[] = [
  { id: 1, title: "Gentle questions, one at a time", description: "I prefer to explore things gradually rather than being overwhelmed with too many questions." },
  { id: 2, title: "Being listened to before problem-solving", description: "It helps when I feel heard first, and advice can come later." },
];

export const timelineEntries: TimelineEntry[] = [
  { id: 1, date: "22 Sep 2026", time: "10:14 AM", title: "Feeling overwhelmed lately", detail: "College has been exhausting lately and I feel irritated at everyone.", type: "Conversation" },
  { id: 2, date: "21 Sep 2026", time: "1:32 PM", title: "Good presentation today!", detail: "Presentation actually went surprisingly well.", type: "Quick Capture" },
  { id: 3, date: "20 Sep 2026", time: "4:20 PM", title: "Reflection on group work", detail: "I noticed I take responsibility before checking what is actually mine.", type: "Reflection" },
  { id: 4, date: "19 Sep 2026", time: "6:58 PM", title: "Personal chats", detail: "A conversation that helped me feel less alone.", type: "Conversation" },
  { id: 5, date: "18 Sep 2026", time: "4:20 PM", title: "Assignment deadline", detail: "Workload and expectations appeared together again.", type: "Pattern" },
];
