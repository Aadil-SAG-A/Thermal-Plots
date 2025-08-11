# -*- coding: utf-8 -*-
"""
Thermal Analysis Report and Plot Generator

This script reads all settings from a 'config.ini' file, analyzes
satellite thermal simulation data, compares it against acceptance limits,
and generates consolidated plots and a summary text report.
"""

# --- 1. Import Libraries ---
import os
import sys
import configparser
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from scipy.interpolate import pchip_interpolate
from datetime import datetime
import warnings

# Suppress warnings from matplotlib about font properties, which can be noisy.
warnings.filterwarnings("ignore", category=UserWarning)

# Apply a professional and clean plot style
plt.style.use('seaborn-v0_8-whitegrid')


# --- 2. Read Configuration File ---
print("--> Reading configuration from config.ini...")
config = configparser.ConfigParser()
if not os.path.exists('config.ini'):
    print("FATAL ERROR: config.ini not found. Please create it from the template.")
    sys.exit()
config.read('config.ini')

# --- File and Output Configuration ---
simulation_data_filename = config.get('FILES', 'simulation_data_filename')
limits_filename = config.get('FILES', 'limits_filename')

# --- Plot Aesthetics and Configuration ---
line_thickness = config.getfloat('COLORS_AND_STYLES', 'line_thickness')
font_family = config.get('FONTS', 'font_family')
font_settings = {'family': font_family, 'weight': 'bold'}
bold_font = fm.FontProperties(family=font_family, weight='bold')

# --- Font Sizes ---
full_plot_title_fontsize = config.getint('FONTS', 'full_plot_title')
full_plot_label_fontsize = config.getint('FONTS', 'full_plot_labels')
full_plot_axis_fontsize = config.getint('FONTS', 'full_plot_ticks')
zoom_plot_title_fontsize = config.getint('FONTS', 'last_2_orbits_plot_title')
zoom_plot_label_fontsize = config.getint('FONTS', 'last_2_orbits_plot_labels')
zoom_plot_axis_fontsize = config.getint('FONTS', 'last_2_orbits_plot_ticks')
deck_plot_title_fontsize = config.getint('FONTS', 'deck_plot_title')
deck_plot_label_fontsize = config.getint('FONTS', 'deck_plot_labels')
deck_plot_axis_fontsize = config.getint('FONTS', 'deck_plot_ticks')
deck_plot_legend_fontsize = config.getint('FONTS', 'deck_plot_legend')
deck_zoom_plot_title_fontsize = config.getint('FONTS', 'deck_last_2_orbits_plot_title')
deck_zoom_plot_label_fontsize = config.getint('FONTS', 'deck_last_2_orbits_plot_labels')
deck_zoom_plot_axis_fontsize = config.getint('FONTS', 'deck_last_2_orbits_plot_ticks')
deck_zoom_plot_legend_fontsize = config.getint('FONTS', 'deck_last_2_orbits_plot_legend')
deck_last_orbit_plot_title_fontsize = config.getint('FONTS', 'deck_last_orbit_plot_title')
deck_last_orbit_plot_label_fontsize = config.getint('FONTS', 'deck_last_orbit_plot_labels')
deck_last_orbit_plot_axis_fontsize = config.getint('FONTS', 'deck_last_orbit_plot_ticks')
deck_last_orbit_plot_legend_fontsize = config.getint('FONTS', 'deck_last_orbit_plot_legend')


# --- Colors and Styles ---
individual_plot_line_color = config.get('COLORS_AND_STYLES', 'individual_plot_line')
zoom_plot_max_line_color = config.get('COLORS_AND_STYLES', 'zoom_plot_max_line')
zoom_plot_min_line_color = config.get('COLORS_AND_STYLES', 'zoom_plot_min_line')
zoom_plot_limit_line_style = config.get('COLORS_AND_STYLES', 'zoom_plot_limit_line_style')
legend_frame_color = config.get('COLORS_AND_STYLES', 'legend_frame')
legend_face_color = config.get('COLORS_AND_STYLES', 'legend_background')

