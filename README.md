Satellite Thermal Analysis Automation Tool
Overview
This Python script provides an automated solution for post-processing satellite thermal simulation data. It is designed to read raw CSV output from thermal analysis software (like Thermal Desktop), compare the temperature profiles against predefined acceptance limits, and generate a comprehensive set of plots and a summary report.

The primary goal of this tool is to drastically reduce the manual effort required for thermal analysis data review, ensuring consistency, accuracy, and professional-quality outputs for reports and presentations. The entire process is controlled through a simple config.ini file, making it accessible to engineers who may not have a background in programming.

Features
Automated Plot Generation: Creates four types of high-quality plots for thorough analysis:

Full Profile Plots: Individual temperature plots for every component over the entire simulation period.

Zoomed Profile Plots: Individual plots focusing on a specific time range (e.g., the last two orbits) with max/min annotations.

Consolidated Deck Plots: A single plot for each deck, showing all its components' temperature profiles together for easy comparison.

Consolidated Zoomed Plots: A zoomed-in version of the consolidated deck plots.

Automatic Report Generation: Produces a clean, timestamped thermal_report.txt file containing a deck-by-deck summary table with temperature ranges, margins, and a clear PASS/FAIL status for each component.

Configuration-Driven: All settings, including file paths, plot aesthetics (fonts, colors, line styles), and component filtering, are controlled via an easy-to-edit config.ini file. No code changes are needed for routine analysis.

Smart Data Handling: Intelligently parses various CSV formats and cleans the data to handle potential issues like missing values or non-numeric entries.

Professional Aesthetics: All plots are generated with a focus on readability, featuring bold text, clear labels, prominent axis lines, and opaque legends.

Prerequisites
Before running this script, you will need to have Python installed on your system. The recommended way to get Python and all the necessary libraries is by installing the Anaconda Distribution.

Install Anaconda: Download and install the Anaconda Distribution from the official website: https://www.anaconda.com/download

Required Libraries: If you are not using Anaconda, ensure you have the following Python libraries installed:

pandas

numpy

matplotlib

scipy

How to Use
Place Your Files: Put your thermal simulation data file (e.g., Results_All graphs (1).xls.csv) in the same folder as the thermal_analyzer.py script.

Configure the config.ini file:

Open the config.ini file in a text editor.

Under the [FILES] section, make sure simulation_data_filename matches the name of your data file.

The script will automatically create a component_limits.csv file on its first run. Open this file and edit the placeholder Acceptance_Min and Acceptance_Max values with the correct temperature limits for your components.

Adjust any other settings in config.ini as needed (e.g., fonts, colors, or components to exclude).

Run the Script:

Open a terminal or Anaconda Prompt.

Navigate to the project folder.

Run the script using the command:

python thermal_analyzer.py

Check the Output: A new folder named Thermal_Analysis_Output_[Date_Time] will be created. Inside, you will find all the generated plots and the summary report, neatly organized into subfolders.

Configuration (config.ini)
This file allows you to customize the script's behavior without editing the code.

[FILES]: Set the names of your input data and limits files.

[SETTINGS]: Control high-level behavior, like toggling the generation of individual plots or setting the time range for zoomed plots.

[COMPONENT_FILTERING]: Exclude specific components from the consolidated plots by listing their full names, separated by commas.

[FONTS]: Control all font sizes for titles, labels, and axis numbers.

[COLORS_AND_STYLES]: Customize the colors and line styles for plots and legends.

[AXIS_TICKS]: Define the time intervals for the x-axis and the default range for the y-axis.

Generated Output
The script will create a main output folder with the following structure:

Thermal_Analysis_Output_YYYY-MM-DD_HH-MM-SS/
├── Component_Plots_Consolidated_Decks/
│   └── Plot_Deck_VD01.png
│   └── ...
├── Component_Plots_Consolidated_Decks_Zoomed/
│   └── Plot_Deck_Zoomed_VD01.png
│   └── ...
├── Component_Plots_Full_Profile/
│   └── Plot_Full_VD01_FOG.png
│   └── ...
├── Component_Plots_Zoomed_Profile/
│   └── Plot_Zoomed_VD01_FOG.png
│   └── ...
└── Report/
    └── thermal_report.txt
