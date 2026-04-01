import numpy as np
import json
import os

dic = {
    #directories
    "save_dir": "Results",
    "results_name": "test",
    "solar_data_dir": "../data/DWD_10min/10minutenwerte_SOLAR_01078_20100101_20191231_hist/produkt_zehn_min_sd_20100101_20191231_01078.txt",
    # simulation parameters
    "resolution": 60, #seconds
    "bat_size_range": np.arange(1,6,1).tolist(),     #kwh battery capacity
    "h2_size_range": (np.arange(0,16*4+1,16)).tolist(),      #kwh h2 tank capacity
    "pv_size_range": (np.arange(0,3,1)*2.688).tolist(),      # Define ranges for simulation
    "refill_time": 7*24.0,                   # hours         # should be variable later
    "month": ["01-06 00:00","30-06 00:00"],
    "start_time": "08:00",
    # h2 device properties
    "fc_weight": 4.4,                           #kg
    "fc_efficiency": None,    #not used!, comes from numpy array! 
    "h2_tank_energy_density": 2.2,            #kWh/kg
    "fc_power_min": 0.0,
    "fc_power_max": 1.0,
    # pv device properties
    "pv_power_density": 7.2/(1.197*2.246) + 0.765,                    #kg/m² module + kg/m² Unterkonstruktuion (1m für 1m²)
    "pv_efficiency": 0.1934,
    "charger_efficiency": 0.9,              # device between pv-module and battery for DC-DC conversion and mpp tracking of the pv module
    "charger_weight": 0.65,
    "vertical_support_weight": 6*0.765,
    # battery device properties
    "bat_energy_density": 0.896/5.6,            #kwh/kg
    "bat_power_max_charging": 999,
    "bat_power_max_discharging": 999,
    "bat_charging_efficiency": 0.9, 
    "bat_discharging_efficiency": 0.9,
    # regulation fuel cell: 
    "fc_on_fraction": 0.1,
    "fc_off_fraction": 0.2,
    "night_fraction": 0.9,
    "fc_power_default": 0.0,
    "sunrise_fraction": 0.3,
    "nighttime_offset": 3600,
    "res_mean_time": 300,
    # regulation battery
    "shut_down_fraction": 0.05,
    "back_on_after_shut_down": 0.15,
    # other
    "weight_limit": 150,

}


# Save config for usement (overwriting!!!)
with open("config.json", "w", encoding="utf-8") as datei:
    json.dump(dic, datei, ensure_ascii=False, indent=4)  # schön formatiert