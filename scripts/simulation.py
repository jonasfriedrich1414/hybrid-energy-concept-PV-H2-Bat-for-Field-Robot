import pandas as pd
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from dating import plot_df, plot_two_columns, data_sampler
from objects import Task, PV, FC, Battery, H2Tank
import os
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

with open("config.json", "r", encoding="utf-8") as datei:
    config = json.load(datei)

# create save_dir:
os.makedirs(config["save_dir"], exist_ok=True)

# Save copy of config in save_dir: 
path = os.path.join(config["save_dir"],config["results_name"]+"_config.json")
with open(path, "w", encoding="utf-8") as datei:
    json.dump(config, datei, ensure_ascii=False, indent=4)  # schön formatiert


# Datei einlesen
file_path = config["solar_data_dir"]

# Zeilen einlesen und 'eor' entfernen
with open(file_path, 'r') as f:
    lines = f.readlines()

# Header aus der ersten Zeile extrahieren
header = lines[0].strip().replace(' ', '').split(';')

# Daten aufbereiten
data = []
for line in lines[1:]:
    line = line.replace('eor', '').strip()
    if line:
        row = [x.strip() for x in line.split(';')]
        data.append(row)

# DataFrame erstellen
df = pd.DataFrame(data, columns=header)

# Numerische Spalten umwandeln
numeric_cols = ['STATIONS_ID', 'QN', 'DS_10', 'GS_10', 'SD_10', 'LS_10']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# -999 als NaN behandeln
df.replace(-999, pd.NA, inplace=True)

# MESS_DATUM in datetime umwandeln
df['MESS_DATUM'] = pd.to_datetime(df['MESS_DATUM'], format='%Y%m%d%H%M')
df['DS_10'] *= 10000/3600*6 /1000
df['GS_10'] *= 10000/3600*6 /1000  #J/m² per 10 min

print(df.head())
df = df.set_index('MESS_DATUM')
# Gesamten Zeitraum anzeigen
start_gesamt = df.index.min()
end_gesamt = df.index.max()
print(f"Gesamter Zeitraum: {start_gesamt} bis {end_gesamt}\n")


# # Prüfen, ob die Zeiten korrekt sind
# print(df.index[:10])
# print(df.index.freq)  # sollte None sein, kann aber später auf 10T gesetzt werden

# # Prüfen auf doppelte oder fehlende Zeitstempel
# print("Duplikate:", df.index.duplicated().sum())
# print("Monoton steigend:", df.index.is_monotonic_increasing)

# plot_two_columns(df, 'DS_10', 'GS_10', start='2014-05-01', end='2014-05-5', title='Solar data example plot')









bat_size_range = np.array(config["bat_size_range"]) #kwh battery capacity
h2_size_range = np.array(config["h2_size_range"])  #kwh h2 tank capacity
pv_size_range = np.array(config["pv_size_range"])     # Define ranges for simulation

refill_time = config["refill_time"]  # hours         # should be variable later
month = config["month"]
start_time = config["start_time"]
resolution = config["resolution"]


print(bat_size_range, h2_size_range, pv_size_range)
print("resolution: ", resolution, "seconds")





import json
with open("../data/DAVEGI_measurement/timeseries_driving.json", "r", encoding="utf-8") as datei:
    timeseries_driving = json.load(datei)
with open("../data/DAVEGI_measurement/timeseries_spraying.json", "r", encoding="utf-8") as datei:
    timeseries_spraying = json.load(datei)
with open("../data/DAVEGI_measurement/timeseries_hands.json", "r", encoding="utf-8") as datei:
    timeseries_hands = json.load(datei)


hands = Task('hands', timeseries_hands, daywork_only=False, duration=refill_time)
driving = Task('driving', timeseries_driving, daywork_only=False, conditional=hands)

time_base = np.float64(hands.time_base)
energy_demand = hands.power_timeseries + driving.power_timeseries + hands.power_timeseries
time, irrad_m2_raw = data_sampler(start_window = month[0], end_window = month[1], start_time = start_time,task=hands,plot=False,data=df)    # array, but wrong base
print('shapes output data_sampler: ',time.shape, irrad_m2_raw.shape)
print('maxvalues: ', np.max(time), np.max(irrad_m2_raw), np.max(time_base))

irrad_m2 = []
for i in range(len(irrad_m2_raw)):
    irrad_m2.append(np.interp(time_base,time[i],irrad_m2_raw[i]))
