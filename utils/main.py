import os
import os.path as path
import csv
import pandas as pd
import time
import datetime
import matplotlib.pyplot as plt

pd.set_option("display.max_rows", 999)
pd.set_option("display.max_columns", 999)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", None)


fieldnames = [
    'full_event',
    'arg1',
    'arg2',
    'arg3',
    'arg4',
    'arg5',
    'arg6',
    'arg7',
    'arg8',
    'arg9',
    'arg10',
]
arena_zones =  [
    "Blade's Edge Arena",
    'Nagrand Arena',
    'Ruins of Lordaeron',
]
my_team = [
    "Drogah-Grobbulus",
    "Veldsar-Grobbulus",
]

def convert_unix_time(date_str,time_str):
    """Convert string date and string time to UNIX timestamp"""
    time_unix_sec = time.mktime(datetime.datetime.strptime(date_str + ' ' + time_str,"%m/%d/%y %H:%M:%S.%f").timetuple())
    return(time_unix_sec)

def determine_win(player_alive):
    """Determines winner of match based on player living status"""  
    if any([player_alive[player] for player in my_team if player in player_alive]):
        return("Win")
    else:
        return("Loss")
    
def determine_match_size(player_alive):
    """Determines match size based on player alive dict"""
    if len(player_alive) <= 4:
        return("2v2")
    elif len(player_alive) <= 6:
        return("3v3")
    elif len(player_alive) <= 10:
        return("5v5")
    else:
        return("invalid")
    

# scan through all logs
print("Start")
df = pd.DataFrame(columns=['start_unix_sec','date','start_timestamp','end_timestamp','match_number','duration','arena_zone','match_size','outcome','players','player_deaths','life_tap_count'])
df = df.astype({'start_unix_sec': 'int32'})
df = df.set_index('start_unix_sec')
directory = path.abspath(path.join(__file__ ,"../../logs/"))
match_number = 0
for filename in os.listdir(directory):
    file_path = os.path.join(directory, filename)
    # extract year
    year = filename.split('-',2)[1].split('_',2)[0][4:6]
    print(file_path)
    arena_active = False
    start_time = None
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile,fieldnames=fieldnames,delimiter=',',restkey='misc')
        
        for row in reader:
            # parse event
            split_out = row['full_event'].split(' ',4)
            date = split_out[0] + "/" + year
            timestamp = split_out[1]
            event = split_out[3]
            if arena_active:
                if event == "ZONE_CHANGE" and (row['arg2'] not in arena_zones):
                    # arena ended => write data and reset
                    end_time = convert_unix_time(date,timestamp)
                    df.loc[start_time,'end_timestamp'] = timestamp
                    duration = end_time - start_time
                    df.loc[start_time,'duration'] = duration
                    df.loc[start_time,'outcome'] = determine_win(player_alive)
                    df.loc[start_time,'players'] = [player_alive.keys()]
                    df.loc[start_time,'match_size'] = determine_match_size(player_alive)
                    df.loc[start_time,'player_deaths'] = [player for player in player_alive.keys() if not player_alive[player]]
                    df.loc[start_time,'life_tap_count'] = life_tap_count
                    # reset variables
                    arena_active = False
                    start_time = None
                elif event == "SPELL_CAST_SUCCESS" and "Player" in row['arg1']:
                    # check for new player
                    if row['arg2'] not in player_alive:
                        player_alive[row['arg2']] = True
                    # check if Life Tap
                    if row['arg10'] == "Life Tap":
                        life_tap_count += 1

                elif event == "UNIT_DIED" and "Player" in row['arg5']:
                    player_alive[row['arg6']] = False
            else:
                # check for new arena
                if event == "ZONE_CHANGE" and (row['arg2'] in arena_zones):
                    start_time = convert_unix_time(date,timestamp)
                    df.loc[start_time,'date'] = date
                    df.loc[start_time,'start_timestamp'] = timestamp
                    df.loc[start_time,'arena_zone'] = row['arg2']
                    df.loc[start_time,'match_number'] = match_number
                    # init variables
                    arena_active = True
                    player_alive = {}
                    life_tap_count = 0
                    match_number += 1

df.plot(x='match_number',y='life_tap_count')
plt.show()
df_2v2 = df[df['match_size'] == '2v2']
print('{} 2v2 matches found'.format(len(df_2v2)))
print('\tWins: {}'.format(sum(df_2v2['outcome'] == 'Win')))
print('\tLosses: {}'.format(sum(df_2v2['outcome'] == 'Loss')))
print("Done")