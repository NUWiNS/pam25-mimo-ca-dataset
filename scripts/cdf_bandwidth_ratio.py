import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import logging
import pickle
import matplotlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    style_path = os.path.join(current_dir, 'matplotlibrc')
    if os.path.exists(style_path):
        matplotlib.rc_file(style_path)
    else:
        plt.style.use('default')
        logger.warning(f"matplotlibrc not found at {style_path}, using default style")
except Exception as e:
    logger.warning(f"Could not load matplotlibrc: {e}")

def plot_cdf_bandwidth_ratio(all_operator_ratio_stats, link_direction='DL', band_type='mmWave', integrity_suffix=""):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plots_dir = os.path.join(current_dir, '..', 'plots')
        os.makedirs(plots_dir, exist_ok=True)
        
        if band_type == 'mmWave': target_operators = ['ATT', 'Verizon']
        else: target_operators = ['ATT', 'TMobile', 'Verizon']
        
        for operator in target_operators:
            fig, ax = plt.subplots(figsize=(8, 7))
            color = 'black'
            valid_data = False
            
            ca_data = all_operator_ratio_stats.get(operator, {})
            
            if not ca_data or 'All' not in ca_data or len(ca_data['All']) == 0:
                plt.close()
                continue
            
            ratio_values = ca_data['All']
            sorted_values = np.sort(ratio_values)
            n = len(sorted_values)
            y = np.arange(1, n + 1) / n
            
            display_name = 'Total BW / PCell BW'
            ax.plot(sorted_values, y, label=f'{display_name}', color=color, linewidth=6, alpha=0.8)
            
            valid_data = True
            
            if not valid_data:
                plt.close()
                continue
            
            ax.set_xlabel('Bandwidth Ratio')
            ax.set_ylabel('CDF')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 1)
            
            if band_type == 'Low': ax.set_xlim(0, 15)
            elif band_type == 'Mid':
                if operator == 'TMobile': ax.set_xlim(0, 15)
                else: ax.set_xlim(0, 3.9)
            elif band_type == 'mmWave': ax.set_xlim(0, 8.3)
            else: ax.set_xlim(left=0)
            
            filename = f'cdf_bandwidth_ratio_{band_type}_{operator}_{link_direction.lower()}'
            plt.savefig(os.path.join(plots_dir, f'{filename}{integrity_suffix}.pdf'), dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"Saved plot: {filename}{integrity_suffix}.pdf")
            
    except Exception as e:
        logger.error(f"An error occurred during plotting: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    integrity_suffix = "_with_integrity"
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pkl_dir = os.path.join(current_dir, '..', 'pkl')
    
    pkl_filename = os.path.join(pkl_dir, 'cdf_bandwidth_ratio_dl.pkl')
    if not os.path.exists(pkl_filename):
        logger.warning(f"Pickle file not found: {pkl_filename}")
        return
        
    with open(pkl_filename, 'rb') as f:
        pkl_data = pickle.load(f)
        
    all_operator_ratio_stats_low = pkl_data['Low']
    all_operator_ratio_stats_mid = pkl_data['Mid']
    all_operator_ratio_stats_mmwave = pkl_data['mmWave']
    
    if all_operator_ratio_stats_low:
        plot_cdf_bandwidth_ratio(all_operator_ratio_stats_low, 'DL', 'Low', integrity_suffix)
    if all_operator_ratio_stats_mid:
        plot_cdf_bandwidth_ratio(all_operator_ratio_stats_mid, 'DL', 'Mid', integrity_suffix)
    if all_operator_ratio_stats_mmwave:
        plot_cdf_bandwidth_ratio(all_operator_ratio_stats_mmwave, 'DL', 'mmWave', integrity_suffix)

    logger.info("Plotting completed.")

if __name__ == "__main__":
    main()

