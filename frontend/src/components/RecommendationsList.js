import React from 'react';

function RecommendationsList({ recommendations }) {
    if (!recommendations) {
        return (
            <div style={{ padding: '20px', border: '1px solid #ddd', margin: '10ox'}}>
                <h3>Recommendations</h3>
                <p>Run Analysis to see recommendations</p>
            </div>
        );
    }

    return (
        <div style={{ padding: '20px', border: '1px solid #ddd', margin: '10px'}}>
            <h3>Latest Recommendations</h3>
            {recommendations.buy_list?.length > 0 && (
                <div style={{marginBottom: '15px'}}>
                    <h4 style={{color: 'green'}}>Buy Signals ({recommendations.buy_list.length})</h4>
                    {recommendations.buy_list.slice(0,5).map((stock, index) => (
                        <div key={index} style={{marginBottom: '5px'}}>
                            <strong>{stock.symbol}</strong> - ${stock.current_price?.toFixed(2)}
                            <br />
                            <small>Signal: {stock.adjusted_signal?.toFixed(3)} | Confidence {stock.confidence?.toFixed(2)}</small>
                        </div>
                    ))}
                </div>
            )}

            {recommendations.sell_list?.length > 0 && (
                <div>
                    <h4 style={{color: 'red'}}>Sell Signals ({recommendations.sell_list.length})</h4>
                    {recommendations.sell_list.slice(0, 5).map((stock, index) => (
                        <div key={index} style={{marginBottom: '5px'}}>
                            <strong>{stock.symbol}</strong> - {stock.name}
                            <br />
                            <small>Signal: {stock.adjusted_signal?.toFixed(3)} | Confidence {stock.confidence?.toFixed(2)}</small>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
export default RecommendationsList;