

# 🛰️ DisasterAI - Multimodal Geospatial Intelligence

> AI-powered multimodal analysis for disaster response, infrastructure monitoring, and comprehensive geospatial intelligence synthesis. Real-time monitoring for all types of disasters including earthquakes, floods, wildfires, hurricanes, tsunamis, volcanic eruptions, droughts, landslides, cyclones, and more.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev)
[![Gemini](https://img.shields.io/badge/Gemini-2.0-4285F4.svg)](https://ai.google.dev)

---

## ✨ Features

- **🔍 Multimodal Document Analysis** - Analyze satellite imagery, PDFs, and technical reports
- **🗺️ Geospatial Mapping** - Automatic coordinate extraction and polygon visualization
- **🤖 AI-Powered Insights** - Google Gemini integration for intelligent summarization
- **📊 NER Entity Extraction** - Identify locations, organizations, and risk indicators
- **🔄 Background Processing** - Async task queue for large document processing
- **🌐 REST API** - Full-featured FastAPI backend with OpenAPI documentation

---

## 🏗️ Architecture

```
disasterai/
├── 📁 backend/                 # Python FastAPI Backend
│   ├── main.py                 # FastAPI app & endpoints
│   ├── models.py               # Pydantic data models
│   ├── tasks.py                # Background task processing
│   ├── config.py               # Configuration management
│   ├── services/               # Business logic services
│   │   ├── gemini_service.py   # Gemini AI integration
│   │   ├── geocoding_service.py # Location resolution
│   │   └── ner_service.py      # Named Entity Recognition
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Environment template
├── 📁 components/              # React UI Components
├── App.tsx                     # Main React application
├── types.ts                    # TypeScript type definitions
└── package.json                # Node.js dependencies
```

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend)
- **Gemini API Key** ([Get one here](https://ai.google.dev))

### Frontend Setup

```bash
# Install dependencies
npm install

# Set your Gemini API key in .env.local
# GEMINI_API_KEY=your_key_here

# Run the frontend
npm run dev
```

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your GEMINI_API_KEY

# Run the backend server
python run.py

# OR use uvicorn directly:
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📡 API Endpoints

Once the backend is running, visit **http://localhost:8000/docs** for interactive API documentation.

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API info |
| `GET` | `/health` | Health check & service status |
| `GET` | `/api/health-detailed` | Detailed health check with service verifications |
| `GET` | `/api/metrics/system` | System resource metrics |
| `GET` | `/api/metrics/tasks` | Task-related metrics |
| `GET` | `/api/metrics/performance` | Comprehensive performance metrics |
| `POST` | `/api/analyze` | Synchronous document analysis |
| `POST` | `/api/analyze/async` | Async analysis (returns task ID) |
| `POST` | `/api/analyze/upload` | Upload & analyze file |
| `GET` | `/api/tasks/{id}` | Get task status & results |
| `POST` | `/api/geocode` | Geocode location name |
| `POST` | `/api/ner` | Extract named entities |

### Disaster Monitoring Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/disasters/types` | Get all supported disaster types |
| `GET` | `/api/disasters/active` | Get currently active disasters |
| `GET` | `/api/disasters/historical` | Get historical disasters |
| `GET` | `/api/disasters/location/{location}` | Get disaster timeline for a location |
| `GET` | `/api/disasters/stats` | Get disaster statistics and summaries |
| `POST` | `/api/disasters/subscribe` | Subscribe to alerts for an area |
| `POST` | `/api/disasters/unsubscribe` | Unsubscribe from alerts for an area |

### Alerting Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/alerts/active` | Get active alerts |
| `GET` | `/api/alerts/sent` | Get sent alerts |
| `GET` | `/api/alerts/{alert_id}` | Get status of specific alert |
| `POST` | `/api/alerts/{alert_id}/acknowledge` | Acknowledge receipt of an alert |
| `GET` | `/api/alerts/channels` | Get available alert channels |
| `GET` | `/api/alerts/priorities` | Get available alert priorities |
| `GET` | `/api/alerts/stats` | Get alert statistics |

### Real-time Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `WS` | `/api/ws` | WebSocket for real-time disaster monitoring |

### Example: Analyze Document

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "document_data": "BASE64_ENCODED_IMAGE",
    "mime_type": "image/png",
    "analysis_mode": "comprehensive"
  }'
```

### Example: Extract Entities

```bash
curl -X POST "http://localhost:8000/api/ner" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Critical infrastructure damage reported in Chennai Terminal. LogiCorp dispatching emergency response team to Bangalore Hub."
  }'
```

---

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `GEMINI_MODEL` | Model to use | `gemini-2.0-flash` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Enable debug mode | `false` |
| `CORS_ORIGINS` | Allowed origins | `localhost:5173,3000` |
| `MAX_FILE_SIZE_MB` | Max upload size | `50` |
| `CACHE_ENABLED` | Enable response caching | `true` |
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./disasterai.db` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `TASK_TIMEOUT` | Task processing timeout (seconds) | `300` |

---

## 🔮 Technology Stack

### Backend
- **FastAPI** - High-performance async API framework
- **Pydantic** - Data validation & settings management
- **Google GenAI** - Gemini multimodal AI
- **GeoPy** - Geocoding with Nominatim
- **Tenacity** - Retry logic for resilience

### Backend Enhancements
- **Persistent Task Storage** - Database-backed task management with SQLAlchemy
- **Comprehensive Logging** - Structured logging with JSON format and request tracing
- **Enhanced Error Handling** - Detailed error reporting and graceful fallbacks
- **Performance Monitoring** - Real-time metrics for system resources and task processing
- **Health Checks** - Detailed service availability verification
- **Security & Validation** - Enhanced input validation and secure coding practices

### Real-time Disaster Monitoring
- **Multi-Hazard Detection** - AI-powered detection of earthquakes, floods, wildfires, hurricanes, tsunamis, volcanic eruptions, droughts, landslides, and more
- **Real-time Alerts** - Multi-channel alerting system (email, SMS, push notifications, webhooks)
- **WebSocket Integration** - Live streaming of disaster events and alerts
- **Subscription System** - Area-based alert subscriptions for targeted notifications
- **Historical Tracking** - Comprehensive database of past disaster events
- **Risk Assessment** - Multi-tiered alert levels (Green, Yellow, Orange, Red, Black)

### Frontend
- **React 19** - Modern UI framework
- **Vite** - Next-gen build tool
- **Framer Motion** - Fluid animations
- **Leaflet** - Interactive maps
- **Lucide** - Beautiful icons

---

## 📦 Project Status

| Component | Status |
|-----------|--------|
| Frontend UI | ✅ Complete |
| Backend API | ✅ Complete |
| Gemini Integration | ✅ Complete |
| Geocoding Service | ✅ Complete |
| NER Service | ✅ Complete |
| Task Queue | ✅ Complete |
| Database Persistence | ✅ Complete |
| Logging & Monitoring | ✅ Complete |
| Real-time Disaster Monitoring | ✅ Complete |
| Multi-Hazard Detection | ✅ Complete |
| Alerting System | ✅ Complete |
| WebSocket Integration | ✅ Complete |
| Production Deploy | 🔄 Planned |

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

[MIT](LICENSE)

---

<div align="center">
  <strong>Built with 💙 using AI-powered geospatial analysis</strong>
</div>
