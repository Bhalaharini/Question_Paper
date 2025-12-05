# SIH25210 - Mining Comminution Optimization System

Full-stack application for mining equipment monitoring and optimization with AI-powered insights.

## Architecture

- **Backend**: FastAPI (Python 3.13+) with Motor (async MongoDB)
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Database**: MongoDB Atlas
- **Deployment**: Railway (backend) + Vercel (frontend)

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- MongoDB Atlas account

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (edit .env file)
cp .env.example .env
# Edit .env and set your MONGODB_URL, JWT_SECRET, etc.

# Seed database with sample data (optional)
python app/seed.py

# Run backend
python -m uvicorn app.main:app --reload --port 8000
```

Backend will be available at **http://localhost:8000**

API docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (optional - defaults to http://localhost:8000/api)
echo "VITE_BACKEND_URL=http://localhost:8000/api" > .env

# Run frontend
npm run dev
```

Frontend will be available at **http://localhost:5173**

### Test Credentials (after seeding)

- **Admin**: username: `admin` / password: `admin123`
- **Operator**: username: `operator1` / password: `operator123`
- **Engineer**: username: `engineer1` / password: `engineer123`

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   └── seed.py          # Database seeding script
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment variables (create from .env.example)
│   └── README_FASTAPI.md    # Backend-specific docs
│
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API client
│   │   ├── contexts/        # React contexts
│   │   └── types/           # TypeScript types
│   ├── package.json         # Node dependencies
│   └── vite.config.ts       # Vite configuration
│
├── railway.json             # Railway deployment config
└── vercel.json              # Vercel deployment config
```

## API Endpoints

### Public
- `GET /health` - Health check
- `GET /api/db/status` - Database status
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration

### Protected (requires Bearer token)
- `GET /api/machines/{machineId}/data` - Machine data history
- `GET /api/machines/{machineId}/status` - Current machine status
- `POST /api/machines/{machineId}/control` - Control machine
- `GET /api/analytics/overview` - System overview
- `GET /api/analytics/trends` - Trending data
- `GET /api/analytics/breakdown` - Utilization breakdown
- `GET /api/analytics/alerts` - Active alerts
- `GET /api/users/logs` - User activity logs
- `POST /api/gemini/voice` - Voice command processing
- `POST /api/gemini/chat` - AI chat assistant

## Environment Variables

### Backend (.env)
```
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/dbname
JWT_SECRET=your-secret-key-change-this
CORS_ORIGIN=http://localhost:5173
GEMINI_API_KEY=your-gemini-api-key
MONGODB_DB=sih
```

### Frontend (.env)
```
VITE_BACKEND_URL=http://localhost:8000/api
```

## Deployment

### Railway (Backend)

1. Connect your GitHub repository
2. Set environment variables in Railway dashboard:
   - `MONGODB_URL`
   - `JWT_SECRET`
   - `CORS_ORIGIN` (your Vercel frontend URL)
   - `GEMINI_API_KEY`
3. Deploy from `updated` branch

Railway will use `railway.json` config to start the FastAPI server.

### Vercel (Frontend)

1. Connect your GitHub repository
2. Set build settings:
   - Framework: Vite
   - Root Directory: `frontend`
3. Set environment variable:
   - `VITE_BACKEND_URL` = your Railway backend URL + `/api`
4. Deploy from `updated` branch

## Development

### Backend Tasks

```bash
# Run backend
cd backend && source .venv/bin/activate && python -m uvicorn app.main:app --reload --port 8000

# Seed database
cd backend && source .venv/bin/activate && python app/seed.py

# Check dependencies
pip list
```

### Frontend Tasks

```bash
# Run frontend
cd frontend && npm run dev

# Build for production
cd frontend && npm run build

# Preview production build
cd frontend && npm run preview

# Lint
cd frontend && npm run lint
```

## Features

- 🔐 JWT-based authentication
- 📊 Real-time machine monitoring
- 📈 Analytics and trends
- 🤖 AI-powered chat assistant
- 🎤 Voice control integration
- ⚡ Real-time alerts
- 📱 Responsive design
- 🔄 Digital Twin simulation

## Tech Stack

**Backend:**
- FastAPI - Modern async web framework
- Motor - Async MongoDB driver
- Pydantic - Data validation
- JWT - Authentication
- Bcrypt - Password hashing
- Google Generative AI - AI features

**Frontend:**
- React 18 - UI framework
- TypeScript - Type safety
- Vite - Build tool
- Tailwind CSS - Styling
- React Router - Navigation

## Support

For issues or questions, please open an issue on GitHub.

## License

MIT
