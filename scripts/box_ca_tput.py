import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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
        # Fallback default style
        plt.style.use('default')
        logger.warning(f"matplotlibrc not found at {style_path}, using default style")
except Exception as e:
    logger.warning(f"Could not load matplotlibrc: {e}")

# Define data type configurations for different metrics
DATA_TYPE_CONFIGS = {
    'TPUT': {
        'use_tca_tt': True,  # Use Tca/Tt calculation for throughput
        'ylabel': 'Throughput (Mbps)',
        'title_suffix': 'Throughput',
        'filename_prefix': 'box_ca_tput'
    },
    'MCS': {
        'use_tca_tt': False,  # Use direct values for other metrics
        'data_col': 'Layer1 DL MCS (Avg)',
        'ylabel': 'MCS',
        'title_suffix': 'MCS',
        'filename_prefix': 'box_ca_mcs'
    },
    'RSRP': {
        'use_tca_tt': False,
        'data_col': 'RF Serving SS-RSRP [dBm]',
        'ylabel': 'RSRP (dBm)',
        'title_suffix': 'RSRP',
        'filename_prefix': 'box_ca_rsrp'
    },
    'CQI': {
        'use_tca_tt': False,
        'data_col': 'RF CQI',
        'ylabel': 'CQI',
        'title_suffix': 'CQI',
        'filename_prefix': 'box_ca_cqi'
    },
    'BANDWIDTH': {
        'use_tca_tt': False,
        'data_col': 'RF BandWidth',
        'ylabel': 'Bandwidth (MHz)',
        'title_suffix': 'Bandwidth',
        'filename_prefix': 'box_ca_bandwidth'
    },
    'LAYERS': {
        'use_tca_tt': False,
        'data_col': 'Layer1 DL Layer Num (Mode)',
        'ylabel': 'MIMO Layers',
        'title_suffix': 'MIMO Layers',
        'filename_prefix': 'box_ca_layers'
    }
}

