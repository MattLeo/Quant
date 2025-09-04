import React from 'react';

function PositionsList ({ positions }) {
    return (
        <div style={{ padding: '20px' , border: '1px solid #ddd', margin: '10px'}}>
            <h3> Active Positions ({positions?.length || 0})</h3>
            {positions?.length > 0 ? (
                <div style={{maxHeight: '500px', overflowY: 'auto'}}>
                    {positions.map((position) => (
                        <div key={position.id} style={{ borderBottom: '1px solid #eee', padding: '10px 0' }}>
                            <strong>{position.symbol}</strong> - {position.quantity} shares
                            <br />
                            Entry: ${position.entry_price?.toFixed(2)}
                            {position.current_stop_loss && (
                                <span> | Stop Loss: ${position.current_stop_loss.toFixed(2)}</span>
                            )}
                        </div>
                    ))}
                </div>
            ) : (
                <p>No active positions.</p>
            )}
        </div>
    );
}

export default PositionsList;