# --- Axis Ticks ---
full_plot_time_tick_interval = config.getint('AXIS_TICKS', 'time_tick_interval')
zoom_plot_time_tick_interval = config.getint('AXIS_TICKS', 'zoom_time_tick_interval')
deck_plot_time_tick_interval = config.getint('AXIS_TICKS', 'time_tick_interval')
deck_zoom_plot_time_tick_interval = config.getint('AXIS_TICKS', 'zoom_time_tick_interval')
y_tick_interval = config.getint('AXIS_TICKS', 'y_tick_interval')

# --- Axis Ranges ---
def parse_range(config_str):
    if config_str.strip().lower() == 'auto':
        return 'auto'
    return [float(x.strip()) for x in config_str.split(',')]

full_plot_x_range = parse_range(config.get('AXIS_RANGES', 'full_plot_x_range'))
zoom_plot_x_range = parse_range(config.get('AXIS_RANGES', 'last_2_orbits_plot_x_range'))
deck_plot_x_range = parse_range(config.get('AXIS_RANGES', 'deck_plot_x_range'))
deck_zoom_plot_x_range = parse_range(config.get('AXIS_RANGES', 'deck_last_2_orbits_plot_x_range'))
deck_last_orbit_plot_x_range = parse_range(config.get('AXIS_RANGES', 'deck_last_orbit_plot_x_range'))


full_plot_y_range = parse_range(config.get('AXIS_RANGES', 'full_plot_y_range'))
zoom_plot_y_range = parse_range(config.get('AXIS_RANGES', 'last_2_orbits_plot_y_range'))
deck_plot_y_range = parse_range(config.get('AXIS_RANGES', 'deck_plot_y_range'))
deck_zoom_plot_y_range = parse_range(config.get('AXIS_RANGES', 'deck_last_2_orbits_plot_y_range'))
deck_last_orbit_plot_y_range = parse_range(config.get('AXIS_RANGES', 'deck_last_orbit_plot_y_range'))


# Parse manual Y limits from the dedicated section
manual_ylimits = {key: parse_range(value) for key, value in config.items('MANUAL_Y_LIMITS')}

# --- Performance and Filtering ---
generate_individual_plots = config.getboolean('SETTINGS', 'generate_individual_plots')
exclude_components_str = config.get('COMPONENT_FILTERING', 'exclude_components')
excluded_components = [item.strip() for item in exclude_components_str.split(',') if item.strip()]


# --- Create a single main output folder with a timestamp ---
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
main_output_folder = f'Thermal_Analysis_Output_{timestamp}'
print(f"--> Creating main output directory: {main_output_folder}")

output_folder_full = os.path.join(main_output_folder, 'Component_Plots_Full_Profile')
output_folder_zoomed = os.path.join(main_output_folder, 'Component_Plots_Zoomed_Profile')
output_folder_consolidated = os.path.join(main_output_folder, 'Component_Plots_Consolidated_Decks')
output_folder_consolidated_zoomed = os.path.join(main_output_folder, 'Component_Plots_Consolidated_Decks_Zoomed')
output_folder_consolidated_last_orbit = os.path.join(main_output_folder, 'Component_Plots_Consolidated_Decks_Last_Orbit')
output_folder_report = os.path.join(main_output_folder, 'Report')

os.makedirs(output_folder_full, exist_ok=True)
os.makedirs(output_folder_zoomed, exist_ok=True)
os.makedirs(output_folder_consolidated, exist_ok=True)
os.makedirs(output_folder_consolidated_zoomed, exist_ok=True)
os.makedirs(output_folder_consolidated_last_orbit, exist_ok=True)
os.makedirs(output_folder_report, exist_ok=True)


# --- Read and Process Simulation Data ---
print('--> Reading and processing simulation data...')
try:
    data_df = pd.read_csv(simulation_data_filename)
    if 'Time, min' not in data_df.columns:
        print("  'Time, min' column not found. Assuming first column is 'Time, s' and converting.")
        time_col_name = data_df.columns[0]
        data_df.rename(columns={time_col_name: 'Time, min'}, inplace=True)
        data_df['Time, min'] = data_df['Time, min'] / 60.0
    if 'Time, s' in data_df.columns and 'Time, min' in data_df.columns:
         data_df = data_df.drop(columns=['Time, s'])
    data_df.dropna(how='all', inplace=True)
    print(f'Successfully processed data from {simulation_data_filename}.')
