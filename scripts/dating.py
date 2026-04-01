import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta




def plot_two_columns(df, col1, col2, start=None, end=None, title=None):
    """
    Plottet zwei Spalten eines DataFrames über den DatetimeIndex.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame mit DatetimeIndex
    col1 : str
        Name der ersten Spalte
    col2 : str
        Name der zweiten Spalte
    start : str or pd.Timestamp, optional
        Startzeit für das Slicing (z.B. '2012-06-01')
    end : str or pd.Timestamp, optional
        Endzeit für das Slicing (z.B. '2012-06-30')
    title : str, optional
        Titel des Plots
    """
    
    # Slice DataFrame nach Start/End, falls angegeben
    if start is not None and end is not None:
        df_plot = df[start:end]
    elif start is not None:
        df_plot = df[start:]
    elif end is not None:
        df_plot = df[:end]
    else:
        df_plot = df.copy()
    
    # Plot erstellen
    plt.figure(figsize=(12, 6))
    plt.plot(df_plot.index, df_plot[col1], label=col1)
    plt.plot(df_plot.index, df_plot[col2], label=col2)
    
    plt.xlabel('Datum')
    plt.ylabel('Wert')
    plt.title(title if title else f'{col1} und {col2} über Zeit')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()



def data_windows(df, start="20-04 00:00", end="28-04 00:00"):
    """
    Extrahiert Zeitfenster aus einem DataFrame anhand von Tag-Monat-Zeit-Stempeln (DD-MM HH:MM).
    Nutzt DatetimeIndex (MESS_DATUM) und behält die ursprüngliche Spalte.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame mit DatetimeIndex (MESS_DATUM)
    start : str
        Startzeitpunkt im Format 'DD-MM HH:MM'
    end : str
        Endzeitpunkt im Format 'DD-MM HH:MM'
    
    Returns
    -------
    List[pd.DataFrame]
        Liste der DataFrames, je eines pro gefundenem Zeitfenster
    """
    
    if df is None or df.empty:
        raise ValueError("DataFrame darf nicht None oder leer sein")
    
    # Stelle sicher, dass DatetimeIndex gesetzt ist
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame muss einen DatetimeIndex haben")
    

    # Start- und Endzeit als Zeitkomponente parsen (ohne Jahr)
    start_time = pd.to_datetime(start, format="%d-%m %H:%M").time()
    end_time   = pd.to_datetime(end, format="%d-%m %H:%M").time()
    
    windows = []

    # Alle Jahre durchlaufen
    years = df.index.year.unique()
    for year in years:
        # Start- und Endzeit in diesem Jahr
        start_dt = pd.Timestamp.combine(pd.Timestamp(f"{year}-01-01").date(), start_time)
        end_dt   = pd.Timestamp.combine(pd.Timestamp(f"{year}-01-01").date(), end_time)
        # Tages- und Monatskomponente anpassen
        start_dt = start_dt.replace(day=int(start[:2]), month=int(start[3:5]))
        end_dt   = end_dt.replace(day=int(end[:2]), month=int(end[3:5]))

        # Jahreswechsel berücksichtigen
        if start_dt <= end_dt:
            mask = (df.index >= start_dt) & (df.index <= end_dt)
        else:
            # Fenster über Jahresende
            end_dt_next = end_dt.replace(year=year + 1)
            mask = (df.index >= start_dt) | (df.index <= end_dt_next)
        
        window = df.loc[mask]
        if not window.empty:
            windows.append(window)

    return windows


#Chat_GPT
def plot_df(window, columns=["GS_10", "DS_10"]):
    df_to_plot = window.copy()
    
    plt.figure(figsize=(12, 3))
    
    for col in columns:
        series = pd.to_numeric(df_to_plot[col], errors='coerce')
        plt.plot(df_to_plot.index, series, label=col)
    
    plt.title("Window")
    plt.ylabel(columns if columns else "Wert")
    plt.xlabel("Zeit")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def data_sampler(start_window = "04-06 00:00", end_window = "12-06 00:00", start_time = "07:00", yearly_samples = 10, data = None, task = None, plot=False):
    if data is None: 
        print('Error, no irradiation data')
    if task is None: 
        print('Error, no Task is given. The duration of the task is required!')
    start_time = pd.to_datetime(start_time, format="%H:%M").time()
    duration = task.duration
    windows = data_windows(data, start_window, end_window)
    #print('lenwindow', len(windows))
    samples_df = []
    for window in windows: 
        if plot:
            plot_df(window)
        last_minute = window.index[-1]
        first_minute = window.index[0]
        #print('lastminute',last_minute)
        last_start = last_minute - timedelta(seconds=duration)
        rng = pd.date_range(start=first_minute, end=last_start, freq="min")  # jede Minute
        # Filtere nach der gewünschten Uhrzeit
        all_starts = rng[rng.time == start_time]
        all_ends = all_starts + timedelta(seconds=duration)

        relevant_data = window["GS_10"]
        for start, end in zip(all_starts,all_ends):
            sample_df = relevant_data[start:end]
            samples_df.append(sample_df)
            if plot:
                plt.plot(sample_df)
                plt.show()
                plot = False

    #print('Original sample_size:', len(samples_df))
    samples = []
    for sample_df in samples_df:

        sample = sample_df.to_numpy()
        time_seconds = (sample_df.index - sample_df.index[0]).total_seconds().to_numpy()
        try: 
            samples.append(np.float64([time_seconds,sample]))
        except:
            pass
            #print('One irradiation sample data is thrown out')
    #print('Cleaned Sample size: ', len(samples))
    samples = np.float64(samples).transpose(1,0,2)
    #print('cleaned sample shape: ', samples.shape)
    return [samples[0], samples[1]]

    



