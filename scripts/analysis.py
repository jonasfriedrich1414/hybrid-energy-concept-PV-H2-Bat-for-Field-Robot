import json
import numpy as np
import matplotlib.pyplot as plt
import os


with open("config.json", "r", encoding="utf-8") as datei:
    config = json.load(datei)

refill_time = config["refill_time"]  # hours         # should be variable later
month = config["month"]
start_time = config["start_time"]

path = os.path.join(config["save_dir"],config["results_name"]+"_results_5D.npy")
results = np.load(path)


# Ad the weight of the 
# results[:,0] = np.where(results[:,4] == 0, results[:,0], results[:,0] + config["fc_weight"])
# results[:,0] = np.where(results[:,2] == 0, results[:,0], results[:,0] + config["charger_weight"] + config["vertical_support_weight"])


pareto_front = []
for point in results:
    lighter = np.where(results[:,0] < point[0], 1, 0)   # If anything is lighter
    reduced_auslastung = lighter*results[:,1]
    if np.max(reduced_auslastung) < point[1]:
        pareto_front.append(point)
pareto_front = np.array(pareto_front)
args = np.argsort(pareto_front[:,0])
pareto_front = pareto_front[args]


pareto_front_no_h2 = []
results_no_h2 = results[(results[:,4] == 0)]
if len(results_no_h2) != 0: 
    for point in results_no_h2:
        lighter = np.where(results_no_h2[:,0] < point[0], 1, 0)   # If anything is lighter
        reduced_auslastung = lighter*results_no_h2[:,1]
        if np.max(reduced_auslastung) < point[1]:
            pareto_front_no_h2.append(point)
    pareto_front_no_h2 = np.array(pareto_front_no_h2)
    args = np.argsort(pareto_front_no_h2[:,0])
    pareto_front_no_h2 = pareto_front_no_h2[args]
    plot_no_h2 = True
else: plot_no_h2 = False

pareto_front_no_pv = []
results_no_pv = results[(results[:,2] == 0)]
if len(results_no_pv) != 0:
    for point in results_no_pv:
        lighter = np.where(results_no_pv[:,0] < point[0], 1, 0)   # If anything is lighter
        reduced_auslastung = lighter*results_no_pv[:,1]
        if np.max(reduced_auslastung) < point[1]:
            pareto_front_no_pv.append(point)
    pareto_front_no_pv = np.array(pareto_front_no_pv)
    args = np.argsort(pareto_front_no_pv[:,0])
    pareto_front_no_pv = pareto_front_no_pv[args]
    plot_no_pv = True
else: plot_no_pv = False


default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
plt.figure(figsize=(6,4))
plt.scatter(results[:,0],results[:,1],s=2,color=default_colors[2]) # Auslastung
plt.plot(pareto_front[:,0],pareto_front[:,1],label='Pareto Front PV, H2, Bat', color = default_colors[2]) # Auslastung
if plot_no_h2:
    plt.plot(pareto_front_no_h2[:,0],pareto_front_no_h2[:,1], label="Pareto Front PV, Bat", color = default_colors[1]) # Auslastung
    plt.scatter(results_no_h2[:,0],results_no_h2[:,1],s=2,color = default_colors[1])
if plot_no_pv:
    plt.plot(pareto_front_no_pv[:,0],pareto_front_no_pv[:,1], label= "Pareto Front H2, Bat", color = default_colors[3]) # Auslastung
    plt.scatter(results_no_pv[:,0],results_no_pv[:,1],s=2,color=default_colors[3])
plt.text(1,0.8,f'Zeitfenster: \n{month[0][:5]} bis {month[1][:5]} \nTankintervall: \n{refill_time/24} Tage')
#plt.title('Alle Simulationspunkte und bedingte Pareto Fronten')
plt.xlabel('Gewicht [kg]')
plt.ylabel('Auslastung')
plt.ylim(-0.05,1.05)
plt.xlim(0)
plt.grid(True)
plt.legend(loc="lower right")
path = os.path.join(config["save_dir"],config["results_name"]+"_pareto-front.pdf")
plt.savefig(path, bbox_inches="tight")



fig, ax1 = plt.subplots(figsize=(10, 6))

# ---------- linke Achse: Auslastung ----------
l1 = ax1.scatter(
    pareto_front[:,0],
    pareto_front[:,1],
    s = 10,
    label="Auslastung",
)
ax1.set_xlabel("System Weight Pareto")
ax1.set_ylabel("Auslastung")
ax1.grid(True)

# ---------- rechte Achse 1: BAT + H2 (kWh) ----------
ax2 = ax1.twinx()
l2 = ax2.scatter(
    pareto_front[:,0],
    pareto_front[:,3],
    s = 10,
    color="purple",
    label="Batteriegröße (kWh)"
)
ax2.set_ylabel("Bat Speichergröße (kWh)")

# ---------- rechte Achse 2: H2 (kWh) ----------
ax3 = ax1.twinx()
ax3.spines["right"].set_position(("outward", 60))
l3 = ax3.scatter(
    pareto_front[:,0],
    pareto_front[:,4],
    s = 10,
    color="orange",
    label="H2-Größe (kWh)"
)
ax3.set_ylabel("H2 Speichergröße (kWh)")

# ---------- rechte Achse 3: PV (m²) ----------
ax4 = ax1.twinx()
ax4.spines["right"].set_position(("outward", 120))
l4 = ax4.scatter(
    pareto_front[:,0],
    pareto_front[:,2],
    s = 10,
    color="black",
    label="PV-Fläche (m²)"
)
ax4.set_ylabel("PV-Fläche (m²)")

# ---------- gemeinsame Legende ----------
lines = [l1, l2, l3, l4]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc="best")

plt.title("Pareto-optimale Systemauslegung")
plt.tight_layout()

path = os.path.join(config["save_dir"],config["results_name"]+"_pareto-front2.pdf")
plt.savefig(path, bbox_inches="tight")



#plt.show()

# default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

# plt.plot(time_base/3600,energy_demand, color=default_colors[0],label='energy demand')
# plt.plot(time_base/3600,irrad_m2[0], color=default_colors[1], label='irradiation / m²')
# plt.plot(time_base/3600,residual_last_list, color=default_colors[2], label='residual last')
# #plt.plot(time_base/3600,power_balance_list, color=default_colors[3], label='power balance')
# #plt.plot(time_base/3600,bat.fill_fraction_timeseries, color=default_colors[4], label='battery fill fraction')
# #plt.plot(time_base/3600,fc.power_timeseries, color=default_colors[5], label='fuel cell power')
# plt.title('Irradiation data sample and energy demand overlay')
# plt.ylabel('Power [kW] and [kW/m²]')
# #plt.ylim(-0.5,1.5)
# #plt.xlim(140,150)
# plt.xlabel(f'Time [h], res {resolution}s')
# plt.legend()
# plt.show()