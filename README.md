# AI Task Assignment System

An intelligent task assignment system that uses RAG (Retrieval-Augmented Generation) and LangGraph to automatically assign tasks to the best-suited team members based on their skills, roles, and current workload.

## 🚀 Features

- **AI-Powered Assignment**: Uses GPT-4 and LangGraph to analyze tasks and match them with team members
- **RAG Integration**: Retrieves relevant team member information from documents
- **Confidence-Based Auto-Assignment**: Automatically assigns high-confidence matches, sends low-confidence tasks for human review
- **Email Notifications**: Sends assignment notifications to team members
- **Real-time Dashboard**: React-based frontend for task management
- **Workload Management**: Tracks and balances team member workloads

## 📋 Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (or use Docker)
- OpenAI API Key

## 🛠️ Backend Setup

### 1. Start PostgreSQL Database

```bash
# Using Docker Compose
docker-compose up -d

# Or install PostgreSQL locally
```

### 2. Set Up Python Environment

```bash
cd backend

# Activate the virtual environment
.\internalrag\Scripts\activate  # Windows
# source internalrag/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit .env and add your configuration:
# - DATABASE_URL
# - OPENAI_API_KEY
# - SMTP credentials
```

### 4. Initialize Database

```bash
# Seed the database with sample team members
python seed.py
```

### 5. Run the Backend

```bash
# Development mode
uvicorn app.main:app --reload

# The API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## 🎨 Frontend Setup

### 1. Initialize Vite React Project

```bash
cd frontend

# Create Vite project (if not already created)
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install axios @tanstack/react-query lucide-react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 2. Configure Tailwind CSS

Update `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

Add to `src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 3. Run the Frontend

```bash
npm run dev

# The app will be available at http://localhost:5173
```

## 📖 API Endpoints

### Tasks

- `POST /api/tasks/` - Create a new task (AI will attempt assignment)
- `GET /api/tasks/` - Get all tasks (with optional status filter)
- `GET /api/tasks/{id}` - Get specific task
- `POST /api/tasks/{task_id}/assign/{member_id}` - Manually assign task
- `PUT /api/tasks/{task_id}/status/{status}` - Update task status
- `DELETE /api/tasks/{id}` - Delete task

### Team Members

- `POST /api/team/` - Create team member
- `GET /api/team/` - Get all team members
- `GET /api/team/{id}` - Get specific team member
- `PUT /api/team/{id}` - Update team member
- `DELETE /api/team/{id}` - Deactivate team member
- `GET /api/team/{id}/tasks` - Get member's tasks

### Chat

- `POST /api/chat/` - Send message to AI assistant

## 🧪 Testing the System

### 1. Create a Task

```bash
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"description": "Create a FastAPI backend for user authentication with JWT tokens"}'
```

### 2. Check Assignment

```bash
curl http://localhost:8000/api/tasks/
```

### 3. Manual Review (if needed)

```bash
# Get tasks needing review
curl "http://localhost:8000/api/tasks/?status=manual_review"

# Manually assign
curl -X POST http://localhost:8000/api/tasks/1/assign/1
```

## 📊 How It Works

### 1. Task Submission

User describes a task through the chat interface or API.

### 2. AI Analysis (LangGraph Workflow)

```
Fetch RAG Context → Extract Requirements → Score Members → Select Best Match
```

- **Fetch Context**: Retrieves relevant team member info from vector store
- **Extract Requirements**: Uses GPT-4 to identify required skills
- **Score Members**: Calculates match score based on skills and workload
- **Select Match**: Chooses best candidate and generates reasoning

### 3. Auto-Assignment Decision

- **High Confidence (≥75%)**: Auto-assign + send email
- **Low Confidence (<75%)**: Send for manual review

### 4. Notification

Assigned team member receives email with task details.

## 🔧 Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://taskuser:taskpass@localhost:5432/task_assignment

# OpenAI
OPENAI_API_KEY=sk-...

# Email (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# AI Settings
CONFIDENCE_THRESHOLD=0.75  # 75% confidence required for auto-assignment

# Frontend
FRONTEND_URL=http://localhost:5173
```

### Adjusting Confidence Threshold

Lower threshold = More auto-assignments (but potentially less accurate)
Higher threshold = More manual reviews (but higher accuracy)

## 📁 Project Structure

```
internal-rag/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── tasks.py
│   │   │       ├── team.py
│   │   │       └── chat.py
│   │   ├── models/
│   │   │   ├── team_member.py
│   │   │   ├── task.py
│   │   │   └── assignment.py
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── rag_service.py
│   │   │   ├── langgraph_service.py
│   │   │   └── email_service.py
│   │   ├── database/
│   │   ├── config.py
│   │   └── main.py
│   ├── documents/
│   │   ├── team_roles.txt
│   │   └── expertise_guide.txt
│   ├── requirements.txt
│   ├── seed.py
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── types/
│   │   └── App.tsx
│   └── package.json
└── docker-compose.yml
```

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker ps

# Restart database
docker-compose restart postgres
```

### RAG Not Working

```bash
# Make sure documents exist
ls backend/documents/

# Check if documents were loaded (in logs)
# Look for: "Loaded X document chunks into vector store"
```

### Email Not Sending

- Verify SMTP credentials in `.env`
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)
- Check firewall/network settings

## 📝 License

MIT

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a PR.
