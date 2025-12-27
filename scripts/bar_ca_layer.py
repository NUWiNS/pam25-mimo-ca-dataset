import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import logging
import pickle
import matplotlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set Matplotlib style using relative path
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

DATA_TYPE_CONFIG = {
    'use_t1_t3': False,
    'data_col': 'Layer1 DL Layer Num (Mode)',
    'ylabel': 'MIMO Layers',
    'title_suffix': 'MIMO Layers',
    'filename_prefix': 'bar_ca_layers'
}

def plot_bar_ca_data(all_ca_stats, data_type='LAYERS', link_direction='DL', band_type='mmWave', plot_mode='values', integrity_suffix=""):
    """
    Plot bar charts for CA data showing layer distribution across different CA types
    """
    try:
        if data_type != 'LAYERS':
            logger.error(f"Only LAYERS data type is supported, received: {data_type}")
            return
            
        config = DATA_TYPE_CONFIG
        plot_mode = 'values'
        
        if band_type == 'mmWave':
            target_operators = ['ATT', 'Verizon']
        else:
            target_operators = ['ATT', 'TMobile', 'Verizon']
        
        for operator in target_operators:
            ca_data = all_ca_stats.get(operator, {})
            if not ca_data:
                logger.warning(f"{operator} has no {band_type} data, skipping")
                continue
            
            available_ca_types = []
            ca_layer_stats = {}
            
            for ca_type in ['NonCA', '2CA', '3CA', '4CA', '5CA', '6CA', '7CA', '8CA']:
                if ca_type in ca_data and len(ca_data[ca_type]['values']) > 0:
                    layer_values = ca_data[ca_type]['values']
                    
                    layer_counts = {}
                    total_count = len(layer_values)
                    
                    for layer_value in layer_values:
                        layer_key = f'{int(layer_value)} Layer'
                        layer_counts[layer_key] = layer_counts.get(layer_key, 0) + 1
                    
                    layer_percentages = {layer: (count/total_count)*100 for layer, count in layer_counts.items()}
                    
                    ca_layer_stats[ca_type] = {
                        'percentages': layer_percentages,
                        'total_count': total_count
                    }
                    available_ca_types.append(ca_type)
            
            if band_type == 'mmWave':
                if operator == 'ATT':
                    allowed_types = {'NonCA', '4CA', '8CA'}
                    available_ca_types = [ct for ct in available_ca_types if ct in allowed_types]
                elif operator == 'Verizon':
                    allowed_types = {'NonCA', '4CA', '6CA', '8CA'}
                    available_ca_types = [ct for ct in available_ca_types if ct in allowed_types]
            
            if not available_ca_types:
                continue
            
            fig, ax = plt.subplots(figsize=(8, 7))
            
            layer_colors = {
                '1 Layer': "#08710C",
                '2 Layer': "#70CA32",
                '3 Layer': "#ADE728",
                '4 Layer': "#F3FF33", 
            }
            
            all_layer_types = set()
            for ca_type in available_ca_types:
                all_layer_types.update(ca_layer_stats[ca_type]['percentages'].keys())
            
            sorted_layer_types = sorted(all_layer_types, key=lambda x: int(x.split()[0]))
            
            x = range(len(available_ca_types))
            width = 0.8
            bottom = np.zeros(len(available_ca_types))
            handles = []
            
            for layer_type in sorted_layer_types:
                values = []
                for ca_type in available_ca_types:
                    percentage = ca_layer_stats[ca_type]['percentages'].get(layer_type, 0)
                    values.append(percentage)
                
                bars = ax.bar(x, values, width, bottom=bottom, 
                             color=layer_colors.get(layer_type, '#999999'), 
                             label=layer_type, alpha=0.8)
                
                if any(v > 0 for v in values):
                    handles.append(plt.Rectangle((0,0),1,1, color=layer_colors.get(layer_type, '#999999')))
                
                bottom = [b + v for b, v in zip(bottom, values)]
            
            x_labels = []
            ca_to_num = {'NonCA': '1', '2CA': '2', '3CA': '3', '4CA': '4', '5CA': '5', '6CA': '6', '7CA': '7', '8CA': '8'}
            for ca_type in available_ca_types:
                x_labels.append(ca_to_num.get(ca_type, ca_type))
            
            ax.set_xticks(x)
            ax.set_xticklabels(x_labels)
            
            actual_layer_types = [layer_type for layer_type in sorted_layer_types 
                                 if any(ca_layer_stats[ca_type]['percentages'].get(layer_type, 0) > 0 
                                       for ca_type in available_ca_types)]
            
            if handles and actual_layer_types:
                legend_labels = [layer_type.split()[0] for layer_type in actual_layer_types]
                legend_ncol = min(len(actual_layer_types), 2)
                ax.legend(
                    handles, legend_labels,
                    loc='upper center',
                    bbox_to_anchor=(0.5, 0.995),
                    ncol=legend_ncol,
                    borderaxespad=0.2,
                )
            
            ax.set_xlabel('Number of CCs')
            ax.set_ylabel('Percentage (%)')
            if len(actual_layer_types) > 2:
                ax.set_ylim(0, 154)
                plt.yticks(range(0, 101, 20))
            else:
                ax.set_ylim(0, 126)
                plt.yticks(range(0, 101, 20))
            
            plt.tight_layout()
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            plots_dir = os.path.join(current_dir, '..', 'plots')
            os.makedirs(plots_dir, exist_ok=True)
            
            filename = f'bar_ca_layers_{band_type}_{operator}_{link_direction.lower()}'
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
    
    pkl_filename = os.path.join(pkl_dir, 'bar_ca_layer_dl.pkl')
    if not os.path.exists(pkl_filename):
        logger.warning(f"Pickle file not found: {pkl_filename}")
        return

    with open(pkl_filename, 'rb') as f:
        pkl_data = pickle.load(f)
        
    all_ca_stats_low = pkl_data['Low']
    all_ca_stats_mid = pkl_data['Mid']
    all_ca_stats_mmwave = pkl_data['mmWave']
    
    band_stats = [
        (all_ca_stats_low, 'Low'),
        (all_ca_stats_mid, 'Mid'), 
        (all_ca_stats_mmwave, 'mmWave')
    ]
    
    for stats, band_type in band_stats:
        if stats:
            logger.info(f"Plotting {band_type} band DL LAYERS...")
            plot_bar_ca_data(
                stats,
                data_type='LAYERS',
                link_direction='DL',
                band_type=band_type,
                plot_mode='values',
                integrity_suffix=integrity_suffix
            )
            
    logger.info("Plotting completed.")

if __name__ == "__main__":
    main()
