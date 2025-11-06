export const TaskStatus = {
  PENDING: "pending",
  AUTO_ASSIGNED: "auto_assigned",
  MANUAL_REVIEW: "manual_review",
  COMPLETED: "completed",
  REJECTED: "rejected",
} as const;

export type TaskStatus = (typeof TaskStatus)[keyof typeof TaskStatus];

export interface TeamMember {
  id: number;
  name: string;
  email: string;
  role: string;
  skills: string[];
  responsibilities: string;
  current_workload: number;
  max_workload: number;
  created_at: string;
}

export interface Task {
  id: number;
  description: string;
  status: TaskStatus;
  confidence_score: number | null;
  assigned_to: number | null;
  assigned_by: string;
  created_at: string;
  assigned_at: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  taskId?: number; // Optional task ID for tracking created tasks
}

export interface AssignmentRecommendation {
  team_member_id: number;
  team_member_name: string;
  team_member_email: string;
  confidence_score: number;
  reasoning: string;
  matched_skills: string[];
}
