import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import logging
import re
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

SPECTRUM_COLORS = [
    "#08710C",
    "#70CA32",
    "#ADE728",
    "#F3FF33",
    "#FFB233",
    "#FF7A30",
    "#FF4629",
    "#CB0404",
]

def extract_band_number(band):
    match = re.search(r'n(\d+)', band)
    return int(match.group(1)) if match else 0

def classify_5g_type(band, frequency):
    low_bands = ['n71', 'n12', 'n13', 'n14', 'n5']
    mid_bands = ['n2', 'n25', 'n66', 'n41', 'n77', 'n78', 'n48', 'n53']
    mmwave_bands = ['n260', 'n261']
    
    if pd.notna(band):
        if band in low_bands: return '5G Low'
        elif band in mid_bands: return '5G Mid'
        elif band in mmwave_bands: return '5G mmWave'
    
    if pd.notna(frequency):
        freq = float(frequency)
        if freq < 1000: return '5G Low'
        elif freq < 6000: return '5G Mid'
        else: return '5G mmWave'
    return None

def plot_mimo_distribution(operator_data, link_direction='UL'):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plots_dir = os.path.join(current_dir, '..', 'plots')
        os.makedirs(plots_dir, exist_ok=True)
        
        for operator, data in operator_data.items():
            cell_data = data
            combined_band_mimo_counts = {}
            cell_types = ['PCell'] + [f'SCell[{i}]' for i in range(1, 8)]
            
            for cell_type in cell_types:
                if cell_type in cell_data:
                    for band, mimo_counts in cell_data[cell_type].items():
                        if band not in combined_band_mimo_counts:
                            combined_band_mimo_counts[band] = {}
                        for mode, count in mimo_counts.items():
                            if mode not in combined_band_mimo_counts[band]:
                                combined_band_mimo_counts[band][mode] = 0
                            combined_band_mimo_counts[band][mode] += count
            
            if not combined_band_mimo_counts:
                logger.warning(f"{operator} no data, skipping")
                continue
            
            if operator == 'TMobile':
                for banned_band in ('n66', 'n260'):
                    combined_band_mimo_counts.pop(banned_band, None)
                if not combined_band_mimo_counts:
                    continue
                
            band_totals = {}
            for band, mimo_counts in combined_band_mimo_counts.items():
                band_totals[band] = sum(mimo_counts.values())
            
            type_order = {'5G Low': 0, '5G Mid': 1, '5G mmWave': 2}
            sorted_bands = sorted(
                band_totals.keys(),
                key=lambda b: (
                    type_order.get(classify_5g_type(b, None), 3),
                    -band_totals[b],
                    extract_band_number(b)
                )
            )
            
            band_mimo_percentages = {}
            for band in sorted_bands:
                mimo_counts = combined_band_mimo_counts[band]
                total = band_totals[band]
                percentages = {mode: (count/total)*100 for mode, count in mimo_counts.items()}
                band_mimo_percentages[band] = percentages
                
            plt.figure(figsize=(8, 7))
            
            x = range(len(band_mimo_percentages))
            width = 0.8
            colors = SPECTRUM_COLORS
            
            bottom = np.zeros(len(band_mimo_percentages))
            mimo_modes = set()
            for band_data in band_mimo_percentages.values():
                mimo_modes.update(band_data.keys())
            
            handles = []
            for i, mode in enumerate(sorted(mimo_modes)):
                values = [band_mimo_percentages[band].get(mode, 0) for band in sorted_bands]
                plt.bar(x, values, width, bottom=bottom, color=colors[i % len(colors)], label=mode)
                handles.append(plt.Rectangle((0,0),1,1, color=colors[i % len(colors)]))
                bottom += values
            
            operator_names = {'ATT': 'AT&T', 'TMobile': 'T-Mobile', 'Verizon': 'Verizon'}
            
            plt.xlabel('Band')
            plt.ylabel('Percentage (%)')
            plt.ylim(0, 120)
            plt.yticks(range(0, 101, 20))

            legend_labels = []
            for mode in sorted(mimo_modes):
                if mode == '1x1_MIMO': legend_labels.append('1x1') # UL specific
                elif mode == '2x2_MIMO': legend_labels.append('2x2')
                else: legend_labels.append(mode)
            
            legend_ncol = min(len(mimo_modes), 4)
            plt.legend(
                handles, legend_labels,
                loc='upper center',
                bbox_to_anchor=(0.5, 0.997),
                ncol=legend_ncol,
                borderaxespad=0.2
            )
            plt.tight_layout()
            
            x_labels = [f"{band}" for band in sorted_bands]
            plt.xticks(x, x_labels)
            
            plt.savefig(os.path.join(plots_dir, f'bar_mimo_mode_all_cells_{operator}_{link_direction.lower()}.pdf'), bbox_inches='tight', dpi=300)
            logger.info(f"Saved plot: bar_mimo_mode_all_cells_{operator}_{link_direction.lower()}.pdf")
            plt.close()
            
    except Exception as e:
        logger.error(f"Error during plotting: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pkl_dir = os.path.join(current_dir, '..', 'pkl')
    
    pkl_filename = os.path.join(pkl_dir, 'bar_mimo_mode_all_cells_ul.pkl')
    if not os.path.exists(pkl_filename):
        logger.warning(f"Pickle file not found: {pkl_filename}")
        return
        
    with open(pkl_filename, 'rb') as f:
        ul_operator_data = pickle.load(f)
        
    plot_mimo_distribution(ul_operator_data, link_direction='UL')

if __name__ == "__main__":
    main()
