#%%
import numpy as np 
import pandas as pd 
import os 
import os 
import random

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
# %%