def plot_box_ca_data(all_ca_stats, data_type='TPUT', link_direction='DL', band_type='mmWave', plot_mode='Tca', integrity_suffix=""):
    """
    Plot box charts for CA data across different CA types
    """
    try:
        # Get data type configuration
        config = DATA_TYPE_CONFIGS.get(data_type, DATA_TYPE_CONFIGS['TPUT'])
        use_tca_tt = config['use_tca_tt']
        
        # For non-TPUT data types, force plot_mode to 'values'
        if not use_tca_tt:
            plot_mode = 'values'
        
        # Define which operators to plot for each band type
        if band_type == 'mmWave':
            # Only ATT and Verizon have mmWave data
            target_operators = ['ATT', 'Verizon']
        else:
            # All operators have Low/Mid band data
            target_operators = ['ATT', 'TMobile', 'Verizon']
        
        # Create separate charts for each target operator
        for operator in target_operators:
            ca_data = all_ca_stats.get(operator, {})
            
            if not ca_data:
                logger.warning(f"{operator} has no {band_type} data, skipping")
                continue
            
            # Get all available CA types with data
            available_ca_types = []
            for ca_type in ['NonCA', '2CA', '3CA', '4CA', '5CA', '6CA', '7CA', '8CA']:
                if ca_type in ca_data:
                    if use_tca_tt:
                        # TPUT data with Tca/Tt structure
                        if plot_mode == 'Tca' and len(ca_data[ca_type]['Tca']) > 0:
                            available_ca_types.append(ca_type)
                        elif plot_mode == 'Tt' and len(ca_data[ca_type]['Tt']) > 0:
                            available_ca_types.append(ca_type)
                        elif plot_mode == 'Tca_vs_Tt' and (len(ca_data[ca_type]['Tca']) > 0 or len(ca_data[ca_type]['Tt']) > 0):
                            available_ca_types.append(ca_type)
                    else:
                        # Other data types with 'values' structure
                        if plot_mode == 'values' and len(ca_data[ca_type]['values']) > 0:
                            available_ca_types.append(ca_type)
            
            # Apply operator-specific CA filters for mmWave plotting only
            if band_type == 'mmWave':
                if operator == 'ATT':
                    allowed_types = {'NonCA', '4CA', '8CA'}
                    available_ca_types = [ct for ct in available_ca_types if ct in allowed_types]
                elif operator == 'Verizon':
                    allowed_types = {'NonCA', '4CA', '6CA', '8CA'}
                    available_ca_types = [ct for ct in available_ca_types if ct in allowed_types]
            
            if not available_ca_types:
                logger.warning(f"{operator} has no valid {band_type} data for {plot_mode}, skipping")
                continue
            
            # Create new chart
            fig, ax = plt.subplots(figsize=(8, 7))
            
            # Prepare data for plotting
            plot_data = []
            plot_labels = []
            plot_positions = []
            
            if plot_mode in ['Tca', 'Tt', 'values']:
                # Single data type plotting
                for i, ca_type in enumerate(available_ca_types):
                    data = ca_data[ca_type][plot_mode]
                    if len(data) > 0:
                        plot_data.append(data)
                        # Map CA label to numeric CC count for x-axis label
                        ca_to_num = {'NonCA': '1', '2CA': '2', '3CA': '3', '4CA': '4', '5CA': '5', '6CA': '6', '7CA': '7', '8CA': '8'}
                        plot_labels.append(ca_to_num.get(ca_type, ca_type))
                        plot_positions.append(i + 1)
                
                # Create box plot
                if plot_data:
                    bp = ax.boxplot(plot_data, positions=plot_positions, labels=plot_labels,
                                   patch_artist=True, showfliers=True, widths=0.5)
                    
                    # Customize box plot colors and line styles
                    uniform_color = 'lightblue'  # Single color for all boxes in single mode
                    for patch in bp['boxes']:
                        patch.set_facecolor(uniform_color)
                        patch.set_alpha(0.7)
                        patch.set_linewidth(4)  # Make box outline thicker
                    
                    # Customize median lines (make them red and thicker)
                    for median in bp['medians']:
                        median.set_color('orange')
                        median.set_linewidth(5)
                    
                    # Customize whiskers (make them thicker)
                    for whisker in bp['whiskers']:
                        whisker.set_linewidth(4)
                    
                    # Customize caps (make them thicker)
                    for cap in bp['caps']:
                        cap.set_linewidth(4)
                    
                    # Customize outlier markers
                    for flier in bp['fliers']:
                        flier.set_markeredgewidth(3)
            
            elif plot_mode == 'Tca_vs_Tt':
                # Comparison plotting with paired boxes
                position = 1
                xtick_positions = []
                xtick_labels = []
                
                # Define consistent colors for Tca vs Tt comparison
                tca_color = 'lightblue'      # Uniform color for all Tca boxes
                tt_color = 'lightcoral'     # Uniform color for all Tt boxes
                
                # Adjust spacing and width based on number of CA types
                num_ca_types = len(available_ca_types)
                if num_ca_types <= 3:
                    box_width = 0.35
                    spacing = 0.4
                elif num_ca_types <= 5:
                    box_width = 0.32
                    spacing = 0.38
                else:
                    box_width = 0.28
                    spacing = 0.35
                
                for ca_type in available_ca_types:
                    tca_data = ca_data[ca_type]['Tca']
                    tt_data = ca_data[ca_type]['Tt']
                    
                    # Plot Tca box if data exists
                    if len(tca_data) > 0:
                        bp1 = ax.boxplot([tca_data], positions=[position], widths=box_width,
                                        patch_artist=True, showfliers=True)
                        bp1['boxes'][0].set_facecolor(tca_color)
                        bp1['boxes'][0].set_alpha(0.7)
                        bp1['boxes'][0].set_linewidth(4)  # Make box outline thicker
                        
                        # Customize Tca box elements
                        bp1['medians'][0].set_color('orange')
                        bp1['medians'][0].set_linewidth(5)
                        for whisker in bp1['whiskers']:
                            whisker.set_linewidth(4)
                        for cap in bp1['caps']:
                            cap.set_linewidth(4)
                        for flier in bp1['fliers']:
                            flier.set_markeredgewidth(3)
                    
                    # Plot Tt box if data exists
                    if len(tt_data) > 0:
                        bp3 = ax.boxplot([tt_data], positions=[position + spacing], widths=box_width,
                                        patch_artist=True, showfliers=True)
                        bp3['boxes'][0].set_facecolor(tt_color)
                        bp3['boxes'][0].set_alpha(0.7)
                        bp3['boxes'][0].set_linewidth(4)  # Make box outline thicker
                        
                        # Customize Tt box elements
                        bp3['medians'][0].set_color('orange')
                        bp3['medians'][0].set_linewidth(5)
                        for whisker in bp3['whiskers']:
                            whisker.set_linewidth(4)
                        for cap in bp3['caps']:
                            cap.set_linewidth(4)
                        for flier in bp3['fliers']:
                            flier.set_markeredgewidth(3)
                    
                    # Store position and label for x-axis
                    xtick_positions.append(position + spacing/2)  # Center between Tca and Tt
                    
                    # Map CA label to numeric CC count for x-axis label
                    ca_to_num = {'NonCA': '1', '2CA': '2', '3CA': '3', '4CA': '4', '5CA': '5', '6CA': '6', '7CA': '7', '8CA': '8'}
                    xtick_labels.append(ca_to_num.get(ca_type, ca_type))
                    
                    # Adjust position increment based on spacing to avoid overlap
                    position += spacing + 0.6  # Add extra space between CA type groups
                
                # Set custom x-axis ticks and labels
                ax.set_xticks(xtick_positions)
                ax.set_xticklabels(xtick_labels)
                
                # Add legend for Tca vs Tt
                from matplotlib.patches import Patch
                legend_elements = [Patch(facecolor=tca_color, alpha=0.7, label=r'T$_{CA}$'),
                                  Patch(facecolor=tt_color, alpha=0.7, label=r'T$_{TOTAL}$')]
                ax.legend(handles=legend_elements, loc='upper left')
            
            # Set chart title and labels
            if use_tca_tt:
                # TPUT data type
                if plot_mode == 'Tca':
                    title_suffix = r'T$_{CA}$ (Normalized Throughput)'
                    ylabel = 'Normalized Throughput (Mbps)'
                elif plot_mode == 'Tt':
                    title_suffix = r'T$_{TOTAL}$ (Raw Sum Throughput)'
                    ylabel = 'Raw Sum Throughput (Mbps)'
                else:
                    title_suffix = r'T$_{CA}$ vs T$_{TOTAL}$ Comparison'
                    ylabel = 'Throughput (Mbps)'
            else:
                # Other data types
                title_suffix = config['title_suffix']
                ylabel = config['ylabel']
            
            ax.set_xlabel('Number of CCs')
            ax.set_ylabel(ylabel)
            
            # Add grid for better readability
            ax.grid(True, alpha=0.3)
            
            # Adjust layout to prevent label cutoff
            plt.tight_layout()
            
            # Create save directory (relative to this script)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            plots_dir = os.path.join(current_dir, '..', 'plots')
            os.makedirs(plots_dir, exist_ok=True)
            
            # Create filename using consistent format
            if use_tca_tt:
                filename = f'{config["filename_prefix"]}_{plot_mode}_{band_type}_{operator}_{link_direction.lower()}'
            else:
                filename = f'{config["filename_prefix"]}_{band_type}_{operator}_{link_direction.lower()}'
            
            # Save with appropriate suffix based on integrity filtering
            save_path = os.path.join(plots_dir, f'{filename}{integrity_suffix}.pdf')
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved plot to {save_path}")
            
            plt.close()
        
    except Exception as e:
        logger.error(f"An error occurred during plotting: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    # Control variables for different data types
    TPUT = 1
    MCS = 1
    RSRP = 1
    CQI = 1
    BANDWIDTH = 1
    LAYERS = 0
    
    # Control variables for TPUT plotting modes
    Tca = 0
    Tt = 0
    Tca_vs_Tt = 1
    
    # Default integrity suffix since we process "with_integrity" data by default
    integrity_suffix = "_with_integrity"
    
    # Define directory for pkl files
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pkl_dir = os.path.join(current_dir, '..', 'pkl')
    
    data_types_to_process = []
    if TPUT == 1: data_types_to_process.append('TPUT')
    if MCS == 1: data_types_to_process.append('MCS')
    if RSRP == 1: data_types_to_process.append('RSRP')
    if CQI == 1: data_types_to_process.append('CQI')
    if BANDWIDTH == 1: data_types_to_process.append('BANDWIDTH')
    if LAYERS == 1: data_types_to_process.append('LAYERS')
    
    for data_type in data_types_to_process:
        logger.info(f"Plotting {data_type} data...")
        
        pkl_filename = os.path.join(pkl_dir, f'box_ca_{data_type.lower()}_dl.pkl')
        if not os.path.exists(pkl_filename):
            logger.warning(f"Pickle file not found: {pkl_filename}")
            continue
            
        with open(pkl_filename, 'rb') as f:
            pkl_data = pickle.load(f)
            
        all_ca_stats_low = pkl_data['Low']
        all_ca_stats_mid = pkl_data['Mid']
        all_ca_stats_mmwave = pkl_data['mmWave']
        
        # Plot the results for all three frequency bands
        band_stats = [
            (all_ca_stats_low, 'Low'),
            (all_ca_stats_mid, 'Mid'), 
            (all_ca_stats_mmwave, 'mmWave')
        ]
        
        for stats, band_type in band_stats:
            if stats:
                if data_type == 'TPUT':
                    if Tca == 1:
                        plot_box_ca_data(stats, data_type, 'DL', band_type, 'Tca', integrity_suffix)
                    if Tt == 1:
                        plot_box_ca_data(stats, data_type, 'DL', band_type, 'Tt', integrity_suffix)
                    if Tca_vs_Tt == 1:
                        plot_box_ca_data(stats, data_type, 'DL', band_type, 'Tca_vs_Tt', integrity_suffix)
                else:
                    plot_box_ca_data(stats, data_type, 'DL', band_type, 'values', integrity_suffix)

    logger.info("Plotting completed.")

if __name__ == "__main__":
    main()
