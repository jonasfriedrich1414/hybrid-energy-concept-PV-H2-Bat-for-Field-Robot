from typing import Optional
import numpy as np
from scipy.interpolate import interp1d

global resolution
resolution = 60 #seconds


class Battery():
    def __init__(self, capacity_kwh, capacity_kwh_max, power_max_charging, power_max_discharging, energy_density, charging_eff, discharging_eff, shut_down_frac):
        self.capacity_kwh = capacity_kwh #kwh
        self.capacity_kwh_max = capacity_kwh_max
        self.power_max_discharging = power_max_discharging #kW
        self.power_max_charging = power_max_charging #kW
        self.energy_density = energy_density #kWh/kg
        self.charging_eff = charging_eff
        self.discharging_eff = discharging_eff
        self.shut_down_frac = shut_down_frac

        self.capacity_kJ = self.capacity_kwh*3600
        self.capacity_kJ_max = self.capacity_kwh_max*3600
        self.weigth = self.capacity_kwh_max/self.energy_density
        if self.capacity_kJ_max != 0: self.fill_fraction = self.capacity_kJ/self.capacity_kJ_max
        else: self.fill_fraction = 0
        self.fill_fraction_timeseries = []
        self.is_on = True


    def charging_efficiency(self,power_charging):
        return self.charging_eff   # Change it!!!
    
    def discharging_efficiency(self,power_discharging):
        return self.discharging_eff
    
    def discharge(self, power):
        if self.fill_fraction <= self.shut_down_frac:
            self.is_on = False
            self.update()
            return 0
        else:
            if power >= self.power_max_discharging:
                print("Attention battery power overload, and no shutdown")
            self.capacity_kJ -= power*resolution/self.discharging_efficiency(power)
            self.update()
            return 1


    def charge(self, power):
        if power >= self.power_max_charging:
            power = self.power_max_charging

        if self.fill_fraction >= 1:
            self.update()
            return 1
        else:
            self.capacity_kJ += power*resolution*self.charging_efficiency(power)
            self.update()
            return 1


    def update(self):
        if self.capacity_kJ_max != 0: self.fill_fraction = self.capacity_kJ/self.capacity_kJ_max
        else: self.fill_fraction = 0
        self.capacity_kwh = self.capacity_kJ/3600
        if self.capacity_kJ > self.capacity_kJ_max: 
            self.capacity_kJ = self.capacity_kJ_max
            self.fill_fraction = 1.0
            #print('Battery full, energy lost')
        self.fill_fraction_timeseries.append(self.fill_fraction)
        return

        
class FC():
    def __init__(self, power_max, power_min, on_frac, off_frac, weight, efficiency, power_default):
        self.power_max = power_max #kW
        self.power_min = power_min  #kW
        self.weight = weight #kg
        self.on_frac = on_frac
        self.off_frac = off_frac
        self.is_on = False
        self.power_default = power_default   #Starting power on demand
        self.power = self.power_default
        self.power_timeseries = []
        self.efficiency_arr = np.load("../data/Fuel_cell_data/UI-Curve1000w.npy")

    def efficiency(self, power):
        return self.efficiency_arr[1,int(power*1000)]



class H2Tank():
    def __init__(self, capacity_kwh, energy_density):
        self.energy_density = energy_density
        self.weight = capacity_kwh/self.energy_density

        self.capacity_kwh = capacity_kwh

        self.capacity_kJ = self.capacity_kwh*3600
        self.capacity_kJ_max = self.capacity_kJ
        if self.capacity_kJ_max != 0: self.fill_fraction = self.capacity_kJ/self.capacity_kJ_max
        else: self.fill_fraction = 0
        self.fill_fraction_timeseries = []

        if capacity_kwh > 0: self.is_empty = False
        else: self.is_empty = True


    def update(self):
        if self.capacity_kJ_max != 0: self.fill_fraction = self.capacity_kJ/self.capacity_kJ_max
        else: self.fill_fraction = 0
        self.fill_fraction_timeseries.append(self.fill_fraction)
        self.capacity_kwh = self.capacity_kJ/3600
        if self.fill_fraction <= 0: 
            if not self.is_empty:
                pass
                #print(f"Hydrogen Tank is empty after {len(self.fill_fraction_timeseries)*resolution/3600} hours")
            self.is_empty = True



