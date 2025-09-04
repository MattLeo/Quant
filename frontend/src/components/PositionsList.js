import React, {useState, useEffect} from 'react';

function PositionsList ({ positions }) {
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(10);

    useEffect(() => {
        setCurrentPage(1);
    }, [positions]);

    const totalItems = positions?.length || 0;
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const currentPositions = positions?.slice(startIndex, endIndex) || [];

    const handlePageChange = (newPage) => {
        if (newPage >= 1 && newPage <= totalPages) {
            setCurrentPage(newPage); 
        }
    };

    const handleItemsPerPageChange = (event) => {
        const newItemsPerPage = parseInt(event.target.value);
        setItemsPerPage(newItemsPerPage);
        setCurrentPage(1);
    };

    const getPageNumbers = () => {
        const pages = [];
        const maxVisiblePages = 5;

        let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            pages.push(i);
        }

        return pages;
    }

    return (
        <div style={{ padding: '20px' , border: '1px solid #ddd', margin: '10px'}}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style= {{margin: '0'}}> Active Positions ({positions?.length || 0})</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <label htmlFor="itemsPerPage" style={{ fontSize: '0.9em', color: '#666'}}>Show:</label>
                        <select
                            id="itemsPerPage"
                            value={itemsPerPage}
                            onChange={handleItemsPerPageChange}
                            style={{
                                padding: '4px 8px',
                                border: '1px solid #ccc',
                                borderRadius: '4px',
                                fontSize: '0.9em'
                            }}
                        >
                            <option value={5}>5</option>
                            <option value={10}>10</option>
                            <option value={15}>15</option>
                            <option value={20}>20</option>
                            <option value={25}>25</option>
                            <option value={50}>50</option>
                            <option value={100}>100</option>
                        </select>
                        <span style={{fontSize: '0.9em', color: '#666'}}>per page</span>
                    </div>
                    {totalPages > 1 && (
                        <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                            <button
                                onClick={() => handlePageChange(currentPage - 1)}
                                disabled={currentPage === 1}
                                style={{
                                    padding: '4px 8px',
                                    border: '1px solid #ccc',
                                    backgroundColor: currentPage === 1 ? '#f5f5f5' : 'white',
                                    borderRadius: '4px',
                                    fontSize: '0.85em',
                                    cursor: currentPage === 1 ? 'not-allowed' : 'pointer'
                                }}
                            >←</button>
                            {getPageNumbers().map(pageNum => (
                                <button
                                    key={pageNum}
                                    onClick={() => handlePageChange(pageNum)}
                                    style={{
                                        padding: '4px 8px',
                                        border: '1px solid #ccc',
                                        backgroundColor: pageNum === currentPage ? '#1976d2' : 'white',
                                        color: pageNum === currentPage ? 'white' : 'black',
                                        borderRadius: '4px',
                                        fontSize: '0.85em',
                                        cursor: 'pointer'
                                    }}
                                >{pageNum}</button>
                            ))}
                            <button
                                onClick={() => handlePageChange(currentPage + 1)}
                                disabled={currentPage === totalPages}
                                style={{
                                    padding: '4px 8px',
                                    border: '1px solid #ccc',
                                    backgroundColor: currentPage === totalPages ? '#f5f5f5' : 'white',
                                    borderRadius: '4px',
                                    fontSize: '0.85em',
                                    cursor: currentPage === totalPages ? 'not-allowed' : 'pointer'
                                }}
                            >→</button>
                        </div>
                    )}
                </div>
            </div>
            {totalPages > 0 && (
                <div style={{fontSize:'0.85em', color:'#666', marginBottom:'12px'}}>
                    Showing {startIndex + 1}-{Math.min(endIndex, totalItems)} of {totalItems} positions
                </div>
            )}
            {currentPositions?.length > 0 ? (
                <div style={{maxHeight: '600px', overflowY: 'auto', border: '1px solid #ccc'}}>
                    {currentPositions.map((position) => (
                        <div key={position.id} style={{ borderBottom: '1px solid #eee', padding: '10px 5px' }}>
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