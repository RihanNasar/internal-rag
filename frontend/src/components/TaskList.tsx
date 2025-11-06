import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { taskAPI, teamAPI } from "../services/api";
import { TaskStatus } from "../types";
import {
  CheckCircle,
  Clock,
  AlertCircle,
  XCircle,
  Calendar,
  User as UserIcon,
  TrendingUp,
} from "lucide-react";
import "./TaskList.css";

export const TaskList: React.FC = () => {
  const [selectedStatus, setSelectedStatus] = useState<TaskStatus | "all">(
    "all"
  );

  const {
    data: tasks,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["tasks", selectedStatus],
    queryFn: () =>
      taskAPI.getTasks(selectedStatus === "all" ? undefined : selectedStatus),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const { data: teamMembers } = useQuery({
    queryKey: ["team-members"],
    queryFn: () => teamAPI.getTeamMembers(),
  });

  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case TaskStatus.AUTO_ASSIGNED:
        return <CheckCircle className="w-4 h-4 text-emerald-600" />;
      case TaskStatus.PENDING:
        return <Clock className="w-4 h-4 text-amber-600" />;
      case TaskStatus.MANUAL_REVIEW:
        return <AlertCircle className="w-4 h-4 text-amber-600" />;
      case TaskStatus.COMPLETED:
        return <CheckCircle className="w-4 h-4 text-emerald-600" />;
      case TaskStatus.REJECTED:
        return <XCircle className="w-4 h-4 text-red-600" />;
    }
  };

  const getAssigneeName = (assignedTo: number | null): string => {
    if (!assignedTo || !teamMembers) return "Unassigned";
    const member = teamMembers.find((m) => m.id === assignedTo);
    return member ? member.name : "Unknown";
  };

  if (isLoading) {
    return (
      <div className="tasks-loading-container">
        <div className="tasks-loading-content">
          <div className="loading-spinner-box">
            <div className="retro-spinner" />
          </div>
          <p className="loading-text">LOADING TASK DATABASE...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="tasks-error-container">
        <div className="tasks-error-content">
          <div className="error-icon-box">
            <XCircle className="error-icon" />
          </div>
          <h3 className="error-title">SYSTEM ERROR</h3>
          <p className="error-message">
            Failed to establish connection with task database. Check backend
            status.
          </p>
          <button onClick={() => refetch()} className="retry-button">
            RETRY CONNECTION
          </button>
        </div>
      </div>
    );
  }

  const taskStats = {
    total: tasks?.length || 0,
    autoAssigned:
      tasks?.filter((t) => t.status === TaskStatus.AUTO_ASSIGNED).length || 0,
    pending: tasks?.filter((t) => t.status === TaskStatus.PENDING).length || 0,
    review:
      tasks?.filter((t) => t.status === TaskStatus.MANUAL_REVIEW).length || 0,
  };

  return (
    <div className="tasks-overview-container">
      {/* Retro Stats Dashboard */}
      <div className="stats-grid">
        {[
          {
            label: "TOTAL TASKS",
            count: taskStats.total,
            icon: TrendingUp,
            color: "coral",
          },
          {
            label: "AUTO ASSIGNED",
            count: taskStats.autoAssigned,
            icon: CheckCircle,
            color: "electric",
          },
          {
            label: "PENDING",
            count: taskStats.pending,
            icon: Clock,
            color: "butter",
          },
          {
            label: "NEEDS REVIEW",
            count: taskStats.review,
            icon: AlertCircle,
            color: "coral",
          },
        ].map((stat) => (
          <div key={stat.label} className={`stat-card stat-${stat.color}`}>
            <div className="stat-icon-box">
              <stat.icon className="stat-icon" />
            </div>
            <div className="stat-number">{stat.count}</div>
            <p className="stat-label">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Filter Tabs */}
      <div className="filter-tabs-container">
        {[
          { value: "all", label: "ALL TASKS" },
          { value: TaskStatus.AUTO_ASSIGNED, label: "AUTO ASSIGNED" },
          { value: TaskStatus.MANUAL_REVIEW, label: "MANUAL REVIEW" },
          { value: TaskStatus.PENDING, label: "PENDING" },
          { value: TaskStatus.COMPLETED, label: "COMPLETED" },
        ].map((tab) => (
          <button
            key={tab.value}
            onClick={() => setSelectedStatus(tab.value as any)}
            className={`filter-tab ${
              selectedStatus === tab.value ? "active" : ""
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Task Cards */}
      <div className="tasks-list">
        {tasks && tasks.length > 0 ? (
          tasks.map((task) => (
            <div key={task.id} className="task-card">
              {/* Header Row */}
              <div className="task-header">
                {/* Task ID Badge */}
                <div className="task-id-badge">TASK #{task.id}</div>

                {/* Status & Confidence */}
                <div className="task-meta-group">
                  <div className="task-status-badge">
                    {getStatusIcon(task.status)}
                    <span className="task-status-text">
                      {task.status.replace("_", " ")}
                    </span>
                  </div>
                  {task.confidence_score !== null && (
                    <div className="confidence-badge">
                      <div className="confidence-bar-container">
                        <div
                          className="confidence-bar-fill"
                          style={{ width: `${task.confidence_score * 100}%` }}
                        />
                        <div className="confidence-bar-segments">
                          <span></span>
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </div>
                      <span className="confidence-text">
                        {(task.confidence_score * 100).toFixed(0)}% MATCH
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Task Description */}
              <p className="task-description">{task.description}</p>

              {/* Footer: Meta + Assignee */}
              <div className="task-footer">
                <div className="task-timestamps">
                  <div className="timestamp-item">
                    <Calendar className="timestamp-icon" />
                    <span>
                      CREATED: {new Date(task.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {task.assigned_at && (
                    <div className="timestamp-item assigned">
                      <CheckCircle className="timestamp-icon" />
                      <span>
                        ASSIGNED:{" "}
                        {new Date(task.assigned_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>

                {/* Assignee Badge */}
                {task.assigned_to && (
                  <div className="task-assignee">
                    <UserIcon className="assignee-icon" />
                    <span className="assignee-name">
                      {getAssigneeName(task.assigned_to)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="tasks-empty-state">
            <div className="empty-state-icon">
              <Clock className="empty-icon" />
            </div>
            <p className="empty-state-title">NO TASKS FOUND</p>
            <p className="empty-state-message">
              {selectedStatus === "all"
                ? "Initialize system by creating first task via AI terminal"
                : `No tasks match filter: "${selectedStatus}"`}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
