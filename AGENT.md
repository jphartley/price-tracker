# AGENT.md - Price Tracker Development Guide

## Build/Test/Lint Commands
- Setup: `python setup.py` (installs all deps for both frontend/backend)
- Backend: `cd backend && source venv/bin/activate && python main.py` (or `./start-backend.sh`)
- Frontend: `cd frontend && npm run dev` (or `./start-frontend.sh`)
- Frontend lint: `cd frontend && npm run lint`
- Frontend build: `cd frontend && npm run build`
- Backend deps: `cd backend && pip install -r requirements.txt && playwright install`
- No test framework configured - create tests using pytest for backend, vitest for frontend

## Architecture
- **Backend**: FastAPI + SQLite database, port 8000, main endpoints: GET/POST /products, POST /products/{id}/check-price
- **Frontend**: React + Vite + Tailwind CSS, port 5173, single-page app in App.jsx
- **Database**: SQLite with Product and PriceHistory tables using SQLAlchemy ORM
- **Scraping**: Playwright-based scraper for Paul Smith website in scraper.py
- **CORS**: Backend allows localhost:5173, configured in main.py

## Code Style
- **Backend**: Python with FastAPI patterns, SQLAlchemy models, async/await, snake_case naming
- **Frontend**: JSX with React hooks, camelCase, Tailwind utility classes, ES6 modules
- **Database**: SQLAlchemy declarative base, DateTime fields use datetime.utcnow
- **API**: RESTful endpoints with Pydantic models, HTTPException for errors
- **Imports**: Absolute imports, group by stdlib/third-party/local
- **Error handling**: try/catch with appropriate HTTP status codes
