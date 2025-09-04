import React from 'react';

function TradeHistory({ history}) {
  return (
    <div style={{ padding: '20px', border: '1px solid #ddd', margin: '10px' }}>
      <h3>Trade History</h3>
      {history?.length > 0 ? (
        <div style={{ maxHeight: '500px', overflowY: 'auto'}}>
          {history.map((trade) => {
            const dateObj = new Date(trade.trade_date); // use trade, not history
            const localDate = dateObj.toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
            });
            const localTime = dateObj.toLocaleTimeString('en-US', {
              hour: '2-digit',
              minute: '2-digit',
              hour12: true,
            });

            return (
              <div
                key={trade.id}
                style={{ borderBottom: '1px solid #eee', padding: '10px 0'}}
              >
                <strong>
                  {localDate} - {localTime}
                </strong>
                <br />
                <strong>{trade.symbol}</strong> - {trade.action === 'BUY' ? 'Purchased' : 'Sold'}
                <br />
                Quantity: {trade.quantity} ( Price: ${trade.price?.toFixed(2)} )
                <br />
                Reason: {trade.reason === 'STOP_LOSS' ? 'Stop Loss' 
                    : trade.reason === 'NEW_POSITION' ? 'New Position'
                    : trade.reason === 'SIGNAL_CHANGE' ? 'Signal Change'
                    : trade.reason === 'TAKE_PROFIT' ? 'Take Profit'
                    : trade.reason === 'TRAILING_STOP_LOSS' ? 'Trailing Stop Loss'
                    : trade.reason === 'MANUAL' ? 'Manual'
                    : trade.reason}
              </div>
            );
          })}
        </div>
      ) : (
        <p>No trade history found.</p>
      )}
    </div>
  );
}

export default TradeHistory;
