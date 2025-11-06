import axios from "axios";
import type { Task, TeamMember, TaskStatus } from "../types";

// Use environment variable or fallback to localhost
const API_BASE_URL =
  import.meta.env.VITE_API_URL || "https://internal-rag-backend.onrender.com ";

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor to ensure skills is always an array
api.interceptors.response.use(
  (response) => {
    // If response data is a team member or array of team members, ensure skills is array
    if (response.data) {
      if (Array.isArray(response.data)) {
        response.data = response.data.map((item: any) => {
          if (item.skills && !Array.isArray(item.skills)) {
            item.skills = [];
          }
          return item;
        });
      } else if (response.data.skills && !Array.isArray(response.data.skills)) {
        response.data.skills = [];
      }
    }
    return response;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const taskAPI = {
  createTask: async (description: string): Promise<Task> => {
    const response = await api.post<Task>("/tasks/", { description });
    return response.data;
  },

  getTasks: async (status?: TaskStatus): Promise<Task[]> => {
    const params = status ? { status } : {};
    const response = await api.get<Task[]>("/tasks/", { params });
    return response.data;
  },

  getTask: async (id: number): Promise<Task> => {
    const response = await api.get<Task>(`/tasks/${id}`);
    return response.data;
  },

  manualAssign: async (taskId: number, memberId: number): Promise<void> => {
    await api.post(`/tasks/${taskId}/assign/${memberId}`);
  },
};

export const teamAPI = {
  getTeamMembers: async (): Promise<TeamMember[]> => {
    const response = await api.get<TeamMember[]>("/team/");
    return response.data;
  },

  createTeamMember: async (
    member: Omit<TeamMember, "id" | "current_workload" | "created_at">
  ): Promise<TeamMember> => {
    const response = await api.post<TeamMember>("/team/", member);
    return response.data;
  },

  getTeamMember: async (id: number): Promise<TeamMember> => {
    const response = await api.get<TeamMember>(`/team/${id}`);
    return response.data;
  },

  updateTeamMember: async (
    id: number,
    member: Partial<TeamMember>
  ): Promise<TeamMember> => {
    const response = await api.put<TeamMember>(`/team/${id}`, member);
    return response.data;
  },

  deleteTeamMember: async (id: number): Promise<void> => {
    await api.delete(`/team/${id}`);
  },
};

export const chatAPI = {
  sendMessage: async (message: string): Promise<string> => {
    const response = await api.post<{ response: string }>("/chat/", {
      message,
    });
    return response.data.response;
  },
};