irrad_m2_2D = np.float32(irrad_m2)
np.random.seed(42)
# np.random.shuffle(irrad_m2_2D)
print('Irradiation shape after interp: ', irrad_m2_2D.shape)
print('maxvalue after interpolation: ', np.max(irrad_m2_2D))


print('max leistung driving: ')
print(np.max(np.array(timeseries_driving['amps']))*50)

# plt.plot(driving.debug1[0],driving.debug1[1])
# plt.show()
# plt.plot(driving.debug2[0],driving.debug2[1])
# plt.show()

plt.figure(figsize=(6,4))
plt.plot(timeseries_hands['seconds'], 1000*np.array(timeseries_hands['volt'])*np.array(timeseries_hands['amps'])/1000)
#plt.title('hands measurement data')
plt.ylabel('Leistung [W]')
plt.xlabel('Zeit [s]')
plt.tight_layout()
plt.savefig('Messdaten_Hands.pdf')
# plt.show()
print(np.mean(np.array(timeseries_driving['amps'])/1000*np.array(timeseries_driving['volt'])))
# plt.plot(timeseries_driving['seconds'],np.array(timeseries_driving['amps'])/1000*np.array(timeseries_driving['volt']))
# plt.title('driving measurement data')
# plt.ylabel('Power [kW]')
# plt.xlabel('time [s]')
# plt.show()

