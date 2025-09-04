import React, { useEffect, useState, useRef } from 'react';
import { Card, CardContent, Button, FormControl, Select, MenuItem, FormControlLabel, Switch } from '@mui/material';
import axios from 'axios';

function AnalysisControls({ onRunAnalysis, loading }) {
    const [universeType, setUniverseType] = useState('filtered');
    const [executeTrades, setExecuteTrades] = useState(true);
    const [logs, setLogs] = useState([]);
    const logRef = useRef(null);
    const [autoScroll, setAutoScroll] = useState(true);

    useEffect(() => {
        let interval;
        if (loading) {
            interval = setInterval(async () => {
                try {
                    const response = await axios.get('http://localhost:8282/api/logs');
                    setLogs(response.data.logs.split('\n'));
                } catch (error) {
                    console.error('Error fetching logs:', error);
                }
            }, 1000);
        } else {
            axios.post('http://localhost:8282/api/logs/clear')
                .catch(err => console.error('Error clearing logs:', err));
        }
        return () => clearInterval(interval);
    }, [loading]);

    useEffect(() => {
        const el = logRef.current;
        if (!el) return;
        
        if (autoScroll) {
            el.scrollTop = el.scrollHeight;
        }
    }, [logs, autoScroll]);

    const handleScroll = () => {
        const el = logRef.current;
        if (!el) return;
        const isAtBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 5;
        setAutoScroll(isAtBottom);
    };

    const handleRunAnalysis = () => {
        onRunAnalysis(universeType, executeTrades);
    };

    return (
        <Card>
            <CardContent>
                <h3>Run Analysis</h3>
                
                <FormControl fullWidth sx={{ mb: 2 }}>
                    <Select
                        value={universeType}
                        onChange={(e) => setUniverseType(e.target.value)}
                    >
                        <MenuItem value="starter">Starter Stocks</MenuItem>
                        <MenuItem value="filtered">Filtered Universe</MenuItem>
                        <MenuItem value="all">All Stocks</MenuItem>
                    </Select>
                </FormControl>

                <FormControlLabel
                    control={
                        <Switch
                            checked={executeTrades}
                            onChange={(e) => setExecuteTrades(e.target.checked)}
                        />
                    }
                    label="Execute Trades Automatically"
                />

                <Button 
                    variant="contained" 
                    onClick={handleRunAnalysis}
                    disabled={loading}
                    fullWidth
                    sx={{ mt: 2 }}
                >
                    {loading ? 'Running Analysis...' : 'Run Analysis'}
                </Button>
                <div
                    ref = {logRef}
                    onScroll = {handleScroll}
                    style={{
                        marginTop: '16px',
                        height: '200px',
                        backgroundColor: '#f5f5f5',
                        border: '1px solid #ccc',
                        padding: '8px',
                        overflowY: 'auto',
                        fontFamily: 'monospace',
                        fontSize: '0.85rem'
                    }}
                >
                    {logs.map((line, index) => (
                        <div key={index}>{line}</div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}

export default AnalysisControls;