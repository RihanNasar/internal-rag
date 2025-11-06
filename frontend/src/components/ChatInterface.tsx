import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2 } from "lucide-react";
import type { ChatMessage } from "../types";
import { taskAPI } from "../services/api";
import "./ChatInterface.css";

const STORAGE_KEY = "taskai_chat_history";

const getInitialMessages = (): ChatMessage[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      // Convert timestamp strings back to Date objects
      return parsed.map((msg: any) => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
      }));
    }
  } catch (error) {
    console.error("Error loading chat history:", error);
  }

  // Default welcome message
  return [
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hi! I'm your AI task assignment assistant. Describe a task and I'll find the best team member to handle it.",
      timestamp: new Date(),
    },
  ];
};

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>(getInitialMessages);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch (error) {
      console.error("Error saving chat history:", error);
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Create task
      const task = await taskAPI.createTask(input);

      let content = "";
      if (task.status === "auto_assigned") {
        // Fetch team member details if assigned
        let assignedMemberName = `Team Member #${task.assigned_to}`;
        if (task.assigned_to) {
          try {
            const response = await fetch(
              `https://internal-rag-backend.onrender.com/${task.assigned_to}`
            );
            if (response.ok) {
              const member = await response.json();
              assignedMemberName = `${member.name} (${member.role})`;
            }
          } catch (err) {
            console.error("Error fetching team member:", err);
          }
        }

        content =
          `✅ Task created and automatically assigned!\n\n` +
          `📊 Confidence Score: ${(task.confidence_score! * 100).toFixed(
            1
          )}%\n` +
          `👤 Assigned to: ${assignedMemberName}\n\n` +
          `The team member has been notified via email.`;
      } else if (task.status === "manual_review") {
        content =
          `⚠️ Task created but needs manual review.\n\n` +
          `📊 Confidence Score: ${(task.confidence_score! * 100).toFixed(
            1
          )}%\n` +
          `This is below the confidence threshold (75%).\n\n` +
          `Please go to the Review tab to manually assign this task.`;
      } else {
        content =
          `✓ Task created successfully and is pending assignment.\n\n` +
          `Task ID: ${task.id}`;
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content,
        timestamp: new Date(),
        taskId: task.id,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error("Error creating task:", error);

      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `❌ Sorry, there was an error processing your request:\n\n${
          error.response?.data?.detail || error.message || "Unknown error"
        }`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    if (e.key === "Escape") {
      setInput("");
    }
  };

  const handleClearHistory = () => {
    if (window.confirm("Clear all chat history? This cannot be undone.")) {
      const welcomeMessage: ChatMessage = {
        id: "welcome-" + Date.now(),
        role: "assistant",
        content:
          "Hi! I'm your AI task assignment assistant. Describe a task and I'll find the best team member to handle it.",
        timestamp: new Date(),
      };
      setMessages([welcomeMessage]);
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  return (
    <div className="chat-container">
      {/* Retro Terminal Chat */}
      <div className="chat-terminal">
        {/* Terminal Header */}
        <div className="chat-header">
          <div className="chat-header-left">
            <div className="terminal-dots">
              <span className="dot dot-red"></span>
              <span className="dot dot-yellow"></span>
              <span className="dot dot-green"></span>
            </div>
            <div className="chat-avatar-bot">
              <Bot className="icon-bot" />
            </div>
            <div className="chat-title-group">
              <h2 className="chat-title">AI TASK TERMINAL</h2>
              <p className="chat-subtitle">SYSTEM v2.0.25 // READY FOR INPUT</p>
            </div>
          </div>
          <div className="terminal-status">
            <button
              className="chat-clear-button"
              onClick={handleClearHistory}
              title="Clear chat history"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
            <span className="status-indicator"></span>
            <span className="status-text">ONLINE</span>
          </div>
        </div>

        {/* Messages Area */}
        <div className="chat-messages">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message-wrapper ${
                message.role === "user" ? "message-user" : "message-assistant"
              }`}
            >
              {/* Avatar */}
              <div
                className={`message-avatar ${
                  message.role === "user" ? "avatar-user" : "avatar-bot"
                }`}
              >
                {message.role === "assistant" ? (
                  <Bot className="avatar-icon" />
                ) : (
                  <User className="avatar-icon" />
                )}
              </div>

              {/* Message Bubble */}
              <div className="message-content-wrapper">
                <div
                  className={`message-bubble ${
                    message.role === "user" ? "bubble-user" : "bubble-bot"
                  }`}
                >
                  <p className="message-text">{message.content}</p>
                  <div className="message-time">
                    {message.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* Loading */}
          {isLoading && (
            <div className="message-wrapper message-assistant">
              <div className="message-avatar avatar-bot">
                <Loader2 className="avatar-icon loading-spin" />
              </div>
              <div className="message-content-wrapper">
                <div className="message-bubble bubble-bot">
                  <div className="loading-dots">
                    <span className="loading-dot"></span>
                    <span className="loading-dot"></span>
                    <span className="loading-dot"></span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="chat-input-container">
          <div className="chat-input-wrapper">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="ENTER TASK DESCRIPTION..."
              className="chat-input"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="chat-send-button"
            >
              {isLoading ? (
                <Loader2 className="send-icon loading-spin" />
              ) : (
                <Send className="send-icon" />
              )}
            </button>
          </div>
          <p className="chat-hint">
            <kbd className="kbd-key">ENTER</kbd> TO TRANSMIT //{" "}
            <kbd className="kbd-key">ESC</kbd> TO CLEAR
          </p>
        </div>
      </div>
    </div>
  );
};
