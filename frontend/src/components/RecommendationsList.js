import React from 'react';

function RecommendationsList({ recommendations }) {
    if (!recommendations) {
        return (
            <div style={{ padding: '20px', border: '1px solid #ddd', margin: '10px' }}>
                <h3>Recommendations</h3>
                <p>Run analysis to see recommendations</p>
            </div>
        );
    }

    return (
        <div style={{ padding: '20px', border: '1px solid #ddd', margin: '10px' }}>
            <h3>Latest Recommendations</h3>
            
            {recommendations.buy_list?.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ color: 'green' }}>🟢 Buy Signals ({recommendations.buy_list.length})</h4>
                    {recommendations.buy_list.slice(0, 5).map((stock, index) => (
                        <div key={index} style={{ marginBottom: '10px', padding: '8px', backgroundColor: '#f0f8f0', border: '1px solid #d4e6d4', borderRadius: '4px' }}>
                            <div style={{ fontWeight: 'bold' }}>
                                {stock.symbol} - ${stock.current_price?.toFixed(2)}
                            </div>
                            <div style={{ fontSize: '0.9em', color: '#666' }}>
                                Signal: {stock.adjusted_signal?.toFixed(3)} | Confidence: {stock.confidence?.toFixed(2)}
                            </div>
                            <div style={{ fontSize: '0.8em', color: '#888' }}>
                                Risk Score: {stock.risk_metrics?.risk_score?.toFixed(2)} | Volatility: {stock.risk_metrics?.volatility?.toFixed(2)}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {recommendations.sell_list?.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ color: 'red' }}>🔴 Sell Signals ({recommendations.sell_list.length})</h4>
                    {recommendations.sell_list.slice(0, 5).map((stock, index) => (
                        <div key={index} style={{ marginBottom: '10px', padding: '8px', backgroundColor: '#fdf2f2', border: '1px solid #f5c6c6', borderRadius: '4px' }}>
                            <div style={{ fontWeight: 'bold' }}>
                                {stock.symbol} - ${stock.current_price?.toFixed(2)}
                            </div>
                            <div style={{ fontSize: '0.9em', color: '#666' }}>
                                Signal: {stock.adjusted_signal?.toFixed(3)} | Confidence: {stock.confidence?.toFixed(2)}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {recommendations.hold_list?.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ color: '#666' }}>⚪ Hold/Neutral Signals ({recommendations.hold_list.length})</h4>
                    <div style={{ fontSize: '0.9em', color: '#666', marginBottom: '10px' }}>
                        Showing top 5 by signal strength
                    </div>
                    {recommendations.hold_list
                        .sort((a, b) => b.adjusted_signal - a.adjusted_signal) // Sort by signal strength
                        .slice(0, 5)
                        .map((stock, index) => (
                        <div key={index} style={{ marginBottom: '8px', padding: '6px', backgroundColor: '#f9f9f9', border: '1px solid #e0e0e0', borderRadius: '4px' }}>
                            <div style={{ fontWeight: 'bold' }}>
                                {stock.symbol} - ${stock.current_price?.toFixed(2)}
                            </div>
                            <div style={{ fontSize: '0.85em', color: '#666' }}>
                                Signal: {stock.adjusted_signal?.toFixed(3)} | Confidence: {stock.confidence?.toFixed(2)}
                            </div>
                            <div style={{ fontSize: '0.8em', color: '#888' }}>
                                SMA: {stock.signals?.sma?.value?.toFixed(2)} | RSI: {stock.signals?.rsi?.value?.toFixed(2)} | Vol: {stock.signals?.volume?.value?.toFixed(2)}
                            </div>
                        </div>
                    ))}
                    
                    {recommendations.hold_list.length > 5 && (
                        <div style={{ fontSize: '0.8em', color: '#888', marginTop: '10px' }}>
                            ... and {recommendations.hold_list.length - 5} more hold recommendations
                        </div>
                    )}
                </div>
            )}

            {recommendations.buy_list?.length === 0 && recommendations.sell_list?.length === 0 && (
                <div style={{ padding: '15px', backgroundColor: '#fff3cd', border: '1px solid #ffeaa7', borderRadius: '4px', color: '#856404' }}>
                    <strong>No strong buy/sell signals detected.</strong> Current market conditions suggest a neutral/hold stance for most analyzed stocks.
                </div>
            )}
        </div>
    );
}

export default RecommendationsList;