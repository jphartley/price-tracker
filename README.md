# Paul Smith Price Tracker

A web application to track product prices on Paul Smith's website and get notified when prices drop.

## Features

- Add Paul Smith product URLs to track
- Check current prices with a "Check Now" button
- View price history for tracked products
- Clean, responsive UI built with React and Tailwind CSS
- FastAPI backend with SQLite database

## Tech Stack

**Frontend:**
- React with Vite
- Tailwind CSS
- JavaScript

**Backend:**
- FastAPI
- SQLite database
- Playwright for web scraping
- Python

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Quick Setup (Recommended)

1. Clone or download the project
2. Navigate to the project root directory
3. Run the setup script:
   ```bash
   python setup.py
   ```

This will automatically set up both backend and frontend dependencies, including installing Playwright browsers.

### Manual Setup

#### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```bash
   playwright install
   ```

#### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

### Running the Application

#### Option 1: Using convenience scripts (from project root)
```bash
# Terminal 1 - Start backend
./start-backend.sh

# Terminal 2 - Start frontend  
./start-frontend.sh
```

#### Option 2: Manual startup
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

- Backend API: `http://localhost:8000`
- Frontend App: `http://localhost:5173`
- API Documentation: `http://localhost:8000/docs`

## Usage

1. Open your browser and go to `http://localhost:5173`
2. Paste a Paul Smith product URL in the input field
3. Click "Add Product" to start tracking
4. Use the "Check Price" button to manually check for price updates
5. View tracked products and their current prices in the list below

## API Endpoints

- `GET /products` - Get all tracked products
- `POST /products` - Add a new product to track
- `POST /products/{id}/check-price` - Check current price for a product
- `GET /products/{id}/history` - Get price history for a product

## Project Structure

```
price-tracker/
├── backend/
│   ├── main.py          # FastAPI application
│   ├── scraper.py       # Web scraping logic
│   └── requirements.txt # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx      # Main React component
│   │   ├── main.jsx     # React entry point
│   │   └── index.css    # Tailwind CSS
│   ├── package.json     # Node.js dependencies
│   └── vite.config.js   # Vite configuration
└── README.md
```

## Future Enhancements

- Automated price checking with scheduled jobs
- Email notifications for price drops
- Support for additional fashion websites
- User authentication and personal dashboards
- Price drop alerts and thresholds
- Export price history data