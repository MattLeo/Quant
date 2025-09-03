import React, {useState, useEffect} from 'react';
import axios from 'axios';
import PortfolioSummary from './PortfolioSummary';
import PositionsList from './PositionsList';
import AnalysisControls from './AnalysisControls';
import RecommendationsList from './RecommendationsList'
import TradeHistory from './TradeHistory';
import { useRef } from 'react';

const API_BASE = 'http://localhost:8282/api';

function Dashboard() {
    const [portfolio, setPortfolio] = useState(null);
    const [positions, setPositions] = useState([]);
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [history, setHistory] = useState([]);

    useEffect(() => {
        fetchPortfolio();
        fetchPositions();
        fetchHistory();
    }, []);
    

    const fetchPortfolio = async () => {
        try {
            const response = await axios.get(`${API_BASE}/portfolio`);
            setPortfolio(response.data);
        } catch (error) {
            console.error('Error fetching portfolio:', error);
        }
    }

    const fetchPositions = async () => {
        try {
            const response = await axios.get(`${API_BASE}/positions`);
            setPositions(response.data);
        } catch (error) {
            console.error('Error fetching positions:', error);
        }
    }

    const runAnalysis = async (universeType, executeTrades) => {
        setLoading(true);
        try {
            const response = await axios.post(`${API_BASE}/analysis/run`, {
                universe_type: universeType,
                execute_trades: executeTrades
            });

            setRecommendations(response.data.new_opportunities.recommendations);
            // Refresh portfolio after running analysis
            await fetchPortfolio();
            await fetchPositions();
            await fetchHistory();
        } catch (error) {
            console.error('Error running analysis:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchHistory = async () => {
        try{
            const response = await axios.get(`${API_BASE}/trades`);
            setHistory(response.data);
        } catch (error) {
            console.error('Error fetching trade history:', error);
        }
    };

    return (
        <div className='dashboard'>
            <h1>Trading Dashboard</h1>

            <div className='dashboard-grid'>
                <PortfolioSummary portfolio={portfolio} />
                <PositionsList positions={positions} />
                <TradeHistory history={history} />
                <RecommendationsList recommendations={recommendations} />
                <AnalysisControls onRunAnalysis={runAnalysis} loading={loading} />
            </div>
        </div>
    );
}

export default Dashboard;