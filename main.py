#!/usr/bin/env python

import subprocess
import datetime
import os
from time import sleep
from time import time

foreground = "ff99ff"
foreground_alt = "94b2ff"
foreground_combined = "CFA4FF"
background = "f1f1f1"
separator = "787878"

def set_key(color_binds:dict):
    binds = [f"{k}={v}" for k,v in color_binds.items()]
    if len(binds) <= 0:
        return
    cmd = ["keyledsctl","set-leds"]+ binds
    subprocess.run(cmd)

class Module:
    def __init__(self,update_rate:float,build):
        self.update_rate = update_rate
        self.build = build

def mod_binary_time(second_mode = False) -> dict:
    separator_key = "6"
    key_set = ["1","2","3","4","5","6","7","8","9","0","MINUS","EQUAL"]
    key_set.remove(separator_key)
    if second_mode:
        key_set = ["GRAVE"]+key_set
    now = datetime.datetime.now()
    hour = format(now.hour,"b").rjust(5,"0")
    minute = format(now.minute,"b").rjust(6,"0")
    seconds = format(now.second,"b").rjust(6,"0")
    keys =  {}
    render_str = minute+seconds if second_mode else hour+minute
    for index,v in enumerate(render_str):
        if v == "1":
            keys[key_set[index]] = foreground
        else:
            keys[key_set[index]] = background
    keys[separator_key] = separator
    if second_mode:
        hh = now.hour%12
        if hh == 0:
            hh = 12
        for i in range(12):
            keys[f"F{i+1}"] = background
        keys[f"F{hh}"] = foreground
    return keys

def mod_num_time(second_mode = False) -> dict:
    now = datetime.datetime.now()
    hh = now.hour%12
    if hh == 0:
        hh = 12
    minutes = str(now.minute).rjust(2,"0")
    keys = {}
    for i in range(12):
        keys[f"F{i+1}"] = background
        keys[str(i%10)] = background
    keys[f"F{hh}"] = foreground if now.hour <= 12 else foreground_alt
    if minutes[0] == minutes[1]:
        keys[minutes[0]] = foreground_combined
    else:
        keys[minutes[0]] = foreground
        keys[minutes[1]] = foreground_alt
    if second_mode:
        seconds = str(now.second).rjust(2,"0")
        for i in range(10):
            keys[f"KP{i}"] = background
        if seconds[0] == seconds[1]:
            keys[f"KP{seconds[0]}"] = foreground_combined
        else:
            keys[f"KP{seconds[0]}"] = foreground
            keys[f"KP{seconds[1]}"] = foreground_alt
    return keys


modules_library = {
    "clear": Module(0,lambda : set_key({"all": background})),
    "num_time": Module(60, mod_num_time),
    "num_time_s": Module(1, lambda : mod_num_time(second_mode=True)),
    "binary_time": Module(60, mod_binary_time),
    "binary_time_s": Module(1, lambda : mod_binary_time(second_mode=True))
}

def compile_mods(mods:list, force_update=False) -> dict:
    keys = {}
    for mod in mods:
        if not force_update and mod.update_rate > 0 and not time()%mod.update_rate < clock_frequency:
            continue
        res = mod.build()
        if res is None:
            continue
        keys.update(res)
    return keys


modlist = [modules_library.get(f) for f in os.sys.argv[1:]]
modlist = filter(lambda x: not x is None, modlist)

srtd = sorted(modlist,key= lambda x: x.update_rate)
init_build = []
iter_build = []
for f in srtd:
    if f.update_rate <= 0:
        init_build.append(f)
    else:
        iter_build.append(f)


frequency = iter_build[0].update_rate
clock_frequency = min(frequency,1)
# auto clear on start :
# (can be removed)
init_build = [modules_library["clear"]]+init_build

set_key(compile_mods(init_build+iter_build, force_update=True))

if len(iter_build) == 0:
    exit()

# timer sync
while True:
    now = time()
    if now-int(now) <= 0.1:
        break

while True:
    start = time()
    # removes the millisecond time increment comming
    # from the clock system itself
    delta = start-int(start)
    keys = compile_mods(iter_build)
    set_key(keys)
    sleep((clock_frequency-(time()-start))-delta)