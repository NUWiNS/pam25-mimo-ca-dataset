import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import logging
import pickle
import matplotlib
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

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

def plot_cdf_tput(all_operator_tput_stats, link_direction='DL', band_type='mmWave', tput_modes=['Tput_0'], integrity_suffix="", enable_inset=False, inset_xmin=0, inset_xmax=None):
    try:
        if band_type == 'mmWave': target_operators = ['ATT', 'Verizon']
        elif band_type in ('Low', 'Mid'): target_operators = ['ATT', 'TMobile', 'Verizon']
        else: target_operators = ['ATT', 'TMobile', 'Verizon']
        
        for operator in target_operators:
            filtered_tput_modes = tput_modes
            
            fig, ax = plt.subplots(figsize=(8, 7))
            
            color_map = {
                'Tput_0': 'red',
                'Tput_1': 'green', 
                'Tput_2': 'blue',
                'Tput_3': 'black'
            }
            
            valid_modes = []
            mode_to_curve = {}
            mode_to_handle = {}
            mode_to_label = {}
            
            for tput_mode in filtered_tput_modes:
                operator_tput_stats = all_operator_tput_stats.get(tput_mode, {})
                ca_data = operator_tput_stats.get(operator, {})
                
                if not ca_data or 'All' not in ca_data or len(ca_data['All']) == 0:
                    continue
                
                tput_values = ca_data['All']
                sorted_values = np.sort(tput_values)
                n = len(sorted_values)
                y = np.arange(1, n + 1) / n
                
                mode_display_names = {
                    'Tput_0': r'T$_{BASE}$',
                    'Tput_1': r'T$_{CA}$',
                    'Tput_2': r'T$_{MIMO}$',
                    'Tput_3': r'T$_{TOTAL}$'
                }
                
                display_name = mode_display_names.get(tput_mode, tput_mode)
                mode_to_label[tput_mode] = display_name
                color = color_map.get(tput_mode, 'gray')
                
                line, = ax.plot(sorted_values, y, label=f'{display_name}', color=color, linewidth=6, alpha=0.8)
                
                valid_modes.append(tput_mode)
                mode_to_curve[tput_mode] = (sorted_values, y, color)
                mode_to_handle[tput_mode] = line
            
            if not valid_modes:
                plt.close()
                continue
            
            ax.set_xlabel(f'Throughput (Mbps)')
            ax.set_ylabel('CDF')
            ax.grid(True, alpha=0.3)
            
            if band_type == 'mmWave': ax.set_xlim(0, 3000)
            elif band_type in ('Low', 'Mid'): ax.set_xlim(0, 1000)
            else: ax.set_xlim(left=0)

            desired_order = ['Tput_0', 'Tput_2', 'Tput_1', 'Tput_3']
            ordered_modes = [m for m in desired_order if m in valid_modes]
            ordered_handles = [mode_to_handle[m] for m in ordered_modes]
            ordered_labels = [mode_to_label[m] for m in ordered_modes]
            ax.legend(ordered_handles, ordered_labels, loc='lower right')
            ax.set_ylim(0, 1)

            if enable_inset:
                if inset_xmax is None:
                    if band_type == 'mmWave': inset_xmax_effective = 750
                    elif band_type == 'Mid': inset_xmax_effective = 500
                    elif band_type == 'Low': inset_xmax_effective = 200
                    else: inset_xmax_effective = 750
                else:
                    inset_xmax_effective = inset_xmax

                axins = inset_axes(ax, width="45%", height="45%", loc='lower left', borderpad=1)
                for mode in valid_modes:
                    sorted_values, y_values, color = mode_to_curve[mode]
                    axins.plot(sorted_values, y_values, color=color, linewidth=4, alpha=0.8)
                axins.set_xlim(inset_xmin, inset_xmax_effective)
                axins.set_ylim(0, 1)
                axins.grid(True, alpha=0.3)
                axins.tick_params(labelsize=8)
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            plots_dir = os.path.join(current_dir, '..', 'plots')
            os.makedirs(plots_dir, exist_ok=True)
            
            filename = f'cdf_tput_{band_type}_{operator}_{link_direction.lower()}'
            plt.savefig(os.path.join(plots_dir, f'{filename}{integrity_suffix}.pdf'), dpi=300, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Saved plot: {filename}{integrity_suffix}.pdf")
        
    except Exception as e:
        logger.error(f"An error occurred during plotting: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    integrity_suffix = "_with_integrity"
    modes_to_process = ['Tput_0', 'Tput_1', 'Tput_2', 'Tput_3']
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pkl_dir = os.path.join(current_dir, '..', 'pkl')
    
    pkl_filename = os.path.join(pkl_dir, 'cdf_tput_dl.pkl')
    if not os.path.exists(pkl_filename):
        logger.warning(f"Pickle file not found: {pkl_filename}")
        return
        
    with open(pkl_filename, 'rb') as f:
        pkl_data = pickle.load(f)
        
    all_operator_tput_stats_low = pkl_data['Low']
    all_operator_tput_stats_mid = pkl_data['Mid']
    all_operator_tput_stats_mmwave = pkl_data['mmWave']
    
    if all_operator_tput_stats_low:
        plot_cdf_tput(all_operator_tput_stats_low, 'DL', 'Low', modes_to_process, integrity_suffix)
    if all_operator_tput_stats_mid:
        plot_cdf_tput(all_operator_tput_stats_mid, 'DL', 'Mid', modes_to_process, integrity_suffix)
    if all_operator_tput_stats_mmwave:
        plot_cdf_tput(all_operator_tput_stats_mmwave, 'DL', 'mmWave', modes_to_process, integrity_suffix)

    logger.info("Plotting completed.")

if __name__ == "__main__":
    main()