except FileNotFoundError:
    print(f"ERROR: Could not find the simulation data file '{simulation_data_filename}'.")
    sys.exit()
except Exception as e:
    print(f"An error occurred while processing the data file: {e}")
    sys.exit()

all_component_names = data_df.columns[1:]

if not os.path.exists(limits_filename):
    print(f'--> Limits file not found. Creating example: {limits_filename}')
    limits_example_df = pd.DataFrame({
        'ComponentName': all_component_names,
        'Acceptance_Min': -10, 'Acceptance_Max': 50,
        'Design_Min': -15, 'Design_Max': 55
    })
    limits_example_df.to_csv(limits_filename, index=False)

print('--> Reading component temperature limits...')
try:
    limits_df = pd.read_csv(limits_filename)
    limits_df.set_index('ComponentName', inplace=True)
    limits_map = limits_df.to_dict('index')
    print(f'Successfully loaded {len(limits_map)} component limit profiles.')
except FileNotFoundError:
    print(f"ERROR: Could not read the limits file '{limits_filename}'.")
    sys.exit()


# --- Process Data and Interpolate ---
time_minutes_original = data_df['Time, min']
num_components = len(all_component_names)
print(f'Found {num_components} components to process.')

num_interp_points = 5000 
time_fine = np.linspace(time_minutes_original.min(), time_minutes_original.max(), num_interp_points)


