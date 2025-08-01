"""
Demo application for pyfxgit ChartCls functionality with TCGPlayer time series data
This demonstrates how to use the plotChart function with actual time series data.
"""
import sys
import os

# Add parent directory to path to import pyfxgit  
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common.helpers import ChartDataProcessor

def demo_chart_factory(csv_file: str, title: str, save_name: str) -> bool:
    """One-liner demo chart generation factory"""
    try:
        df = ChartDataProcessor.load_and_convert_time_series(csv_file)
        chart_file = ChartDataProcessor.create_chart_with_indicators(df, title, save_name)
        print(f"✅ Generated {chart_file} with {len(df)} records")
        return True
    except Exception as e:
        print(f"❌ Failed to generate {save_name}: {e}")
        return False

def demo_plot_chart():
    """Single-card demo using factory pattern"""
    print("=== TCGPlayer Single Cards Chart Demo ===")
    return demo_chart_factory("data/single_time_series.csv", "Single Cards", "TCG_TimeSeries")

def demo_sealed_data():
    """Sealed products demo using factory pattern"""
    print("\n=== TCGPlayer Sealed Products Chart Demo ===")
    return demo_chart_factory("data/sealed_time_series.csv", "Sealed Products", "TCG_Sealed")

if __name__ == "__main__":
    """One-liner demo execution with comprehensive error handling"""
    try:
        results = [demo_plot_chart(), demo_sealed_data()]
        success_msg = "✅ Demo completed successfully!" if all(results) else "⚠️ Some demos failed"
        charts = ["TCG_TimeSeries", "TCG_Sealed"]
        chart_list = "\n".join([f"  - '_ChartC_0.1_{name}.png'" for i, name in enumerate(charts) if results[i]])
        print(f"\n{success_msg}\nGenerated charts:\n{chart_list}" if chart_list else "\n❌ No charts generated")
    except Exception as e:
        print(f"❌ Critical error: {e}\nEnsure: 1) Run from app directory 2) pyfxgit installed 3) Data files exist")