print('Leistungs Mittlwerte')
print(np.max(np.array(timeseries_hands['amps'])*24.1))
print(np.mean(driving.power_timeseries))
print(np.mean(driving.power_timeseries)/50)
print(np.mean(hands.power_timeseries))
path = os.path.join(config["save_dir"],config["results_name"]+"_energy-demand.pdf")
plt.scatter(hands.time_base[:3600 // resolution],hands.power_timeseries[:3600 // resolution],s=2,label="robot hands")
plt.scatter(driving.time_base[:3600 // resolution],driving.power_timeseries[:3600 // resolution],s=2,label="device driving")
plt.title('interpolated data energy demand (small range)')
plt.ylabel('Power [kW]')
plt.xlabel(f'time [s], res: {resolution}s')
plt.legend()
plt.ylim(0)
plt.savefig(path, bbox_inches="tight")
#plt.show()



# plt.plot(time_base/3600,energy_demand)
# plt.title('interpolated data (large range)')
# plt.ylabel('Power [kW]')
# plt.xlabel(f'time [h], res: {resolution}s')
# plt.ylim(0)
# plt.show()


# plt.plot(time_base/3600,energy_demand)
# plt.plot(time_base/3600,irrad_m2[0])
# plt.title('Irradiation data sample and energy demand overlay')
# plt.ylabel('Power [kW] and [kW/m²]')
# plt.xlabel(f'Time [h], res {resolution}s')
# plt.show()



results = []


for bat_idx, bat_size in enumerate(bat_size_range):
    for h2_idx, h2_size in enumerate(h2_size_range):
        print(bat_idx, h2_idx, 'von', len(bat_size_range),len(h2_size_range))
        for pv_idx, pv_size in enumerate(pv_size_range):

            pv_module = PV(surface=pv_size, conv_eff=config["charger_efficiency"], eff=config["pv_efficiency"],power_density=config["pv_power_density"])
            #print(pv_size, pv_module.weight)
            auslastung_list = []
            for irrad_m2_1D in irrad_m2_2D[:10]:
                
                bat = Battery(capacity_kwh=bat_size, capacity_kwh_max=bat_size, power_max_charging=config["bat_power_max_charging"],
                              shut_down_frac=config["shut_down_fraction"], power_max_discharging=config["bat_power_max_discharging"],
                              energy_density=config["bat_energy_density"], charging_eff=config["bat_charging_efficiency"],
                              discharging_eff=config["bat_discharging_efficiency"])
                fc = FC(power_min=config["fc_power_min"], power_max=config["fc_power_max"], on_frac=config["fc_on_fraction"],
                         off_frac=config["fc_off_fraction"], weight=config["fc_weight"], efficiency=config["fc_efficiency"],
                         power_default=config["fc_power_default"])
                tank = H2Tank(capacity_kwh = h2_size, energy_density=config["h2_tank_energy_density"])


                #print(fc.efficiency(0.0), fc.efficiency(0),fc.efficiency(0.1),fc.efficiency(0.5),fc.efficiency(0.99))



                if pv_module.weight + bat.weigth + tank.weight > config["weight_limit"]:
                    auslastung_list.append(-1)
                    break

                time_str = config["start_time"]
                second = int(time_str.split(":")[0]) * 3600 + int(time_str.split(":")[1]) * 60

                residual_last_list = np.zeros(len(time_base))
                power_balance_list = np.zeros(len(time_base))
                working_list = np.ones(len(time_base))
                debug_list = []
                problems = []
                sunrise = np.nan
                sunset = np.nan
                nighttime_list = [False,True]
                for step, data in enumerate(zip(irrad_m2_1D,energy_demand)):  
                    problem_flag = False

                    irrad, last = data

                    if irrad < 0.01: nighttime = True
                    else: nighttime = False

                    nighttime_list.append(nighttime)
                    if all(nighttime_list[-20:-10]) and not any(nighttime_list[-10:]):
                        sunrise = second - resolution*10 + config['nighttime_offset']
                        #print('sunrise',sunrise/3600, 'time', time_base[step]/3600)
                    if not any(nighttime_list[-20:-10]) and all(nighttime_list[-10:]):
                        sunset = second - resolution*10 - config['nighttime_offset']
                        #print('sunset',sunset/3600, 'time', time_base[step]/3600)

                    pv_supply = irrad*pv_module.efficiency*pv_module.surface
                    
                    

                    if bat.fill_fraction >= config["back_on_after_shut_down"]:  # turn device on after shut down
                        bat.is_on = True

                    residual_last = last - pv_supply
                    residual_last_list[step] = residual_last            
                
                    if bat.is_on: 
                        # Running Fuel Cell and discharging Tank
                        if fc.is_on:
                            if tank.is_empty:
                                fc.is_on = False
                                fc.power_timeseries.append(0)
                                power_balance = residual_last
                            else: 
                                fc.power_timeseries.append(fc.power)
                                power_balance = residual_last - fc.power
                                tank.capacity_kJ -= fc.power*resolution/fc.efficiency(fc.power)
                        else: 
                            fc.power_timeseries.append(0)
                            power_balance = residual_last
                        tank.update()
                        power_balance_list[step] = power_balance

                        
                        # Running Battery
                        if power_balance > 0:
                            working_list[step] = bat.discharge(power_balance)
                        elif power_balance <= 0: 
                            working_list[step] = bat.charge(-power_balance)
                        else: problem_flag = True

                        elements = config["res_mean_time"] // resolution  #take the last 30 minutes for power regulation
                        res_mean = np.mean(residual_last_list[step-elements-1:step-1])  
                        if np.isnan(res_mean): 
                            res_mean = fc.power_default 


                        if pv_size != 0:  # dann wird nur durch PV geladen!

                            # Power regulation Fuel Cell at night time
                            if not np.isnan(sunrise) and not np.isnan(sunset) and (nighttime or second < sunrise or (not np.isnan(sunset) and second > sunset)) and bat.fill_fraction <= config["night_fraction"] and bat.fill_fraction > fc.on_frac and not tank.is_empty and res_mean >= 0: #nighttime
                                
                                fc.is_on = True

                                debug_list.append(0.2)

                                    
                                if second >= sunrise:
                                    seconds_till_sunrise = 24.0*3600 - second + sunrise                 
                                elif second < sunrise:
                                    seconds_till_sunrise = sunrise - second
                                else: 
                                    problem_flag = True
                                    print("happend again")
                                    
                                energy_till_sunrise = res_mean * seconds_till_sunrise #kJ
                                energy_from_battery = max(0,bat.discharging_eff*(bat.fill_fraction - config["sunrise_fraction"])*bat.capacity_kJ_max)
                                energy_from_fc = energy_till_sunrise - energy_from_battery
                                power_from_fc = energy_from_fc/seconds_till_sunrise + 0.005
                                fc.power += (power_from_fc - fc.power)/600*resolution
                                

                                
                                if fc.power <= fc.power_min:
                                    fc.power = fc.power_min#0.0
                                if fc.power >= fc.power_max:
                                    fc.power = fc.power_max
                                
                                    
                            # Power regulation Fuel Cell at day time
                            else:
                                if not problem_flag:
                                    debug_list.append(1)
                                if bat.fill_fraction <= fc.on_frac and not tank.is_empty:
                                    fc.is_on = True
                                if bat.fill_fraction >= fc.off_frac: 
                                    fc.is_on = False

                                if fc.is_on:
                                    fc.power += (res_mean + 0.005 - fc.power)/600*resolution#kW  10% pro minute
                                    if fc.power <= fc.power_min:
                                        fc.power = fc.power_min
                                    if fc.power >= fc.power_max:
                                        fc.power = fc.power_max
                                else:
                                    fc.power = fc.power_default

                        else: # Nur H2 nutzung!
                            fc.is_on = True
                            if bat.fill_fraction < 0.4: 
                                res_mean += 0.03
                            elif bat.fill_fraction > 0.5:
                                res_mean -= 0.03

                            fc.power += (res_mean - fc.power)/600*resolution#kW  10% pro minute
                            if fc.power <= fc.power_min:
                                fc.power = fc.power_min
                            if fc.power >= fc.power_max:
                                fc.power = fc.power_max
                            


                            
                    else: 
                        if not problem_flag:
                            debug_list.append(-0.5)
                        fc.power_timeseries.append(0)
                        tank.update()
                        bat.charge(pv_supply)
                        working_list[step] = 0

                    second += resolution
                    if second >= 24*3600: 
                        second -= 24*3600


                    if np.isnan(fc.power):
                        #problem_flag = True
                        print("problem at: ", time_base[step]/3600)
                        problem_flag = True

                    if problem_flag: print(f'proplem in step {step}')


                auslastung = np.sum(working_list)/len(working_list)
                #print(f'auslastung single sample: {auslastung}')
                auslastung_list.append(auslastung)



            auslastung_list = np.array(auslastung_list)
            mean_auslastung = np.mean(auslastung_list)
            #print(f'mean auslastung: {mean_auslastung}')
            system_weight = bat.weigth + pv_module.weight + tank.weight 
            if pv_module.weight > 0:
                system_weight += config["vertical_support_weight"] + config["charger_weight"]
            if tank.weight > 0: 
                system_weight += config["fc_weight"]

            results.append(np.array([system_weight,mean_auslastung,pv_size,bat_size,h2_size]))

# results = np.array(results)
# path = os.path.join(config["save_dir"],config["results_name"]+"_results_5D.npy")
# np.save(path,results)

results = np.array(results)
path = os.path.join(config["save_dir"], config["results_name"] + "_results_5D.npy")

# if os.path.exists(path):
#     existing = np.load(path)

#     print("Alt:", existing.shape)
#     print("Neu:", results.shape)

#     results = np.concatenate([existing, results], axis=0)

np.save(path, results)
print("Gesamt:", results.shape)

# path = "monthlyH2PV.npy"
# if os.path.exists(path):
#     arr = np.load(path)
#     arr = np.vstack([arr,np.array(results[:,1])])
# else: arr = np.array(results[:,1])
# np.save(path, results[:,1])


plt.clf()
default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

plt.figure(figsize=(7,5))
#plt.plot(time_base/3600,energy_demanlenwindd, color=default_colors[0],label='energy demand')
plt.plot(time_base/3600,irrad_m2_1D, color=default_colors[1], label='Globalstrahlung [kW/m²]')
plt.plot(time_base/3600,residual_last_list, color=default_colors[2], label='Residuallast [kW]')
#plt.plot(time_base/3600,power_balance_list, color=default_colors[3], label='power balance')
plt.plot(time_base/3600,tank.fill_fraction_timeseries, color=default_colors[6], label='H2-Tank Füllstand')
plt.plot(time_base/3600,bat.fill_fraction_timeseries, color=default_colors[4], label='Batterie Füllstand')
#plt.plot(time_base/3600,working_list, color = default_colors[7], label='device on off')
plt.plot(time_base/3600,fc.power_timeseries, color=default_colors[5], label='FC-Leistung [kW]')
#plt.plot(time_base/3600,debug_list, color = default_colors[8], label='debug list')
#plt.title('Irradiation data sample and energy demand overlay')
plt.ylabel('Leistung [kW] Einstrahlung [kW/m²] und Füllstände')
#plt.plot([0,np.max(time_base)/3600],[config['sunrise_fraction'],config['sunrise_fraction']])
#plt.plot([24,24],[0,1])
#plt.ylim(0,0.6)
#plt.xlim(0,72)
plt.xlabel(f'Zeit [h], res {resolution}s')
plt.legend()
plt.grid(True)
path = os.path.join(config["save_dir"],config["results_name"]+"_last-iteration.pdf")
plt.savefig(path, bbox_inches="tight")
#plt.show()