# --- Generate Individual Plots (Optional) ---
if generate_individual_plots:
    print('\n--> Generating individual plots (This may be slow)...')
    for component_name in all_component_names:
        display_name = component_name.split('.T')[0]
        deck_prefix = display_name.split('_')[0]
        
        deck_folder_full = os.path.join(output_folder_full, deck_prefix)
        deck_folder_zoomed = os.path.join(output_folder_zoomed, deck_prefix)
        os.makedirs(deck_folder_full, exist_ok=True)
        os.makedirs(deck_folder_zoomed, exist_ok=True)

        temp_df = data_df[['Time, min', component_name]].copy()
        temp_df[component_name] = pd.to_numeric(temp_df[component_name], errors='coerce')
        temp_df.dropna(inplace=True)
        temp_df.sort_values(by='Time, min', inplace=True)
        
        if len(temp_df) < 2:
            print(f"  SKIPPING: Not enough valid data points for '{component_name}'.")
            continue
            
        local_time_minutes = temp_df['Time, min']
        component_data_raw = temp_df[component_name]
        component_data_interp = pchip_interpolate(local_time_minutes.values, component_data_raw.values, time_fine)
        
        title_name = display_name.replace(f'{deck_prefix}_', '').replace('_', ' ')
        clean_name = "".join(c for c in title_name if c.isalnum() or c in ('_', '-')).rstrip()

        # Full Profile Plot
        fig_full, ax_full = plt.subplots(figsize=(12, 6))
        ax_full.plot(time_fine, component_data_interp, color=individual_plot_line_color, linewidth=line_thickness)
        ax_full.set_title(title_name, fontsize=full_plot_title_fontsize, **font_settings)
        ax_full.set_xlabel('Time (minutes)', fontsize=full_plot_label_fontsize, **font_settings, labelpad=15)
        ax_full.set_ylabel('Temperature (°C)', fontsize=full_plot_label_fontsize, **font_settings, labelpad=15)
        
        if full_plot_x_range == 'auto':
            xticks = np.arange(0, time_minutes_original.max(), full_plot_time_tick_interval)
            xticks = np.append(xticks, time_minutes_original.max())
            ax_full.set_xticks(np.unique(xticks.astype(int)))
            ax_full.set_xlim(time_fine.min(), time_fine.max())
        else:
            ax_full.set_xlim(full_plot_x_range)
            start_tick = np.floor(full_plot_x_range[0] / full_plot_time_tick_interval) * full_plot_time_tick_interval
            xticks = np.arange(start_tick, full_plot_x_range[1], full_plot_time_tick_interval)
            xticks = np.append(xticks, full_plot_x_range[1])
            ax_full.set_xticks(np.unique(xticks.astype(int)))

        ax_full.tick_params(axis='x', labelrotation=90, labelsize=full_plot_axis_fontsize)
        ax_full.tick_params(axis='y', labelsize=full_plot_axis_fontsize, pad=10)
        plt.setp(ax_full.get_xticklabels(), fontweight="bold")
        plt.setp(ax_full.get_yticklabels(), fontweight="bold")
        
        sim_min, sim_max = component_data_interp.min(), component_data_interp.max()
        if component_name in manual_ylimits:
            ax_full.set_ylim(manual_ylimits[component_name])
            ax_full.set_yticks(np.arange(manual_ylimits[component_name][0], manual_ylimits[component_name][1] + 1, y_tick_interval).astype(int))
        elif full_plot_y_range != 'auto' and sim_min >= full_plot_y_range[0] and sim_max <= full_plot_y_range[1]:
            ax_full.set_ylim(full_plot_y_range)
            ax_full.set_yticks(np.arange(full_plot_y_range[0], full_plot_y_range[1] + 1, y_tick_interval).astype(int))
        else:
            print(f"  WARNING: Data for '{component_name}' exceeds default Y-limits. Auto-adjusting.")
            ylim_lower = np.floor(sim_min / 5) * 5
            ylim_upper = np.ceil(sim_max / 5) * 5
            ax_full.set_ylim(ylim_lower, ylim_upper)
            ax_full.set_yticks(np.arange(ylim_lower, ylim_upper + 1, y_tick_interval).astype(int))
        for spine in ax_full.spines.values():
            spine.set_edgecolor('black')
            spine.set_linewidth(1.5)
        plt.tight_layout()
        fig_full.savefig(os.path.join(deck_folder_full, f'Plot_Full_{clean_name}.png'), dpi=600)
        plt.close(fig_full)

        # Zoomed Profile Plot
        zoom_mask = (time_fine >= zoom_plot_x_range[0]) & (time_fine <= zoom_plot_x_range[1])
        if not np.any(zoom_mask): continue
        time_zoomed_fine = time_fine[zoom_mask]
        data_zoomed_interp = component_data_interp[zoom_mask]
        data_zoomed_raw = component_data_raw[(local_time_minutes >= zoom_plot_x_range[0]) & (local_time_minutes <= zoom_plot_x_range[1])]
        if data_zoomed_raw.empty: continue
        max_val_zoomed, min_val_zoomed = data_zoomed_raw.max(), data_zoomed_raw.min()
        fig_zoomed, ax_zoomed = plt.subplots(figsize=(12, 6))
        ax_zoomed.plot(time_zoomed_fine, data_zoomed_interp, color=individual_plot_line_color, linewidth=line_thickness)
        ax_zoomed.axhline(max_val_zoomed, color=zoom_plot_max_line_color, linestyle=zoom_plot_limit_line_style, linewidth=2, label=f'Max: {max_val_zoomed:.2f}°C')
        ax_zoomed.axhline(min_val_zoomed, color=zoom_plot_min_line_color, linestyle=zoom_plot_limit_line_style, linewidth=2, label=f'Min: {min_val_zoomed:.2f}°C')
        ax_zoomed.set_title(title_name, fontsize=zoom_plot_title_fontsize, **font_settings)
        ax_zoomed.set_xlabel('Time (minutes)', fontsize=zoom_plot_label_fontsize, **font_settings, labelpad=15)
        ax_zoomed.set_ylabel('Temperature (°C)', fontsize=zoom_plot_label_fontsize, **font_settings, labelpad=15)
        start_tick = np.floor(zoom_plot_x_range[0] / zoom_plot_time_tick_interval) * zoom_plot_time_tick_interval
        xticks_zoomed = np.arange(start_tick, zoom_plot_x_range[1], zoom_plot_time_tick_interval)
        xticks_zoomed = np.append(xticks_zoomed, zoom_plot_x_range[1])
        ax_zoomed.set_xticks(np.unique(xticks_zoomed.astype(int)))
        ax_zoomed.tick_params(axis='x', labelrotation=90, labelsize=zoom_plot_axis_fontsize)
        ax_zoomed.tick_params(axis='y', labelsize=zoom_plot_axis_fontsize, pad=10)
        plt.setp(ax_zoomed.get_xticklabels(), fontweight="bold")
        plt.setp(ax_zoomed.get_yticklabels(), fontweight="bold")
        ax_zoomed.set_xlim(zoom_plot_x_range)
        ylim_lower, ylim_upper = np.floor(data_zoomed_interp.min() / 5) * 5, np.ceil(data_zoomed_interp.max() / 5) * 5
        ax_zoomed.set_ylim(ylim_lower, ylim_upper)
        ax_zoomed.set_yticks(np.arange(ylim_lower, ylim_upper + 1, y_tick_interval).astype(int))
        leg = ax_zoomed.legend(loc='upper right', frameon=True, fontsize=deck_zoom_plot_legend_fontsize)
        leg.get_frame().set_facecolor(legend_face_color)
        leg.get_frame().set_edgecolor(legend_frame_color)
        leg.get_frame().set_alpha(1.0)
        for text in leg.get_texts(): text.set_fontproperties(bold_font)
        for spine in ax_zoomed.spines.values():
            spine.set_edgecolor('black')
            spine.set_linewidth(1.5)
        plt.tight_layout()
        fig_zoomed.savefig(os.path.join(deck_folder_zoomed, f'Plot_Zoomed_{clean_name}.png'), dpi=600)
        plt.close(fig_zoomed)
    print('Finished generating individual plots.')
