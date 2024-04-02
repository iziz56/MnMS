#%%
import numpy as np 
import pandas as pd 
import os 
import os 
import random
from mnms.time import TimeTable, Dt, Time

def LCF(average_speed):
    sections = ['0_1', '0_3', '1_2', '1_0', '1_4', '2_1', '2_5', '3_4', '3_6', '3_0', '4_5', '4_3', '4_7', '4_1', '5_4', '5_8', '5_2', '6_7', '6_3', '7_8', '7_6', '7_4', '8_7', '8_5', '5b_3b', '3b_5b', '5_5b', '5b_5', '3_3b', '3b_3']
    roads = [random.randint(1,3) for i in range(len(sections)-6)]
    roads = roads + [1, 1, 1, 1, 1, 1]
    max_lane = 3
    average_speed = average_speed
    speed = [average_speed * road/max_lane for road in roads]
    speed_dict = dict(zip(sections, speed))
    return speed_dict

def Network_Length():
    sections = ['0_1', '0_3', '1_2', '1_0', '1_4', '2_1', '2_5', '3_4', '3_6', '3_0', '4_5', '4_3', '4_7', '4_1', '5_4', '5_8', '5_2', '6_7', '6_3', '7_8', '7_6', '7_4', '8_7', '8_5', '5b_3b', '3b_5b', '5_5b', '5b_5', '3_3b', '3b_3']
    roads = [500 for i in range(len(sections)-6)]
    roads = roads + [1000, 1000, 0, 0, 0, 0]
    length_dict = dict(zip(sections, roads))
    return length_dict

def banning_check(tcurrent,time_slots, flags):

    # Handling the special cases where all flags are 0 or 1
    if all(flag == 0 for flag in flags):
        return False  # No active period
    elif all(flag == 1 for flag in flags):
        return True  # Always active period

    # Iterate through the time slots and flags for normal cases
    for i in range(len(flags)):
        if flags[i] == 1:  # Active period indicated by flag
            start_time = time_slots[i]
            # Define end_time as the start of the next time slot, or the end of the day for the last slot
            if i + 1 < len(time_slots):
                end_time = time_slots[i + 1]
            else:
                end_time = Time("23:59:59")  # Extend last period to end of day
            # Check if tcurrent is within the active period
            if start_time <= tcurrent < end_time:  # this function is called every simulation step
                return True # try to banning the connection
    
    # If tcurrent does not match any active periods
    return False

def LCF_bus(n_accum, average_speed):
    # n_accum: bus accumulation 
    # average_speed: speed of bus link
    min_speed = 1 
    min_accum = 5 
    max_accum = 10
    if n_accum <=min_accum:
        speed = average_speed
    elif n_accum<=max_accum and  n_accum>min_accum:
        speed = average_speed - (average_speed - min_speed)/(max_accum-min_accum)*(n_accum-min_accum)
    else: 
        speed = min_speed
    return speed
# %%

