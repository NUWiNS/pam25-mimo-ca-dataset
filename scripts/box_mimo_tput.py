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

DATA_TYPE_COLUMNS = {
    'TPUT': {
        'data_col': 'Layer2 MAC DL Throughput [Mbps]',
        'ylabel': 'Throughput (Mbps)',
        'title_suffix': 'Throughput',
        'filename_prefix': 'box_mimo_tput'
    },
    'MCS': {
        'data_col': 'Layer1 DL MCS (Avg)',
        'ylabel': 'MCS',
        'title_suffix': 'MCS',
        'filename_prefix': 'box_mimo_mcs'
    },
    'RSRP': {
        'data_col': 'RF Serving SS-RSRP [dBm]',
        'ylabel': 'RSRP (dBm)',
        'title_suffix': 'RSRP',
        'filename_prefix': 'box_mimo_rsrp'
    },
    'CQI': {
        'data_col': 'RF CQI',
        'ylabel': 'CQI',
        'title_suffix': 'CQI',
        'filename_prefix': 'box_mimo_cqi'
    },
    'BANDWIDTH': {
        'data_col': 'RF BandWidth',
        'ylabel': 'Bandwidth (MHz)',
        'title_suffix': 'Bandwidth',
        'filename_prefix': 'box_mimo_bandwidth'
    }
}

def plot_box_mimo_data(all_mimo_stats, data_type='TPUT', link_direction='DL', band_type='mmWave', integrity_suffix=""):
    """
    Plot box charts for MIMO layer data across different MIMO layers
    """
    try:
        if data_type not in DATA_TYPE_COLUMNS:
            raise ValueError(f"Unsupported data type: {data_type}")
        
        data_config = DATA_TYPE_COLUMNS[data_type]
        
        if band_type == 'mmWave':
            target_operators = ['ATT', 'Verizon']
        else:
            target_operators = ['ATT', 'TMobile', 'Verizon']
        
        for operator in target_operators:
            mimo_data = all_mimo_stats.get(operator, {})
            
            if not mimo_data:
                logger.warning(f"{operator} has no {band_type} data, skipping")
                continue
            
            available_mimo_layers = []
            for mimo_layer in sorted(mimo_data.keys()):
                if len(mimo_data[mimo_layer]) > 0:
                    available_mimo_layers.append(mimo_layer)
            
            if not available_mimo_layers:
                continue
            
            fig, ax = plt.subplots(figsize=(8, 7))
            
            plot_data = []
            plot_labels = []
            plot_positions = []
            
            for i, mimo_layer in enumerate(available_mimo_layers):
                data_values = mimo_data[mimo_layer]
                if len(data_values) > 0:
                    plot_data.append(data_values)
                    plot_labels.append(f'{mimo_layer}')
                    plot_positions.append(i + 1)
            
            if plot_data:
                bp = ax.boxplot(plot_data, positions=plot_positions, labels=plot_labels,
                               patch_artist=True, showfliers=True, widths=0.5)
                
                uniform_color = 'lightblue'
                for patch in bp['boxes']:
                    patch.set_facecolor(uniform_color)
                    patch.set_alpha(0.7)
                    patch.set_linewidth(4)
                
                for median in bp['medians']:
                    median.set_color('orange')
                    median.set_linewidth(5)
                
                for whisker in bp['whiskers']:
                    whisker.set_linewidth(4)
                
                for cap in bp['caps']:
                    cap.set_linewidth(4)
                
                for flier in bp['fliers']:
                    flier.set_markeredgewidth(3)
            
            ax.set_xlabel('MIMO Layers')
            ax.set_ylabel(data_config['ylabel'])
            if data_type == 'BANDWIDTH' and band_type == 'Low':
                ax.set_ylim(0, 24)
                plt.yticks(range(0, 24, 5))
            elif data_type == 'BANDWIDTH' and band_type == 'Mid':
                ax.set_ylim(0, 109)
                plt.yticks(range(0, 109, 20))
            elif data_type == 'BANDWIDTH' and band_type == 'mmWave':
                ax.set_ylim(45, 105)
                plt.yticks(range(60, 101, 20))
            
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            plots_dir = os.path.join(current_dir, '..', 'plots')
            os.makedirs(plots_dir, exist_ok=True)
            
            filename = f'{data_config["filename_prefix"]}_{band_type}_{operator}_{link_direction.lower()}'
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
    
    data_types_to_process = ['TPUT', 'MCS', 'RSRP', 'CQI', 'BANDWIDTH']
    
    for data_type in data_types_to_process:
        logger.info(f"Plotting {data_type} data...")
        
        pkl_filename = os.path.join(pkl_dir, f'box_mimo_{data_type.lower()}_dl.pkl')
        if not os.path.exists(pkl_filename):
            logger.warning(f"Pickle file not found: {pkl_filename}")
            continue
            
        with open(pkl_filename, 'rb') as f:
            pkl_data = pickle.load(f)
            
        all_mimo_stats_low = pkl_data['Low']
        all_mimo_stats_mid = pkl_data['Mid']
        all_mimo_stats_mmwave = pkl_data['mmWave']
        
        band_stats = [
            (all_mimo_stats_low, 'Low'),
            (all_mimo_stats_mid, 'Mid'), 
            (all_mimo_stats_mmwave, 'mmWave')
        ]
        
        for stats, band_type in band_stats:
            if stats:
                plot_box_mimo_data(
                    stats,
                    data_type=data_type,
                    link_direction='DL',
                    band_type=band_type,
                    integrity_suffix=integrity_suffix
                )
        
    logger.info("Plotting completed.")

if __name__ == "__main__":
    main()

