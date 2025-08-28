from basicAnalysis import BasicTradingAnalysis
from backend.data_access import TradingDAO
from backend.init_db import init_database
import os
from datetime import datetime
import pandas as pd
import json
import glob

print("Imports successful")

def setup_folders(results_folder):
    print(f"Setting up folders for: {results_folder}")
    os.makedirs("../" + results_folder + "/batches", exist_ok=True)
    os.makedirs("../" + results_folder + "/summaries", exist_ok=True)
    print("Folders created successfully")
    return True

def load_config():
    print("Loading config...")
    config_path = "../config.json"
    
    if not os.path.exists(config_path):
        raise ValueError("Config file not found. Check if 'config.json' exists.")
    
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
        api_key = config['alpaca']['api_key']
        secret_key = config['alpaca']['secret']
        results_folder = config['settings']['results_folder']
    
    print("Config loaded successfully")
    return api_key, secret_key, results_folder

def save_results(results, recommendations, results_folder):
    print("Saving results...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Text Summary
    txt_filename = f"../{results_folder}/summaries/{timestamp}_summary.txt"
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
    csv_filename = f"../{results_folder}/summaries/{timestamp}_summary.csv"
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
    batches_folder = f"../{results_folder}/batches"

    if not os.path.exsist(batches_folder):
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
    try:
        init_database()
        api_key, secret_key, results_folder = load_config()
        setup_folders(results_folder)
        framework = BasicTradingAnalysis(api_key, secret_key)
        results = framework.run_analysis(universe_type='filtered', results_folder=results_folder)
        recommendations = framework.generate_recommendations(results)
        dao = TradingDAO()
        dao.save_analysis_resilts(results)
        save_results(results, recommendations, results_folder)
        cleanup_batch_files(results_folder)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()