else:
    print('\n--> Skipping generation of individual plots for a faster run.')


# --- Group Components by Deck and Generate Consolidated Plots & Report ---
print('\n--> Grouping components and generating consolidated plots and report...')
deck_groups = {}
for component_name in all_component_names:
    display_name = component_name.split('.T')[0]
    deck_prefix = display_name.split('_')[0]
    if deck_prefix not in deck_groups:
        deck_groups[deck_prefix] = []
    deck_groups[deck_prefix].append(component_name)

report_filepath = os.path.join(output_folder_report, 'thermal_report.txt')
with open(report_filepath, 'w') as report_file:
    report_file.write('=' * 85 + '\n')
    report_file.write('SATELLITE THERMAL ANALYSIS REPORT\n')
    report_file.write('=' * 85 + '\n')
    report_file.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    color_cycle = plt.get_cmap('tab10').colors
    for deck_name, component_list in deck_groups.items():
        print(f"Processing Deck: {deck_name}...")
        report_file.write('-' * 85 + '\n')
        report_file.write(f'Analysis for Deck: {deck_name}\n')
        report_file.write('-' * 85 + '\n\n')
        header = f"{'Component':<25} | {'Sim Range [C]':<15} | {'Accept Range [C]':<18} | {'Hot Margin [C]':<15} | {'Status':<10}\n"
        report_file.write(header)
        report_file.write('-' * len(header) + '\n')
        
        fig_deck, ax_deck = plt.subplots(figsize=(16, 9))
        fig_deck_zoomed, ax_deck_zoomed = plt.subplots(figsize=(16, 9))
        fig_deck_last_orbit, ax_deck_last_orbit = plt.subplots(figsize=(16, 9))
        all_interp_data_for_deck = []
        
        for i, component_name in enumerate(component_list):
            if component_name in excluded_components:
                continue
            display_name = component_name.split('.T')[0]
            temp_df = data_df[['Time, min', component_name]].copy()
            temp_df[component_name] = pd.to_numeric(temp_df[component_name], errors='coerce')
            temp_df.dropna(inplace=True)
            if len(temp_df) < 2: continue
            local_time_minutes = temp_df['Time, min']
            component_data_raw = temp_df[component_name]
            component_data_interp = pchip_interpolate(local_time_minutes.values, component_data_raw.values, time_fine)
            all_interp_data_for_deck.append(component_data_interp)
            color = color_cycle[i % len(color_cycle)]
            legend_label = display_name.replace(f'{deck_name}_', '').replace('_', ' ')
            
            ax_deck.plot(time_fine, component_data_interp, linewidth=line_thickness, color=color, label=legend_label)
            zoom_mask = (time_fine >= deck_zoom_plot_x_range[0]) & (time_fine <= deck_zoom_plot_x_range[1])
            if np.any(zoom_mask):
                ax_deck_zoomed.plot(time_fine[zoom_mask], component_data_interp[zoom_mask], linewidth=line_thickness, color=color, label=legend_label)
            last_orbit_mask = (time_fine >= deck_last_orbit_plot_x_range[0]) & (time_fine <= deck_last_orbit_plot_x_range[1])
            if np.any(last_orbit_mask):
                ax_deck_last_orbit.plot(time_fine[last_orbit_mask], component_data_interp[last_orbit_mask], linewidth=line_thickness, color=color, label=legend_label)

            sim_min, sim_max = component_data_interp.min(), component_data_interp.max()
            if component_name in limits_map:
                limits = limits_map[component_name]
                hot_margin = limits['Acceptance_Max'] - sim_max
                cold_margin = sim_min - limits['Acceptance_Min']
                status = 'PASS' if (hot_margin >= 0 and cold_margin >= 0) else 'FAIL'
                sim_range_str = f"[{sim_min:<6.1f}, {sim_max:<6.1f}]"
                acc_range_str = f"[{limits['Acceptance_Min']:<6.0f}, {limits['Acceptance_Max']:<6.0f}]"
                report_file.write(f"{display_name.replace('_', ' '):<25} | {sim_range_str:<15} | {acc_range_str:<18} | {hot_margin:<15.2f} | {status:<10}\n")
            else:
                report_file.write(f"{display_name.replace('_', ' '):<25} | {'N/A':<15} | {'N/A':<18} | {'N/A':<15} | {'NO LIMITS':<10}\n")
        
        report_file.write('\n')
        
        # --- Format and Save Full Consolidated Plot ---
        ax_deck.set_title(f'Temperature Profile for Deck: {deck_name}', fontsize=deck_plot_title_fontsize, **font_settings)
        ax_deck.set_xlabel('Time (minutes)', fontsize=deck_plot_label_fontsize, **font_settings, labelpad=15)
        ax_deck.set_ylabel('Temperature (°C)', fontsize=deck_plot_label_fontsize, **font_settings, labelpad=15)
        xticks = np.arange(0, time_minutes_original.max(), deck_plot_time_tick_interval)
        xticks = np.append(xticks, time_minutes_original.max())
        ax_deck.set_xticks(np.unique(xticks.astype(int)))
        ax_deck.tick_params(axis='x', labelrotation=90, labelsize=deck_plot_axis_fontsize)
        ax_deck.tick_params(axis='y', labelsize=deck_plot_axis_fontsize, pad=10)
        plt.setp(ax_deck.get_xticklabels(), fontweight="bold")
        plt.setp(ax_deck.get_yticklabels(), fontweight="bold")
        ax_deck.set_xlim(time_fine.min(), time_fine.max())
        deck_min, deck_max = np.min(all_interp_data_for_deck), np.max(all_interp_data_for_deck)
        if deck_name in manual_ylimits:
             ax_deck.set_ylim(manual_ylimits[deck_name])
             ax_deck.set_yticks(np.arange(manual_ylimits[deck_name][0], manual_ylimits[deck_name][1] + 1, y_tick_interval).astype(int))
        elif deck_plot_y_range != 'auto' and deck_min >= deck_plot_y_range[0] and deck_max <= deck_plot_y_range[1]:
            ax_deck.set_ylim(deck_plot_y_range)
            ax_deck.set_yticks(np.arange(deck_plot_y_range[0], deck_plot_y_range[1] + 1, y_tick_interval).astype(int))
        else:
            print(f"  WARNING: Data for deck '{deck_name}' exceeds default Y-limits. Auto-adjusting.")
            ylim_lower, ylim_upper = np.floor(deck_min / 5) * 5, np.ceil(deck_max / 5) * 5
            ax_deck.set_ylim(ylim_lower, ylim_upper)
            ax_deck.set_yticks(np.arange(ylim_lower, ylim_upper + 1, y_tick_interval).astype(int))
        leg = ax_deck.legend(loc='upper right', fontsize=deck_plot_legend_fontsize, frameon=True)
        leg.get_frame().set_facecolor(legend_face_color); leg.get_frame().set_edgecolor(legend_frame_color); leg.get_frame().set_alpha(1.0)
        [text.set_fontproperties(bold_font) for text in leg.get_texts()]
        for spine in ax_deck.spines.values(): spine.set_edgecolor('black'); spine.set_linewidth(1.5)
        fig_deck.tight_layout()
        clean_deck_name = "".join(c for c in deck_name if c.isalnum() or c in ('_', '-')).rstrip()
        fig_deck.savefig(os.path.join(output_folder_consolidated, f'Plot_Deck_{clean_deck_name}.png'), dpi=600)
        plt.close(fig_deck)

        # --- Format and Save "Last 2 Orbits" Consolidated Plot ---
        ax_deck_zoomed.set_title(f'Temperature Profile for Deck: {deck_name}', fontsize=deck_zoom_plot_title_fontsize, **font_settings)
        ax_deck_zoomed.set_xlabel('Time (minutes)', fontsize=deck_zoom_plot_label_fontsize, **font_settings, labelpad=15)
        ax_deck_zoomed.set_ylabel('Temperature (°C)', fontsize=deck_zoom_plot_label_fontsize, **font_settings, labelpad=15)
        start_tick = np.floor(deck_zoom_plot_x_range[0] / deck_zoom_plot_time_tick_interval) * deck_zoom_plot_time_tick_interval
        xticks_zoomed = np.arange(start_tick, deck_zoom_plot_x_range[1], deck_zoom_plot_time_tick_interval)
        xticks_zoomed = np.append(xticks_zoomed, deck_zoom_plot_x_range[1])
        ax_deck_zoomed.set_xticks(np.unique(xticks_zoomed.astype(int)))
        ax_deck_zoomed.tick_params(axis='x', labelrotation=90, labelsize=deck_zoom_plot_axis_fontsize)
        ax_deck_zoomed.tick_params(axis='y', labelsize=deck_zoom_plot_axis_fontsize, pad=10)
        plt.setp(ax_deck_zoomed.get_xticklabels(), fontweight="bold")
        plt.setp(ax_deck_zoomed.get_yticklabels(), fontweight="bold")
        ax_deck_zoomed.set_xlim(deck_zoom_plot_x_range)
        zoom_start_index_fine = np.where(time_fine >= deck_zoom_plot_x_range[0])[0][0]
        deck_zoomed_min, deck_zoomed_max = np.min(np.array(all_interp_data_for_deck)[:, zoom_start_index_fine:]), np.max(np.array(all_interp_data_for_deck)[:, zoom_start_index_fine:])
        ylim_lower, ylim_upper = np.floor(deck_zoomed_min / 5) * 5, np.ceil(deck_zoomed_max / 5) * 5
        ax_deck_zoomed.set_ylim(ylim_lower, ylim_upper)
        ax_deck_zoomed.set_yticks(np.arange(ylim_lower, ylim_upper + 1, y_tick_interval).astype(int))
        leg_zoomed = ax_deck_zoomed.legend(loc='upper right', fontsize=deck_zoom_plot_legend_fontsize, frameon=True)
        leg_zoomed.get_frame().set_facecolor(legend_face_color); leg_zoomed.get_frame().set_edgecolor(legend_frame_color); leg_zoomed.get_frame().set_alpha(1.0)
        [text.set_fontproperties(bold_font) for text in leg_zoomed.get_texts()]
        for spine in ax_deck_zoomed.spines.values(): spine.set_edgecolor('black'); spine.set_linewidth(1.5)
        fig_deck_zoomed.tight_layout()
        fig_deck_zoomed.savefig(os.path.join(output_folder_consolidated_zoomed, f'Plot_Deck_Zoomed_{clean_deck_name}.png'), dpi=600)
        plt.close(fig_deck_zoomed)

        # --- Format and Save "Last Orbit" Consolidated Plot ---
        ax_deck_last_orbit.set_title(f'Temperature Profile for Deck: {deck_name} - Last Orbit', fontsize=deck_last_orbit_plot_title_fontsize, **font_settings)
        ax_deck_last_orbit.set_xlabel('Time (minutes)', fontsize=deck_last_orbit_plot_label_fontsize, **font_settings, labelpad=15)
        ax_deck_last_orbit.set_ylabel('Temperature (°C)', fontsize=deck_last_orbit_plot_label_fontsize, **font_settings, labelpad=15)
        start_tick = np.floor(deck_last_orbit_plot_x_range[0] / deck_zoom_plot_time_tick_interval) * deck_zoom_plot_time_tick_interval
        xticks_zoomed = np.arange(start_tick, deck_last_orbit_plot_x_range[1], deck_zoom_plot_time_tick_interval)
        xticks_zoomed = np.append(xticks_zoomed, deck_last_orbit_plot_x_range[1])
        ax_deck_last_orbit.set_xticks(np.unique(xticks_zoomed.astype(int)))
        ax_deck_last_orbit.tick_params(axis='x', labelrotation=90, labelsize=deck_last_orbit_plot_axis_fontsize)
        ax_deck_last_orbit.tick_params(axis='y', labelsize=deck_last_orbit_plot_axis_fontsize, pad=10)
        plt.setp(ax_deck_last_orbit.get_xticklabels(), fontweight="bold")
        plt.setp(ax_deck_last_orbit.get_yticklabels(), fontweight="bold")
        ax_deck_last_orbit.set_xlim(deck_last_orbit_plot_x_range)
        last_orbit_start_index_fine = np.where(time_fine >= deck_last_orbit_plot_x_range[0])[0][0]
        deck_last_orbit_min, deck_last_orbit_max = np.min(np.array(all_interp_data_for_deck)[:, last_orbit_start_index_fine:]), np.max(np.array(all_interp_data_for_deck)[:, last_orbit_start_index_fine:])
        ylim_lower, ylim_upper = np.floor(deck_last_orbit_min / 5) * 5, np.ceil(deck_last_orbit_max / 5) * 5
        ax_deck_last_orbit.set_ylim(ylim_lower, ylim_upper)
        ax_deck_last_orbit.set_yticks(np.arange(ylim_lower, ylim_upper + 1, y_tick_interval).astype(int))
        leg_last_orbit = ax_deck_last_orbit.legend(loc='upper right', fontsize=deck_last_orbit_plot_legend_fontsize, frameon=True)
        leg_last_orbit.get_frame().set_facecolor(legend_face_color); leg_last_orbit.get_frame().set_edgecolor(legend_frame_color); leg_last_orbit.get_frame().set_alpha(1.0)
        [text.set_fontproperties(bold_font) for text in leg_last_orbit.get_texts()]
        for spine in ax_deck_last_orbit.spines.values(): spine.set_edgecolor('black'); spine.set_linewidth(1.5)
        fig_deck_last_orbit.tight_layout()
        fig_deck_last_orbit.savefig(os.path.join(output_folder_consolidated_last_orbit, f'Plot_Deck_Last_Orbit_{clean_deck_name}.png'), dpi=600)
        plt.close(fig_deck_last_orbit)

print('Finished generating consolidated plots and report.')

# --- 9. Completion ---
print('\n' + '=' * 85)
print('Processing complete.')
print(f'Report saved in: {report_filepath}')
print(f'All output generated in folder: {main_output_folder}')
print('=' * 85)