class PV():
    '''Assumptions
    1) PV panels are mounted horizontally!
        This is the same orientation, the data is given for. 
        In real life they would be mounted in a shape like a roof, for:
        decreasing reflection, better self cleaning, maximizing the shadow throwing area. 
        This better mounting angles are not taking into account, so that I don't have to track the suns movement!
        This Assumptions underestimates the real power!
    '''
    def __init__(self, surface, eff, conv_eff, power_density):
        self.surface = surface # m²
        if self.surface is None: 
            print('no surface!!!')
        self.efficiency = eff*conv_eff
        self.power_density = power_density  #kg/m²
        #self.power_density = 4
        self.weight = surface*self.power_density

        self.power_max = self.surface*self.efficiency*1000  #kWP

    def data2power(self, radiation):    #radiation must be in kW and on a horizontal surface
        return self.surface*self.efficiency*radiation


class Task():
    def __init__(self, 
            name: str = 'name',
            timeseries: dict = None, #kW
            daywork_only: bool = False,
            conditional: Optional["Task"] = None,   #Enter a Task class, if time information depend on another task
            duration: float = 36.0,        # hours
            ):
        ''
        self.timeseries = timeseries
        self.name = name
        self.daywork_only = daywork_only

        # If you put in a conditional class, some informations are taken from this class
        if conditional is None:
            self.duration = int(duration*3600)
        else: 
            self.duration = int(conditional.duration)

        self.time_base = np.arange(0,self.duration,resolution)

        # Repeat data a few times, because high resolution data is usually short.
        timeseries_power =  np.array(timeseries["amps"])*np.array(timeseries["volt"])/1000
        power_value = list(timeseries_power)
        time_base = list(timeseries["seconds"])
        for _ in range(10):
            power_value.extend(list(timeseries_power))
            time_base.extend(list(np.float32(timeseries["seconds"]) + time_base[-1]))


        # Stufige interpolation für die Punkte der neuen basis
        time_base_new = np.arange(0,np.max(time_base),resolution)
        split_idx = []
        for time_base_new_val in time_base_new[1:]:
            idx = np.searchsorted(time_base,time_base_new_val,'right') -1 
            time_base.insert(idx +1,time_base_new_val)
            power_value.insert(idx +1,power_value[idx])
            split_idx.append(idx)

        self.debug1 = [time_base.copy(),power_value.copy()]

        # Now get the time differences.
        time_base = np.float32(time_base)    # In diesem array sind neue interpolierte basis werte bereits drin
        power_value = np.float32(power_value)
        dT = time_base - np.roll(time_base,1)
        dT = dT[1:]
        power_value = power_value[1:]
        time_base = time_base[1:]
        
        # Auf neue Basis übertragen, integralerhaltend
        energy = power_value*dT
        power_value_new = [np.sum(energy[0:split_idx[0]])/resolution]
        for i in range(len(split_idx)):
            if split_idx[i] == split_idx[-1]: break
            start = split_idx[i]
            end = split_idx[i+1]
            power_value_new.append(np.sum(energy[start:end])/resolution)
        time_base_new = time_base_new[:-1]

        self.debug2 = [time_base_new.copy(), power_value_new.copy()]

        # Put power timeseries into the length of duration. 
        repetitions = int(self.duration // time_base_new[-1] + 1)
        power_value_new = np.array(power_value_new)
        if repetitions <= 1: 
            self.power_timeseries = power_value_new[(self.time_base <= int(self.duration))]
        else: 
            power_value_repeated = np.tile(power_value_new, repetitions)
            self.power_timeseries = power_value_repeated[:len(self.time_base)]



        





            


    


