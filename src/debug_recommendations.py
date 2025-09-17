#!/usr/bin/env python3
"""
Debug script to view the 10 most recent recommendation snapshots
"""

import sys
import os
import json
from datetime import datetime
from backend.database import db_manager
from backend.models import RecommendationsSnapshot
from sqlalchemy import desc

# Add the src directory to the path so we can import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def format_recommendation_data(recs, title, max_display=5):
    """Format and display recommendation data"""
    if not recs:
        print(f"    No {title.lower()} recommendations")
        return
    
    print(f"    {title} ({len(recs)} total):")
    
    # Sort by signal strength if available
    if recs and 'adjusted_signal' in recs[0]:
        recs_sorted = sorted(recs, key=lambda x: x.get('adjusted_signal', 0), reverse=True)
    else:
        recs_sorted = recs
    
    for i, rec in enumerate(recs_sorted[:max_display]):
        symbol = rec.get('symbol', 'N/A')
        price = rec.get('current_price', 0)
        signal = rec.get('adjusted_signal', 0)
        confidence = rec.get('confidence', 0)
        
        print(f"      {i+1}. {symbol:6s} | ${price:7.2f} | Signal: {signal:6.3f} | Conf: {confidence:5.2f}")
    
    if len(recs) > max_display:
        print(f"      ... and {len(recs) - max_display} more")

def get_recent_recommendations(limit=10):
    """Get the most recent recommendation snapshots"""
    session = db_manager.get_session()
    try:
        # Query for the most recent snapshots
        snapshots = session.query(RecommendationsSnapshot)\
            .order_by(desc(RecommendationsSnapshot.analysis_date))\
            .limit(limit)\
            .all()
        
        return snapshots
    finally:
        db_manager.close_session(session)

def main():
    print("=" * 80)
    print("RECENT RECOMMENDATIONS DEBUG VIEW")
    print("=" * 80)
    
    try:
        snapshots = get_recent_recommendations(10)
        
        if not snapshots:
            print("No recommendation snapshots found in database.")
            return
        
        print(f"Found {len(snapshots)} recent snapshots:\n")
        
        for i, snapshot in enumerate(snapshots, 1):
            print(f"[{i}] Analysis Date: {snapshot.analysis_date}")
            print(f"    Snapshot ID: {snapshot.id}")
            
            # Parse JSON data
            try:
                buy_recs = json.loads(snapshot.buy_recommendations) if snapshot.buy_recommendations else []
                sell_recs = json.loads(snapshot.sell_recommendations) if snapshot.sell_recommendations else []
                hold_recs = json.loads(snapshot.hold_recommendations) if snapshot.hold_recommendations else []
                
                # Display recommendations
                format_recommendation_data(buy_recs, "🟢 BUY SIGNALS")
                format_recommendation_data(sell_recs, "🔴 SELL SIGNALS") 
                format_recommendation_data(hold_recs, "⚪ HOLD SIGNALS")
                
                total_recs = len(buy_recs) + len(sell_recs) + len(hold_recs)
                print(f"    Total recommendations: {total_recs}")
                
            except json.JSONDecodeError as e:
                print(f"    Error parsing JSON data: {e}")
            except Exception as e:
                print(f"    Error processing snapshot: {e}")
            
            print("-" * 80)
        
        # Summary statistics
        print("\nSUMMARY:")
        if snapshots:
            latest = snapshots[0]
            try:
                buy_count = len(json.loads(latest.buy_recommendations)) if latest.buy_recommendations else 0
                sell_count = len(json.loads(latest.sell_recommendations)) if latest.sell_recommendations else 0
                hold_count = len(json.loads(latest.hold_recommendations)) if latest.hold_recommendations else 0
                
                print(f"Latest analysis: {latest.analysis_date}")
                print(f"Buy signals: {buy_count}, Sell signals: {sell_count}, Hold signals: {hold_count}")
            except:
                print("Could not parse latest snapshot data")
        
    except Exception as e:
        print(f"Error accessing database: {e}")
        print("Make sure your database file exists and is accessible.")

if __name__ == "__main__":
    main()