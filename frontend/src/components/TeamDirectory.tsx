import { useState, useEffect, useRef } from "react";
import "./TeamDirectory.css";

interface TeamMember {
  id: number;
  name: string;
  email: string;
  role: string;
  skills: string[];
  responsibilities: string;
  current_workload: number;
  max_workload: number;
  is_active: boolean;
}

const TeamDirectory = () => {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [filterRole, setFilterRole] = useState<string>("all");
  const [showFilterMenu, setShowFilterMenu] = useState(false);
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

  useEffect(() => {
    fetchTeamMembers();

    // Refresh team members every 10 seconds
    const interval = setInterval(() => {
      fetchTeamMembers();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const fetchTeamMembers = async () => {
    try {
      setLoading(true);
      console.log("🔄 Fetching team members...");
      const response = await fetch(
        "https://internal-rag-backend.onrender.com/api/team/"
      );
      if (!response.ok) {
        throw new Error("Failed to fetch team members");
      }
      const data = await response.json();
      console.log(`✅ Loaded ${data.length} team members`);
      setTeamMembers(data);
      setError("");
    } catch (err) {
      setError("Failed to load team members");
      console.error("Error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Get unique roles for filter
  const roles = ["all", ...new Set(teamMembers.map((m) => m.role))];

  // Filter team members
  const filteredMembers = teamMembers.filter((member) => {
    const matchesSearch =
      member.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      member.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      member.role.toLowerCase().includes(searchTerm.toLowerCase()) ||
      member.skills.some((skill) =>
        skill.toLowerCase().includes(searchTerm.toLowerCase())
      );

    const matchesRole = filterRole === "all" || member.role === filterRole;

    return matchesSearch && matchesRole && member.is_active;
  });

  const getWorkloadPercentage = (current: number, max: number) => {
    return (current / max) * 100;
  };

  const getWorkloadStatus = (current: number, max: number) => {
    const percentage = getWorkloadPercentage(current, max);
    if (percentage >= 90) return "critical";
    if (percentage >= 70) return "warning";
    return "normal";
  };

  if (loading) {
    return (
      <div className="team-container">
        <div className="team-loading">
          <div className="team-spinner"></div>
          <p>Loading team directory...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="team-container">
        <div className="team-error">
          <div className="team-error-icon">⚠</div>
          <p>{error}</p>
          <button className="team-retry-button" onClick={fetchTeamMembers}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="team-container">
      {/* Header */}
      <div className="team-header">
        <div className="team-header-content">
          <div className="team-header-left">
            <div className="team-led-active"></div>
            <h1 className="team-header-title">TEAM DIRECTORY</h1>
          </div>
          <div className="team-header-right">
            <button
              className="team-refresh-button"
              onClick={fetchTeamMembers}
              title="Refresh team members"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                width="20"
                height="20"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </button>
            <div className="team-header-count">
              <span className="team-count-number">
                {filteredMembers.length}
              </span>
              <span className="team-count-label">Members</span>
            </div>
          </div>
        </div>
        <div className="team-header-accent"></div>
      </div>

      {/* Stats Overview */}
      <div className="team-stats-grid">
        <div className="team-stat-box team-stat-coral">
          <div className="team-stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
          </div>
          <div className="team-stat-value">
            {teamMembers.filter((m) => m.is_active).length}
          </div>
          <div className="team-stat-label">Active Members</div>
        </div>

        <div className="team-stat-box team-stat-electric">
          <div className="team-stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
          </div>
          <div className="team-stat-value">{roles.length - 1}</div>
          <div className="team-stat-label">Unique Roles</div>
        </div>

        <div className="team-stat-box team-stat-butter">
          <div className="team-stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="team-stat-value">
            {teamMembers.reduce((sum, m) => sum + m.current_workload, 0)}
          </div>
          <div className="team-stat-label">Total Tasks</div>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="team-controls">
        <div className="team-search-box">
          <svg
            className="team-search-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            className="team-search-input"
            placeholder="Search by name, role, or skills..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="team-filter-dropdown" ref={filterMenuRef}>
          <button
            className={`team-filter-button ${
              filterRole !== "all" ? "active" : ""
            }`}
            onClick={() => setShowFilterMenu(!showFilterMenu)}
          >
            <svg
              className="team-filter-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
              />
            </svg>
            FILTER
            {filterRole !== "all" && (
              <span className="team-filter-badge">1</span>
            )}
          </button>

          {showFilterMenu && (
            <div className="team-filter-menu">
              <div className="team-filter-menu-header">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  width="14"
                  height="14"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
                ROLE FILTERS
              </div>
              <div className="team-filter-tags">
                {roles.map((role) => (
                  <button
                    key={role}
                    className={`team-filter-tag ${
                      filterRole === role ? "active" : ""
                    }`}
                    onClick={() => {
                      setFilterRole(role);
                      setShowFilterMenu(false);
                    }}
                  >
                    {role === "all" ? "ALL" : role.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Team Members Grid */}
      {filteredMembers.length === 0 ? (
        <div className="team-empty">
          <div className="team-empty-header">
            <div className="team-empty-stripe"></div>
            <h3 className="team-empty-title">NO MEMBERS FOUND</h3>
          </div>
          <div className="team-empty-content">
            <div className="team-empty-icon">👥</div>
            <p className="team-empty-text">
              {searchTerm || filterRole !== "all"
                ? "No team members match your search criteria"
                : "No team members in the directory"}
            </p>
            {(searchTerm || filterRole !== "all") && (
              <button
                className="team-clear-button"
                onClick={() => {
                  setSearchTerm("");
                  setFilterRole("all");
                }}
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="team-members-grid">
          {filteredMembers.map((member) => {
            const workloadStatus = getWorkloadStatus(
              member.current_workload,
              member.max_workload
            );
            const workloadPercentage = getWorkloadPercentage(
              member.current_workload,
              member.max_workload
            );

            return (
              <div key={member.id} className="team-member-card">
                {/* Card Header */}
                <div className="team-card-header">
                  <div className="team-avatar">
                    {member.name
                      .split(" ")
                      .map((n) => n[0])
                      .join("")
                      .toUpperCase()}
                  </div>
                  <div className="team-card-info">
                    <h3 className="team-member-name">{member.name}</h3>
                    <p className="team-member-email">{member.email}</p>
                  </div>
                  <div
                    className={`team-status-led team-status-${workloadStatus}`}
                  ></div>
                </div>

                {/* Role Badge */}
                <div className="team-role-badge">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                  <span>{member.role}</span>
                </div>

                {/* Responsibilities */}
                <div className="team-responsibilities">
                  <div className="team-section-label">
                    <div className="team-section-dot"></div>
                    RESPONSIBILITIES
                  </div>
                  <p className="team-responsibilities-text">
                    {member.responsibilities}
                  </p>
                </div>

                {/* Skills */}
                <div className="team-skills">
                  <div className="team-section-label">
                    <div className="team-section-dot"></div>
                    SKILLS
                  </div>
                  <div className="team-skills-tags">
                    {member.skills.map((skill, index) => (
                      <span key={index} className="team-skill-tag">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Workload */}
                <div className="team-workload">
                  <div className="team-workload-header">
                    <span className="team-workload-label">WORKLOAD</span>
                    <span className="team-workload-value">
                      {member.current_workload} / {member.max_workload}
                    </span>
                  </div>
                  <div className="team-workload-bar">
                    <div
                      className={`team-workload-fill team-workload-${workloadStatus}`}
                      style={{ width: `${Math.min(workloadPercentage, 100)}%` }}
                    ></div>
                  </div>
                  <div className="team-workload-status">
                    <span
                      className={`team-workload-badge team-workload-badge-${workloadStatus}`}
                    >
                      {workloadStatus === "critical"
                        ? "AT CAPACITY"
                        : workloadStatus === "warning"
                        ? "BUSY"
                        : "AVAILABLE"}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default TeamDirectory;
