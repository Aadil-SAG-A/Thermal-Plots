# Thermal-Plots
This code can be used to make plots using data extracted from thermal simulation using Thermal Desktop.
The 0th row in the data should contain header in the form: Time, s   Component 1   Component 2 ...... so on.
The file should in the form of .csv
The code will generate 1 folder with the time stamp, this folder includes 4 seperate sub folders. 1) All Component consolidated plots, 2) Zoomed consolidated plots, 3) Full Profile plots, 4) last 2 orbit plots for each components.
These plots will be named according to their location on their respective deck.
One result file is created in .txt form that compares the simulation result to the design and acceptance temperature of components and shows if the component passes or fails and if it can withstand the temperature profile of the satellite in the orbit.
