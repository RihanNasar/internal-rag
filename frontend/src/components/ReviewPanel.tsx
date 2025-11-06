import React, { useState, useMemo, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { taskAPI, teamAPI } from "../services/api";
import { TaskStatus, Task, TeamMember } from "../types";
import {
  UserPlus,
  AlertCircle,
  Loader2,
  TrendingUp,
  Calendar,
  Search,
  X,
  UserCheck,
  Filter,
} from "lucide-react";
import "./ReviewPanel.css";

type FilterType = "all" | "available" | "low-workload" | "high-workload";

interface ConfirmationState {
  task: Task;
  member: TeamMember;
}

export const ReviewPanel: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<FilterType>("all");
  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [confirmationState, setConfirmationState] =
    useState<ConfirmationState | null>(null);
  const filterMenuRef = useRef<HTMLDivElement>(null);

  // Close filter menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        filterMenuRef.current &&
        !filterMenuRef.current.contains(event.target as Node)
      ) {
        setShowFilterMenu(false);
      }
    };

    if (showFilterMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showFilterMenu]);

  const {
    data: tasks,
    isLoading: tasksLoading,
    error: tasksError,
  } = useQuery({
    queryKey: ["review-tasks"],
    queryFn: () => taskAPI.getTasks(TaskStatus.MANUAL_REVIEW),
    refetchInterval: 5000,
  });

  const {
    data: teamMembers,
    isLoading: teamLoading,
    error: teamError,
  } = useQuery({
    queryKey: ["team-members"],
    queryFn: () => teamAPI.getTeamMembers(),
  });

  const assignMutation = useMutation({
    mutationFn: ({ taskId, memberId }: { taskId: number; memberId: number }) =>
      taskAPI.manualAssign(taskId, memberId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["review-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      queryClient.invalidateQueries({ queryKey: ["team-members"] });
    },
  });

  const handleAssign = (taskId: number, memberId: number) => {
    assignMutation.mutate({ taskId, memberId });
    setConfirmationState(null);
  };

  const showConfirmation = (task: Task, member: TeamMember) => {
    setConfirmationState({ task, member });
  };

  // Filter and search logic
  const getFilteredMembers = (members: typeof teamMembers) => {
    if (!members) return [];

    let filtered = [...members];

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (member) =>
          member.name.toLowerCase().includes(query) ||
          member.role.toLowerCase().includes(query) ||
          member.skills.some((skill) => skill.toLowerCase().includes(query))
      );
    }

    // Apply workload filter
    switch (filterType) {
      case "available":
        filtered = filtered.filter((m) => m.current_workload < m.max_workload);
        break;
      case "low-workload":
        filtered = filtered.filter(
          (m) => m.current_workload / m.max_workload < 0.5
        );
        break;
      case "high-workload":
        filtered = filtered.filter(
          (m) => m.current_workload / m.max_workload >= 0.75
        );
        break;
    }

    return filtered;
  };

  const filteredTeamMembers = useMemo(
    () => getFilteredMembers(teamMembers),
    [teamMembers, searchQuery, filterType]
  );

  if (tasksLoading || teamLoading) {
    return (
      <div className="review-loading-container">
        <div className="review-loading-content">
          <div className="loading-spinner-box">
            <Loader2 className="retro-spinner loading-spin" />
          </div>
          <p className="loading-text">LOADING REVIEW QUEUE...</p>
        </div>
      </div>
    );
  }

  if (tasksError || teamError) {
    return (
      <div className="review-error-container">
        <div className="review-error-content">
          <div className="error-icon-box">
            <AlertCircle className="error-icon" />
          </div>
          <h3 className="error-title">SYSTEM ERROR</h3>
          <p className="error-message">
            Failed to load review data. Refresh and retry connection.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="review-panel-container">
      {/* Retro Header */}
      <div className="review-header">
        <div className="review-header-icon">
          <AlertCircle className="header-icon" />
        </div>
        <div className="review-header-text">
          <h2 className="review-title">MANUAL REVIEW QUEUE</h2>
          <p className="review-subtitle">
            TASKS REQUIRING HUMAN JUDGMENT // LOW AI CONFIDENCE
          </p>
        </div>
        <div className="review-badge">{tasks?.length || 0} PENDING</div>
      </div>

      {/* Task Cards */}
      {tasks && tasks.length > 0 ? (
        <div className="review-tasks-list">
          {tasks.map((task) => (
            <div key={task.id} className="review-task-card">
              {/* Task Info */}
              <div className="review-task-header">
                <div className="task-info-main">
                  <div className="task-id-label">TASK #{task.id}</div>
                  <p className="task-description-review">{task.description}</p>
                  <div className="task-metadata">
                    <div className="confidence-indicator">
                      <TrendingUp className="metadata-icon" />
                      <span className="confidence-value">
                        {task.confidence_score
                          ? `${(task.confidence_score * 100).toFixed(0)}% MATCH`
                          : "N/A"}
                      </span>
                    </div>
                    {task.confidence_score && task.confidence_score < 0.75 && (
                      <div className="threshold-warning">
                        <AlertCircle className="metadata-icon" />
                        <span>BELOW THRESHOLD</span>
                      </div>
                    )}
                    <div className="date-indicator">
                      <Calendar className="metadata-icon" />
                      <span>
                        {new Date(task.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Team Member Selection */}
              <div className="team-selection-area">
                <div className="team-selection-header">
                  <div className="team-controls">
                    {/* Search Box */}
                    <div className="search-box">
                      <Search className="search-icon" />
                      <input
                        type="text"
                        className="search-input"
                        placeholder="Search name, role, or skills..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                      />
                    </div>

                    {/* Filter Dropdown */}
                    <div className="filter-dropdown" ref={filterMenuRef}>
                      <button
                        className={`filter-button ${
                          filterType !== "all" ? "active" : ""
                        }`}
                        onClick={() => setShowFilterMenu(!showFilterMenu)}
                      >
                        <Filter className="filter-icon" />
                        FILTER
                        {filterType !== "all" && (
                          <span className="filter-badge">1</span>
                        )}
                      </button>

                      {showFilterMenu && (
                        <div className="filter-menu">
                          <div className="filter-menu-header">
                            <Filter size={14} />
                            WORKLOAD FILTERS
                          </div>
                          <div className="filter-tags-menu">
                            <button
                              className={`filter-tag ${
                                filterType === "all" ? "active" : ""
                              }`}
                              onClick={() => {
                                setFilterType("all");
                                setShowFilterMenu(false);
                              }}
                            >
                              ALL
                            </button>
                            <button
                              className={`filter-tag ${
                                filterType === "available" ? "active" : ""
                              }`}
                              onClick={() => {
                                setFilterType("available");
                                setShowFilterMenu(false);
                              }}
                            >
                              AVAILABLE
                            </button>
                            <button
                              className={`filter-tag ${
                                filterType === "low-workload" ? "active" : ""
                              }`}
                              onClick={() => {
                                setFilterType("low-workload");
                                setShowFilterMenu(false);
                              }}
                            >
                              LOW
                            </button>
                            <button
                              className={`filter-tag ${
                                filterType === "high-workload" ? "active" : ""
                              }`}
                              onClick={() => {
                                setFilterType("high-workload");
                                setShowFilterMenu(false);
                              }}
                            >
                              HIGH
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {filteredTeamMembers && filteredTeamMembers.length > 0 ? (
                  <div className="team-members-grid">
                    {filteredTeamMembers.map((member) => {
                      const isAtCapacity =
                        member.current_workload >= member.max_workload;
                      const workloadPercentage =
                        (member.current_workload / member.max_workload) * 100;

                      return (
                        <button
                          key={member.id}
                          onClick={() => showConfirmation(task, member)}
                          disabled={isAtCapacity || assignMutation.isPending}
                          className={`team-card ${
                            isAtCapacity ? "at-capacity" : ""
                          } ${assignMutation.isPending ? "assigning" : ""}`}
                        >
                          {/* Member Info */}
                          <div className="team-card-header">
                            <div className="team-avatar">
                              <span className="avatar-initial">
                                {member.name.charAt(0)}
                              </span>
                            </div>
                            <div className="team-member-info">
                              <p className="member-name">{member.name}</p>
                              <p className="member-role">{member.role}</p>
                            </div>
                            {isAtCapacity && (
                              <span className="capacity-badge">MAX</span>
                            )}
                          </div>

                          {/* Skills */}
                          {member.skills && member.skills.length > 0 && (
                            <div className="member-skills">
                              {member.skills.slice(0, 3).map((skill, idx) => (
                                <span key={idx} className="skill-tag">
                                  {skill}
                                </span>
                              ))}
                              {member.skills.length > 3 && (
                                <span className="skill-tag">
                                  +{member.skills.length - 3}
                                </span>
                              )}
                            </div>
                          )}

                          {/* Workload Bar */}
                          <div className="workload-section">
                            <div className="workload-header">
                              <span>WORKLOAD</span>
                              <span className="workload-count">
                                {member.current_workload}/{member.max_workload}
                              </span>
                            </div>
                            <div className="workload-bar">
                              <div
                                className={`workload-fill ${
                                  workloadPercentage >= 100
                                    ? "critical"
                                    : workloadPercentage >= 75
                                    ? "warning"
                                    : "normal"
                                }`}
                                style={{
                                  width: `${Math.min(
                                    workloadPercentage,
                                    100
                                  )}%`,
                                }}
                              />
                              <div className="workload-segments">
                                <span></span>
                                <span></span>
                                <span></span>
                                <span></span>
                              </div>
                            </div>
                          </div>

                          {/* Assign Button (appears on hover) */}
                          {!isAtCapacity && (
                            <div className="assign-button-hover">
                              <UserPlus className="assign-icon" />
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <div className="no-team-members">
                    <p className="no-members-title">
                      {searchQuery || filterType !== "all"
                        ? "NO MATCHING TEAM MEMBERS"
                        : "NO TEAM MEMBERS AVAILABLE"}
                    </p>
                    <p className="no-members-text">
                      {searchQuery || filterType !== "all"
                        ? "Try adjusting your search or filter criteria."
                        : "Add team members to start assigning tasks"}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="review-empty-state">
          <div className="empty-state-icon">
            <AlertCircle className="empty-icon" />
          </div>
          <p className="empty-state-title">NO TASKS PENDING REVIEW</p>
          <p className="empty-state-message">
            All tasks auto-assigned with high confidence. System running
            optimally.
          </p>
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmationState && (
        <div
          className="assignment-modal-backdrop"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setConfirmationState(null);
            }
          }}
        >
          <div className="confirmation-modal">
            <div className="confirmation-header">
              <div className="confirmation-icon-box">
                <AlertCircle className="confirmation-icon" />
              </div>
              <div className="confirmation-header-text">
                <h3>CONFIRM ASSIGNMENT</h3>
                <p>MANUAL TASK DELEGATION</p>
              </div>
            </div>

            <div className="confirmation-body">
              <div className="confirmation-task">
                <p className="confirmation-task-label">
                  TASK #{confirmationState.task.id}
                </p>
                <p className="confirmation-task-text">
                  {confirmationState.task.description}
                </p>
              </div>

              <div className="confirmation-member">
                <div className="confirmation-avatar">
                  {confirmationState.member.name.charAt(0)}
                </div>
                <div className="confirmation-member-info">
                  <h4>{confirmationState.member.name}</h4>
                  <p>{confirmationState.member.role}</p>
                </div>
              </div>

              <div className="confirmation-warning">
                ⚡ EMAIL NOTIFICATION WILL BE SENT TO{" "}
                {confirmationState.member.email}
              </div>

              <div className="confirmation-actions">
                <button
                  className="cancel-button"
                  onClick={() => setConfirmationState(null)}
                >
                  <X className="button-icon" />
                  CANCEL
                </button>
                <button
                  className="confirm-button"
                  onClick={() =>
                    handleAssign(
                      confirmationState.task.id,
                      confirmationState.member.id
                    )
                  }
                >
                  <UserCheck className="button-icon" />
                  CONFIRM
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading Overlay */}
      {assignMutation.isPending && (
        <div className="assignment-modal-backdrop">
          <div className="assignment-modal">
            <div className="modal-spinner-box">
              <Loader2 className="modal-spinner loading-spin" />
            </div>
            <div className="modal-text-content">
              <p className="modal-title">ASSIGNING TASK...</p>
              <p className="modal-subtitle">SENDING NOTIFICATION EMAIL</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
