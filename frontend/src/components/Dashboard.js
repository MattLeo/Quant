import React, {useState, useEffect} from 'react';
import axios from 'axios';
import PortfolioSummary from './PortfolioSummary';
import PositionsList from './PositionsList';
import AnalysisControls from './AnalysisControls';
import RecommendationsList from './RecommendationsList'

const API_BASE = 'http://localhost:8282/api';

function Dashboard() {
    const [porfolio, setPortfolio] = useState(null);
    const [positions, setPositions] = useState([]);
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchPortfolio();
        fetchPositions();
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
        try {
            const response = await axios.post(`${API_BASE}/analysis/run`, {
                universe_type: universeType,
                execute_trades: executeTrades
            });

            setRecommendations(response.data.new_opportunities.recommendations);
            //Refresh portfolio after running analysis
            await fetchPortfolio();
            await fetchPositions();
        } catch (error) {
            console.error('Error running analysis:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className='dashboard'>
            <h1>Aglorithmic Trading Dashboard</h1>

            <div className='dashboard-grid'>
                <PortfolioSummary portfolio={porfolio} />
                <PositionsList positions={positions} />
                <AnalysisControls onRunAnalysis={runAnalysis} />
                <RecommendationsList recommendations={recommendations} />
            </div>
        </div>
    );
}

export default Dashboard;