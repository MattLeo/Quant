import React from 'react'
import {Card, CardContent, Typography, Box} from '@mui/material';

function PortfolioSummary({portfolio}) {
    if (!portfolio) return <div>Loading...</div>;

    const pnlColor = portfolio.total_unrealized_pnl >= 0 ? 'green':'red';

    return (
        <Card>
            <CardContent>
                <Typography variant="h5" component="div">
                    Portfolio Summary
                </Typography>

                <Box sx={{mt: 2}}>
                    <Typography variant="body1">
                        Active Positions: {portfolio.total_positions || 0}
                    </Typography>
                    <Typography variant="body1">
                        Total Value: ${portfolio.total_value?.toFixed(2) || '0.00'}
                    </Typography>
                    <Typography variant="body1">
                        Total Cost: ${portfolio.total_cost?.toFixed(2) || '0.00'}
                    </Typography>

                    <Typography variant="body1" style={{color: pnlColor}}>
                        Unrealized P&L: ${portfolio.total_unrealized_pnl?.toFixed(2) || '0.00'}
                    </Typography>                    
                </Box>
            </CardContent>
        </Card>
    );
}

export default PortfolioSummary;