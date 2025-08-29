import React, {useState} from 'react';
import {
    Card, 
    CardContent, 
    Button, 
    FormControl, 
    InputLabel, 
    Select, 
    MenuItem, 
    FormControlLabel, 
    Switch,
    Menu
} from '@mui/material'


function AnalysisControls({onRunAnalysis, loading}) {
    const [universeType, setUniverseType] = useState('filtered');
    const [executeTrades, setExecuteTrades] = useState(false);

    const handleRunAnalysis = () => {
        onRunAnalysis(universeType, executeTrades);
    };

    return (
        <Card>
            <CardContent>
                <h3>Run Analysis</h3>

                <FormControl fullWidth sx={{mb: 2}}>
                    <InputLabel>Universe Type</InputLabel>
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
                    variant='contained'
                    onClick={handleRunAnalysis}
                    disabled={loading}
                >
                    {loading ? 'Running Analysis...' : 'Run Analysis'}
                </Button>
            </CardContent>
        </Card>
    );
}

export default AnalysisControls;