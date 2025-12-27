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

def plot_cdf_tput_ratio(all_operator_ratio_stats, link_direction='DL', band_type='mmWave', ratio_modes=['T_ca_T_base'], integrity_suffix=""):
    try:
        if band_type == 'mmWave': target_operators = ['ATT', 'Verizon']
        else: target_operators = ['ATT', 'TMobile', 'Verizon']
        
        for operator in target_operators:
            filtered_ratio_modes = ratio_modes
            fig, ax = plt.subplots(figsize=(8, 7))
            
            valid_modes = []
            mode_to_handle = {}
            mode_to_label = {}
            
            for ratio_mode in filtered_ratio_modes:
                operator_ratio_stats = all_operator_ratio_stats.get(ratio_mode, {})
                ca_data = operator_ratio_stats.get(operator, {})
                
                if not ca_data or 'All' not in ca_data or len(ca_data['All']) == 0:
                    continue
                
                ratio_values = ca_data['All']
                sorted_values = np.sort(ratio_values)
                n = len(sorted_values)
                y = np.arange(1, n + 1) / n
                
                ratio_display_names = {
                    'T_ca_T_base': r'T$_{CA}$/T$_{BASE}$',
                    'T_mimo_T_base': r'T$_{MIMO}$/T$_{BASE}$',
                    'T_total_T_base': r'T$_{TOTAL}$/T$_{BASE}$'
                }
                
                display_name = ratio_display_names.get(ratio_mode, ratio_mode)
                mode_to_label[ratio_mode] = display_name
                
                color_map = {
                    'T_ca_T_base': 'green', 
                    'T_mimo_T_base': 'blue',
                    'T_total_T_base': 'black'
                }
                color = color_map.get(ratio_mode, 'gray')
                
                line, = ax.plot(sorted_values, y, label=f'{display_name}', color=color, linewidth=6, alpha=0.8)
                
                valid_modes.append(ratio_mode)
                mode_to_handle[ratio_mode] = line
            
            if not valid_modes:
                plt.close()
                continue
            
            ax.set_xlim(0, 15)
            ax.set_xlabel('Throughput Ratio')
            ax.set_ylabel('CDF')
            ax.grid(True, alpha=0.3)
            
            desired_order = ['T_mimo_T_base', 'T_ca_T_base', 'T_total_T_base']
            ordered_modes = [m for m in desired_order if m in valid_modes]
            ordered_handles = [mode_to_handle[m] for m in ordered_modes]
            ordered_labels = [mode_to_label[m] for m in ordered_modes]
            ax.legend(ordered_handles, ordered_labels, loc='best')
            
            ax.set_ylim(0, 1)
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            plots_dir = os.path.join(current_dir, '..', 'plots')
            os.makedirs(plots_dir, exist_ok=True)
            
            filename = f'cdf_tput_ratio_{band_type}_{operator}_{link_direction.lower()}'
            plt.savefig(os.path.join(plots_dir, f'{filename}{integrity_suffix}.pdf'), dpi=300, bbox_inches='tight')
            plt.close()
            logger.info(f"Saved plot: {filename}{integrity_suffix}.pdf")
            
    except Exception as e:
        logger.error(f"An error occurred during plotting: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    integrity_suffix = "_with_integrity"
    ratio_modes_to_process = ['T_ca_T_base', 'T_mimo_T_base', 'T_total_T_base']
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pkl_dir = os.path.join(current_dir, '..', 'pkl')
    
    pkl_filename = os.path.join(pkl_dir, 'cdf_tput_ratio_dl.pkl')
    if not os.path.exists(pkl_filename):
        logger.warning(f"Pickle file not found: {pkl_filename}")
        return
        
    with open(pkl_filename, 'rb') as f:
        pkl_data = pickle.load(f)
        
    all_operator_ratio_stats_low = pkl_data['Low']
    all_operator_ratio_stats_mid = pkl_data['Mid']
    all_operator_ratio_stats_mmwave = pkl_data['mmWave']
    
    if all_operator_ratio_stats_low:
        plot_cdf_tput_ratio(all_operator_ratio_stats_low, 'DL', 'Low', ratio_modes_to_process, integrity_suffix)
    if all_operator_ratio_stats_mid:
        plot_cdf_tput_ratio(all_operator_ratio_stats_mid, 'DL', 'Mid', ratio_modes_to_process, integrity_suffix)
    if all_operator_ratio_stats_mmwave:
        plot_cdf_tput_ratio(all_operator_ratio_stats_mmwave, 'DL', 'mmWave', ratio_modes_to_process, integrity_suffix)

    logger.info("Plotting completed.")

if __name__ == "__main__":
    main()

