#!/usr/bin/env python

import subprocess
import datetime
import os
import json
import numpy as np
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

def rgb_to_hex(rgb:tuple, prefix="") -> str:
    r = hex(rgb[0])[2:].rjust(2,"0")
    g = hex(rgb[1])[2:].rjust(2,"0")
    b = hex(rgb[2])[2:].rjust(2,"0")

    return prefix+r+g+b

def gradient(color1:str, color2:str, slices = 1, output_hex=True, include_bounds=True) -> list:
    rawc1 = color1[:6] if not color1.startswith("#") else color1[1:7]
    rawc2 = color2[:6] if not color2.startswith("#") else color2[1:7]
    r1 = int(rawc1[0:2],16)
    g1 = int(rawc1[2:4],16)
    b1 = int(rawc1[4:6],16)
    r2 = int(rawc2[0:2],16)
    g2 = int(rawc2[2:4],16)
    b2 = int(rawc2[4:6],16)

    dr = r1-r2
    dg = g1-g2
    db = b1-b2

    res = []
    if include_bounds:
        rgb1 = (r1,g1,b1)
        res.append(rgb1 if not output_hex else rgb_to_hex(rgb1,prefix="#"))

    for i in range(slices):
        nr = round(r1 + (abs((i+1)*(dr/(slices+1)))*(-1 if dr >= 0 else 1)))
        ng = round(g1 + (abs((i+1)*(dg/(slices+1)))*(-1 if dg >= 0 else 1)))
        nb = round(b1 + (abs((i+1)*(db/(slices+1)))*(-1 if db >= 0 else 1)))
        nrgb = (nr,ng,nb)
        res.append(nrgb if not output_hex else rgb_to_hex(nrgb,prefix="#"))
    if include_bounds:
        rgb2 = (r2,g2,b2)
        res.append(rgb2 if not output_hex else rgb_to_hex(rgb2,prefix="#"))
    
    return res

def mod_binary_time(second_mode = False, merged = True) -> dict:
    keys =  {}
    now = datetime.datetime.now()
    separator_key = "6"
    key_set = ["1","2","3","4","5","6","7","8","9","0","MINUS","EQUAL"]
    render_str = ""
    if merged:
        separator_key = None
        hour = str(now.hour)
        minutes = str(now.minute).rjust(2,"0")
        render_str = format(int(hour+minutes),"b").rjust(12,"0")
        print(render_str)
        for index, v in enumerate(render_str):
            if v == "1":
                keys[f"F{index+1}"] = foreground
            else:
                keys[f"F{index+1}"] = background
        return keys

    key_set.remove(separator_key)
    if second_mode:
        key_set = ["GRAVE"]+key_set
    hour = format(now.hour,"b").rjust(5,"0")
    minute = format(now.minute,"b").rjust(6,"0")
    seconds = format(now.second,"b").rjust(6,"0")
    render_str = minute+seconds if second_mode else hour+minute
    for index,v in enumerate(render_str):
        if v == "1":
            keys[key_set[index]] = foreground
        else:
            keys[key_set[index]] = background
    if not separator_key is None:
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

def mod_sysinfo() -> dict:
    keys = {}
    infos = subprocess.check_output("fastfetch --format json -l none --pipe -s CPUUsage:Memory:GPU --multithreading",shell=True).decode()
    res = json.loads(infos)
    cpu_usage = np.mean(res[0]["result"])/10
    memory_total = res[1]["result"]["total"]
    memory_used = res[1]["result"]["used"]
    memory_usage = (memory_used/memory_total)*10
    gpu_usage = res[2]["result"][0]["coreUsage"]
    grad = gradient("#99ff00","#ff2a00",7,include_bounds=True)
    if gpu_usage is None:
        gpu_info = json.loads(subprocess.check_output("rocm-smi --json -u",shell=True))
        gpu_usage = float(gpu_info["card0"]["GPU use (%)"])/10
    
    den = 10/len(grad)

    cpu_grad = min(int(cpu_usage/den),len(grad)-1)
    mem_grad = min(int(memory_usage/den),len(grad)-1)
    gpu_grad = min(int(gpu_usage/den),len(grad)-1)

    for f in range(3):
        if f <= cpu_usage/3:
            keys[f"KP{7+f}"] = grad[cpu_grad]
        else:
            keys[f"KP{7+f}"] = background
        if f <= memory_usage/3:
            keys[f"KP{4+f}"] = grad[mem_grad]
        else:
            keys[f"KP{4+f}"] = background
        if f <= gpu_usage/3:
            keys[f"KP{1+f}"] = grad[gpu_grad]
        else:
            keys[f"KP{1+f}"] = background
    return keys

modules_library = {
    "clear": Module(0,lambda : set_key({"all": background})),
    "num_time": Module(60, mod_num_time),
    "num_time_s": Module(1, lambda : mod_num_time(second_mode=True)),
    "binary_time": Module(60, mod_binary_time),
    "binary_time_s": Module(1, lambda : mod_binary_time(second_mode=True,merged=False)),
    "binary_time_m": Module(60, lambda : mod_binary_time(second_mode=False,merged=True)),
    "sys_info": Module(2, mod_sysinfo)
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

args =  os.sys.argv[1:]

modlist = [modules_library.get(f) for f in args]
modlist = filter(lambda x: not x is None, modlist)

srtd = sorted(modlist,key= lambda x: x.update_rate)
init_build = []
iter_build = []

for f in srtd:
    if f.update_rate <= 0:
        init_build.append(f)
    else:
        iter_build.append(f)

# auto clear on start :
# (can be removed)
init_build = [modules_library["clear"]]+init_build

set_key(compile_mods(init_build+iter_build, force_update=True))

if len(iter_build) == 0:
    exit()

frequency = iter_build[0].update_rate
clock_frequency = min(frequency,1)

# timer sync
while True:
    now = time()
    if now-int(now) <= 0.1:
        break

try:
    while True:
        start = time()
        # removes the millisecond time increment comming
        # from the clock system itself
        delta = start-int(start)
        keys = compile_mods(iter_build)
        set_key(keys)
        slpt = max(0,(clock_frequency-(time()-start))-delta)
        sleep(slpt)
except KeyboardInterrupt:
    set_key({"all": background})