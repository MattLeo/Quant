from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
import traceback
import logging
from logging.handlers import MemoryHandler
from io import StringIO
from datetime import datetime

from backend.data_access import TradingDAO
from backend.init_db import init_database
from trading_manager import TradingManager
from basicAnalysis import TradingAnalysis
import logging

app = Flask(__name__)
if os.getenv('DOCKER_ENV'):
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost",
                "http://localhost:80", 
                "http://127.0.0.1",
                "http://127.0.0.1:80",
                "http://0.0.0.0:80"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True
        }
    })
else:
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })

def load_config():

    project_root = os.path.dirname(os.path.dirname(__file__))
    config_path = f"{project_root}/config.json"

    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
        api_key = config['alpaca']['api_key']
        secret_key = config['alpaca']['secret']
        results_folder = config['settings']['results_folder']
        universe_type = config['settings']['universe_type']
    
    return api_key, secret_key, results_folder, universe_type

def init_logger():
    logger = logging.getLogger('console_log')
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        memory_buffer = StringIO()
        memory_stream_handler = logging.StreamHandler(memory_buffer)
        memory_stream_handler.setLevel(logging.INFO)
        logger.addHandler(memory_stream_handler)

        memory_handler = MemoryHandler(
            capacity=10000,
            flushLevel=logging.CRITICAL,
            target=memory_stream_handler
        )
        logger.addHandler(memory_handler)
        logger.memory_buffer = memory_buffer
        logger.memory_handler = memory_handler

    return logger

init_database()
logger = init_logger()
dao = TradingDAO()
api_key, secret_key, results_folder, universe_type = load_config()
framework = TradingAnalysis(api_key, secret_key)
trading_manager = TradingManager(
    dao,
    framework,
    api_key=api_key,
    secret_key=secret_key,
    paper_trading=True,
    auto_execute=True
)
trading_manager.sync_with_alpaca()

@app.before_request
def log_request():
    print(f"=== REQUEST: {request.method} {request.path} ===")
    print(f"Request headers: {dict(request.headers)}")

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get current portfolio summary"""
    try:
        summary = trading_manager.get_portfolio_summary()
        return jsonify(summary)
    except Exception as e:
        print(f"ERROR in /api/portfolio: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/run', methods=['POST'])
def run_analysis():
    """Run full analysis"""
    try:
        data = request.json
        universe_type = data.get('universe_type', 'filtered')
        execute_trades = data.get('execute_trades', False)
        results = trading_manager.run_full_analysis(universe_type, execute_trades)
        return jsonify(results)
    except Exception as e:
        print(f"ERROR in /api/analysis/run: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/analysis/results', methods=['GET'])
def get_analysis_results():
    """Get analysis results if date matches today"""
    today = datetime.now().date()
    try:
        results = dao.get_analysis_results()

        if results and results.analysis_date.date() == today:
            return jsonify({
                'id': results.id,
                'analysis_date': results.analysis_date,
                'recommendations': {
                    'hold_list': json.loads(results.hold_recommendations),
                    'buy_list': json.loads(results.buy_recommendations),
                    'sell_list': json.loads(results.sell_recommendations)
                }
            })
        else:
            return {}
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get active positions"""
    try:
        positions = dao.get_active_positions()
        return jsonify([{
            'id': pos.id,
            'symbol': pos.symbol,
            'quantity': pos.quantity,
            'entry_price': pos.entry_price,
            'entry_date': pos.entry_date,
            'current_stop_loss': pos.current_stop_loss,
            'is_active': pos.is_active
        } for pos in positions])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get analysis logs"""
    try:
        logger.memory_handler.flush()
        logs = logger.memory_buffer.getvalue()
        return jsonify({"logs": logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """Clear analysis logs"""
    try:
        logger.memory_buffer.truncate(0)
        logger.memory_buffer.seek(0)
        return jsonify({"message": "Logs cleared successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get trade history"""
    try:
        trades = dao.get_trade_history()
        return jsonify([{
            'id': trade.id,
            'position_id': trade.position_id,
            'symbol': trade.symbol,
            'action': trade.action,
            'quantity': trade.quantity,
            'price': trade.price,
            'trade_date': trade.trade_date,
            'reason': trade.reason
        } for trade in trades])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/sync-positions', methods=['POST'])
def sync_positions():
    """Sync positions with Alpaca"""
    try:
        api_key, secret_key, results_folder, universe_type = load_config()

        trading_manager = TradingManager(
            dao,
            framework,
            api_key=api_key,
            secret_key=secret_key,
            paper_trading=True,
            auto_execute=True
        )
        
        result = trading_manager.sync_with_alpaca()

        if result['success']:
            return jsonify({"message": "Position sycned successfully", "details": result})
        else:
            return jsonify({"error": "Failed to sync positions", "details": result}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host= '0.0.0.0', debug=False, port=8282)

