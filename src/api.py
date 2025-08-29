from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

from backend.data_access import TradingDAO
from backend.init_db import init_database
from trading_manager import TradingManager
from basicAnalysis import BasicTradingAnalysis

app = Flask(__name__)
CORS(app)

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

init_database()
dao = TradingDAO()
api_key, secret_key, results_folder, universe_type = load_config()
framework = BasicTradingAnalysis(api_key, secret_key)
trading_manager = TradingManager(api_key, secret_key, dao)

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get current portfolio summary"""
    try:
        summary = trading_manager.get_portfolio_summary()
        return jsonify(summary)
    except Exception as e:
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

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get trade history"""
    # Needs to create this function in DAO
    pass

if __name__ == '__main__':
    app.run(debug=True, port=8282)

