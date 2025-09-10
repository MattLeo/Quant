# Algorithmic Trading Dashboard - Frontend

A React-based frontend application for an algorithmic trading system that provides real-time portfolio monitoring, trade analysis, and automated trading recommendations.

## Features

- **📊 Portfolio Dashboard** - Real-time portfolio summary with current value, daily P&L, and performance metrics
- **📈 Position Monitoring** - Live tracking of all open positions with current prices and unrealized gains/losses
- **🤖 Trading Recommendations** - buy/sell/hold signals with confidence scores
- **📋 Trade History** - Complete transaction history with detailed trade information
- **⚙️ Analysis Controls** - Manual trigger for trading algorithm analysis with execution options
- **📱 Responsive Design** - Mobile-friendly interface built with Material-UI

## Technology Stack

- **Frontend Framework**: React 19.1.1
- **UI Library**: Material-UI (MUI) v7.3.1
- **Styling**: Emotion CSS-in-JS
- **HTTP Client**: Axios 1.11.0
- **Charts**: Recharts 3.1.2
- **Testing**: Jest, React Testing Library
- **Build Tool**: Create React App

## Getting Started

### Prerequisites

- Node.js 14+ 
- npm or yarn
- Backend API running on port 8282

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

4. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner in interactive watch mode
- `npm run build` - Builds the app for production to the `build` folder
- `npm run eject` - **Note: this is a one-way operation!**

## Project Structure

```
frontend/
├── public/
│   ├── index.html          # Main HTML template
│   └── favicon.ico         # App icon
├── src/
│   ├── components/         # React components
│   │   ├── Dashboard.js    # Main dashboard container
│   │   ├── PortfolioSummary.js
│   │   ├── PositionsList.js
│   │   ├── TradeHistory.js
│   │   ├── RecommendationsList.js
│   │   └── AnalysisControls.js
│   ├── App.js             # Main App component
│   ├── App.css            # Application styles
│   └── index.js           # Entry point
├── package.json           # Dependencies and scripts
└── README.md
```

## API Integration

The frontend communicates with a Flask backend API running on `http://localhost:8282/api`. Key endpoints include:

- `GET /api/portfolio` - Fetch portfolio summary
- `GET /api/positions` - Get current positions
- `GET /api/trades` - Retrieve trade history
- `GET /api/analysis/results` - Get latest recommendations
- `POST /api/analysis/run` - Trigger analysis execution

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
REACT_APP_API_URL=http://localhost:8282/api
```

### Backend Requirements

Ensure the backend trading API is running with:
- Flask server on port 8282
- CORS enabled for localhost:3000
- Alpaca Markets API integration
- SQLAlchemy database setup

## Component Overview

### Dashboard
Main container component that orchestrates all dashboard widgets and manages global state.

### PortfolioSummary
Displays key portfolio metrics including:
- Total portfolio value
- Daily profit/loss
- Cash balance
- Buying power

### PositionsList
Shows all current stock positions with:
- Symbol and quantity
- Current market price
- Unrealized P&L
- Position value

### RecommendationsList
Displays algorithmic trading signals:
- **🟢 Buy Signals** - Stocks recommended for purchase
- **🔴 Sell Signals** - Positions recommended for sale
- **⚪ Hold/Neutral** - Stocks with neutral signals

### TradeHistory
Complete transaction log showing:
- Trade timestamp
- Symbol and action (buy/sell)
- Quantity and execution price
- Trade rationale

### AnalysisControls
Interface for triggering analysis runs with options for:
- Universe type selection (filtered/full)
- Execute trades toggle
- Manual analysis initiation

## Styling and Theming

The application uses Material-UI's theming system with a custom theme:

- **Primary Color**: Blue (#1976d2)
- **Secondary Color**: Pink (#dc004e)
- **Success Color**: Green (#2e7d32)
- **Error Color**: Red (#d32f2f)

Responsive grid layout adapts to different screen sizes with mobile-first design principles.

## Testing

Run the test suite:

```bash
npm test
```

Testing stack includes:
- Jest for unit testing
- React Testing Library for component testing
- DOM testing utilities

## Building for Production

Create an optimized production build:

```bash
npm run build
```

This builds the app for production in the `build` folder, with optimized React bundles and minified files ready for deployment.

## Development Notes

- **API Base URL**: Currently hardcoded to `http://localhost:8282/api`
- **Error Handling**: Console error logging for API failures
- **State Management**: React hooks (useState, useEffect)
- **Real-time Updates**: Manual refresh triggers for live data

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Related Documentation

- [Create React App Documentation](https://facebook.github.io/create-react-app/docs/getting-started)
- [React Documentation](https://reactjs.org/)
- [Material-UI Documentation](https://mui.com/)
- [Recharts Documentation](https://recharts.org/)

---

**Note**: This frontend requires the corresponding Python Flask backend to be running for full functionality. Ensure all API endpoints are accessible before running the application.