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

def plot_ca_distribution(operator_data, link_direction='DL'):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plots_dir = os.path.join(current_dir, '..', 'plots')
        os.makedirs(plots_dir, exist_ok=True)
        
        ca_colors = {
            'DL NonCA': SPECTRUM_COLORS[0],
            'DL 2CA': SPECTRUM_COLORS[1],
            'DL 3CA': SPECTRUM_COLORS[2],
            'DL 4CA': SPECTRUM_COLORS[3],
            'DL 5CA': SPECTRUM_COLORS[4],
            'DL 6CA': SPECTRUM_COLORS[5],
            'DL 7CA': SPECTRUM_COLORS[6],
            'DL 8CA': SPECTRUM_COLORS[7],
            'UL NonCA': SPECTRUM_COLORS[0],
            'UL 2CA': SPECTRUM_COLORS[1],
            'UL 3CA': SPECTRUM_COLORS[2],
            'UL 4CA': SPECTRUM_COLORS[3],
            'UL 5CA': SPECTRUM_COLORS[4],
            'UL 6CA': SPECTRUM_COLORS[5],
            'UL 7CA': SPECTRUM_COLORS[6],
            'UL 8CA': SPECTRUM_COLORS[7]
        }
        
        if link_direction == 'DL':
            ca_order = ['DL NonCA', 'DL 2CA', 'DL 3CA', 'DL 4CA', 'DL 5CA', 'DL 6CA', 'DL 7CA', 'DL 8CA']
        else:
            ca_order = ['UL NonCA', 'UL 2CA', 'UL 3CA', 'UL 4CA', 'UL 5CA', 'UL 6CA', 'UL 7CA', 'UL 8CA']
        
        for operator, band_data in operator_data.items():
            if not band_data:
                continue
            
            if operator == 'TMobile':
                band_data = {b: v for b, v in band_data.items() if b not in ('n66', 'n260')}
                if not band_data:
                    continue
                
            band_totals = {}
            for band, ca_counts in band_data.items():
                band_totals[band] = sum(ca_counts.values())
            
            type_order = {'5G Low': 0, '5G Mid': 1, '5G mmWave': 2}
            sorted_bands = sorted(
                band_totals.keys(),
                key=lambda b: (
                    type_order.get(classify_5g_type(b, None), 3),
                    -band_totals[b],
                    extract_band_number(b)
                )
            )
            
            band_ca_percentages = {}
            for band in sorted_bands:
                ca_counts = band_data[band]
                total = band_totals[band]
                percentages = {ca_type: (count/total)*100 for ca_type, count in ca_counts.items()}
                band_ca_percentages[band] = percentages
                
            plt.figure(figsize=(8, 7))
            
            x = range(len(band_ca_percentages))
            width = 0.8
            bottom = np.zeros(len(band_ca_percentages))
            
            existing_ca_types = set()
            for band_stats in band_ca_percentages.values():
                existing_ca_types.update(band_stats.keys())
            
            handles = []
            for ca_type in ca_order:
                if ca_type in existing_ca_types:
                    values = [band_ca_percentages[band].get(ca_type, 0) for band in sorted_bands]
                    bars = plt.bar(x, values, width, bottom=bottom, color=ca_colors.get(ca_type, '#000000'), label=ca_type)
                    handles.append(plt.Rectangle((0,0),1,1, color=ca_colors.get(ca_type, '#000000')))
                    bottom += values
            
            for ca_type in sorted(existing_ca_types):
                if ca_type not in ca_order:
                    values = [band_ca_percentages[band].get(ca_type, 0) for band in sorted_bands]
                    bars = plt.bar(x, values, width, bottom=bottom, color='#999999', label=ca_type)
                    handles.append(plt.Rectangle((0,0),1,1, color='#999999'))
                    bottom += values
            
            plt.xlabel('PCell Band')
            plt.ylabel('Percentage (%)')
            if len(existing_ca_types) > 2:
                plt.ylim(0, 136)
                plt.yticks(range(0, 101, 20))
            else:
                plt.ylim(0, 120)
                plt.yticks(range(0, 101, 20))
            
            x_labels = [f"{band}" for band in sorted_bands]
            plt.xticks(x, x_labels)
            
            # Map CA label to CC label for legend
            cc_label_map = {
                'DL NonCA': '1CC', 'DL 2CA': '2CC', 'DL 3CA': '3CC', 'DL 4CA': '4CC',
                'DL 5CA': '5CC', 'DL 6CA': '6CC', 'DL 7CA': '7CC', 'DL 8CA': '8CC',
                'UL NonCA': '1CC', 'UL 2CA': '2CC', 'UL 3CA': '3CC', 'UL 4CA': '4CC',
                'UL 5CA': '5CC', 'UL 6CA': '6CC', 'UL 7CA': '7CC', 'UL 8CA': '8CC'
            }

            legend_labels = [ca_type for ca_type in ca_order if ca_type in existing_ca_types]
            legend_handles = [handles[i] for i, _ in enumerate(legend_labels)]
            clean_legend_labels = [cc_label_map.get(label, label) for label in legend_labels]
            
            if operator == 'ATT':
                filtered_legend_data = [(handle, label) for handle, label in zip(legend_handles, clean_legend_labels) 
                                      if label in ['1CC', '2CC', '3CC', '4CC']]
            elif operator == 'Verizon':
                filtered_legend_data = [(handle, label) for handle, label in zip(legend_handles, clean_legend_labels) 
                                      if label in ['5CC', '6CC', '7CC', '8CC']]
            else:
                filtered_legend_data = list(zip(legend_handles, clean_legend_labels))
            
            if filtered_legend_data:
                filtered_handles, filtered_labels = zip(*filtered_legend_data)
                legend_ncol = min(len(filtered_labels), 2)
                plt.legend(
                    filtered_handles, filtered_labels,
                    loc='upper center',
                    bbox_to_anchor=(0.5, 0.997),
                    ncol=legend_ncol,
                    borderaxespad=0.2,
                )
            plt.tight_layout()
            
            plt.savefig(os.path.join(plots_dir, f'bar_ca_type_distribution_{operator}_{link_direction.lower()}.pdf'), bbox_inches='tight', dpi=300)
            logger.info(f"Saved plot: bar_ca_type_distribution_{operator}_{link_direction.lower()}.pdf")
            plt.close()
            
    except Exception as e:
        logger.error(f"Error during plotting: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pkl_dir = os.path.join(current_dir, '..', 'pkl')
    
    pkl_filename = os.path.join(pkl_dir, 'bar_ca_type_distribution_dl.pkl')
    if not os.path.exists(pkl_filename):
        logger.warning(f"Pickle file not found: {pkl_filename}")
        return
        
    with open(pkl_filename, 'rb') as f:
        dl_operator_data = pickle.load(f)
        
    plot_ca_distribution(dl_operator_data, link_direction='DL')

if __name__ == "__main__":
    main()

