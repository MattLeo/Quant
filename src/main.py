from basicAnalysis import BasicTradingAnalysis
from backend.data_access import TradingDAO
from backend.init_db import init_database
from trading_manager import TradingManager
import os
from datetime import datetime
import pandas as pd
import json
import glob

print("Imports successful")

def setup_folders(results_folder):
    project_root = os.path.dirname(os.path.dirname(__file__))
    print(f"Setting up folders for: {results_folder}")
    os.makedirs(project_root + results_folder + "/batches", exist_ok=True)
    os.makedirs(project_root + results_folder + "/summaries", exist_ok=True)
    print("Folders created successfully")
    return True

def load_config():
    print("Loading config...")
    project_root = os.path.dirname(os.path.dirname(__file__))
    config_path = f"{project_root}/config.json"
    
    if not os.path.exists(config_path):
        raise ValueError("Config file not found. Check if 'config.json' exists.")
    
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
        api_key = config['alpaca']['api_key']
        secret_key = config['alpaca']['secret']
        results_folder = config['settings']['results_folder']
        universe_type = config['settings']['universe_type']
    
    print("Config loaded successfully")
    return api_key, secret_key, results_folder, universe_type

def save_results(results, recommendations, results_folder):
    print("Saving results...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_root = os.path.dirname(os.path.dirname(__file__))
    
    # Text Summary
    txt_filename = f"{project_root}/{results_folder}/summaries/{timestamp}_summary.txt"
    with open(txt_filename, 'w') as f:
        f.write("Basic Trading Analysis Results\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Stocks Analyzed: {len(results)}\n\n")
        f.write("Universe Type: Filtered\n\n")
        
        f.write("BUY RECOMMENDATIONS:\n")
        for stock in recommendations['buy_list']:
            f.write(f"{stock['symbol']}: ${stock['current_price']:.2f} ")
            f.write(f"(Signal: {stock['adjusted_signal']:.3f})\n")
        
        f.write("\nSELL RECOMMENDATIONS:\n")
        for stock in recommendations['sell_list']:
            f.write(f"{stock['symbol']}: ${stock['current_price']:.2f} ")
            f.write(f"(Signal: {stock['adjusted_signal']:.3f})\n")
        
        f.write("\nHOLD RECOMMENDATIONS:\n")
        for stock in recommendations['hold_list']:
            f.write(f"{stock['symbol']}: ${stock['current_price']:.2f} ")
            f.write(f"(Signal: {stock['adjusted_signal']:.3f})\n")
    
    # CSV Summary
    csv_filename = f"{project_root}/{results_folder}/summaries/{timestamp}_summary.csv"
    df_data = []
    for result in results:
        df_data.append({
            'symbol': result['symbol'],
            'price': result['current_price'],
            'signal': result['adjusted_signal'],
            'confidence': result['confidence'],
            'recommendation': result['recommendation'],
            'risk_score': result['risk_metrics']['risk_score'],
            'volatility': result['risk_metrics']['volatility'],
            'sma_signal': result['signals']['sma']['value'],
            'rsi_signal': result['signals']['rsi']['value'],
            'volume_signal': result['signals']['volume']['value']
        })
    
    df = pd.DataFrame(df_data)
    df.to_csv(csv_filename, index=False)
    
    print(f"Analysis complete. Results saved:")
    print(f"  Text: {timestamp}_summary.txt")
    print(f"  CSV:  {timestamp}_summary.csv")

def cleanup_batch_files(results_folder):
    project_root = os.path.dirname(os.path.dirname(__file__))
    batches_folder = f"{project_root}/{results_folder}/batches"

    if not os.path.exists(batches_folder):
        return
    
    batch_files = glob.glob(os.path.join(batches_folder, "batch_*"))

    if batch_files:
        print("Cleaning up batch files...")
        for file in batch_files:
            try:
                os.remove(file)
            except OSError as e:
                print(f"Error deleting {file}: {e}")
        print("Batch files cleaned up successfully")

if __name__ == "__main__":
    PAPER_TRADING = True
    AUTO_EXECUTE = True

    try:
        # Setup phase
        init_database()
        api_key, secret_key, results_folder, universe_type = load_config()
        ##setup_folders(results_folder)  # Probably no longer necessary

        # Intitialization phase
        framework = BasicTradingAnalysis(api_key, secret_key)
        dao = TradingDAO()
        trading_manager = TradingManager(
            dao,
            framework,
            api_key=api_key,
            secret_key=secret_key,
            paper_trading=PAPER_TRADING,
            auto_execute=AUTO_EXECUTE
        )

        print(f"Execution engine created: {trading_manager.execution_engine is not None}")
        print(f"Auto execute enabled: {trading_manager.auto_execute}")

        if trading_manager.execution_engine:
            account_info = trading_manager.execution_engine.get_account_info()
            if account_info:
                print(f"Account connected - Buying power: ${account_info['buying_power']}")
            else:
                print("Account connection failed")

        # Run analysis
        analysis_results = trading_manager.run_full_analysis(universe_type=universe_type, execute_trades=AUTO_EXECUTE)
        recommendations = analysis_results['new_opportunities']['recommendations']
        results = analysis_results['new_opportunities']['analysis_results']

        print("=" * 50)
        print("⚡ TRADES EXCUTED")
        print("=" * 50)
        executed_trades = analysis_results.get('executed_trades', {})
        if executed_trades.get('buys'):
            print(f"Executed {len(executed_trades['buys'])} buy orders")
        else:
            print(f"No buy orders made")
        if executed_trades.get('sells'):
            print(f"Executed {len(executed_trades['sells'])} sell orders")
        else:
            print(f"No sell orders made")

        # Saving analysis findings
        print("\n" + "=" * 50)
        print("💾 SAVING RESULTS")
        print("=" * 50)
        save_results(results, recommendations, results_folder)
        cleanup_batch_files(results_folder)

        # Show summary
        portfolio_summary = trading_manager.get_portfolio_summary()
        print("\n" + "=" * 50)
        print("📋 FINAL SUMMARY")
        print("=" * 50)
        print(f"📈 Active Positions: {portfolio_summary.get('total_positions', 0)}")
        if 'total_unrealized_pnl' in portfolio_summary:
            pnl = portfolio_summary['total_unrealized_pnl']
            print(f"💵 Total Unrealized PnL: ${pnl:.2f}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()