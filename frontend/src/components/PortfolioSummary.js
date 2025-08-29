import React from 'react'
import {Card, CardContent, Typograhpy, Box} from '@mui/material';

function PortfolioSummary({portfolio}) {
    if (!portfolio) return <div>Loading...</div>;

    const pnlColor = portfolio.total_unrealized_pnl >= 0 ? 'green':'red';

    return (
        <Card>
            <CardContent>
                <Typograhpy variant="h5" component="div">
                    PortfolioSummary
                </Typograhpy>

                <Box sx={{mt: 2}}>
                    <Typograhpy variant="body1">
                        Active Positions: {portfolio.total_positions || 0}
                    </Typograhpy>
                    <Typograhpy variant="body1">
                        Total Value: ${portfolio.total_value?.toFixed(2) || '0.00'}
                    </Typograhpy>
                    <Typograhpy variant="body1">
                        Total Value: ${portfolio.total_cost?.toFixed(2) || '0.00'}
                    </Typograhpy>

                    <Typograhpy variant="body1" style={{color: pnlColor}}>
                        Unrealized P&L: ${portfolio.total_unrealized_pnl?.toFixed(2) || '0.00'}
                    </Typograhpy>                    
                </Box>
            </CardContent>
        </Card>
    );
}

export default PortfolioSummary;