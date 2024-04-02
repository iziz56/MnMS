# %%
from mnms.generation.roads import generate_manhattan_road
from mnms.graph.zone import construct_zone_from_sections
from mnms.mobility_service.personal_vehicle import PersonalMobilityService
from mnms.mobility_service.on_demand import OnDemandMobilityService
from mnms.mobility_service.public_transport import PublicTransportMobilityService
from mnms.graph.layers import MultiLayerGraph, PublicTransportLayer
from mnms.time import TimeTable, Dt, Time
from mnms.generation.layers import generate_layer_from_roads, generate_matching_origin_destination_layer
from mnms.vehicles.veh_type import Bus
from mnms.tools.observer import CSVUserObserver, CSVVehicleObserver
from mnms.demand import BaseDemandManager, User
from mnms.travel_decision.dummy import DummyDecisionModel
from mnms.flow.MFD import MFDFlowMotor, Reservoir
from mnms.simulation import Supervisor
from mnms.tools.render import draw_roads, draw_line
from mnms.log import set_all_mnms_logger_level, LOGLEVEL

import matplotlib.pyplot as plt
import os
import sys
import pandas as pd
import numpy as np
import argparse
import sys

#%%
sys.argv = ['']
parser = argparse.ArgumentParser(description='Run mobility simulation with dynamic flag settings.')

# Add an argument for flags
# Use nargs='+' to indicate multiple values are expected
parser.add_argument('--flags', nargs='+', type=int, default=[0, 1, 0, 1],
                    help='List of flags indicating banning periods. Use spaces to separate flags. Example: --flags 1 0 0 1')

# Parse the arguments
args = parser.parse_args()

# Retrieve the flags list from the parsed arguments
flags = args.flags
#%%



roads = generate_manhattan_road(5, 300, extended=False)
# nodes for bus link 
roads.register_node('1b',  [0,300])
roads.register_node('3b',  [0,900])
roads.register_node('21b', [1200,300])
roads.register_node('23b', [1200,900])
roads.register_node('5b',  [300,0])
roads.register_node('9b',  [300,1200])
roads.register_node('15b', [900,0])
roads.register_node('19b', [900,1200])

# nodes for transition
roads.register_node('6b',  [300,300])
roads.register_node('7b',  [300,600])
roads.register_node('8b',  [300,900])
roads.register_node('11b', [600,300])
roads.register_node('13b', [600,900])
roads.register_node('16b', [900,300])
roads.register_node('17b', [900,600])
roads.register_node('18b', [900,900])



# sections for bus link
roads.register_section('1b_21b',  '1b',  '21b', 1200)
roads.register_section('21b_1b', '21b',  '1b',  1200)
roads.register_section('3b_23b',  '3b',  '23b', 1200)
roads.register_section('23b_3b', '23b',  '3b',  1200)
roads.register_section('5b_9b',   '5b',  '9b',  1200)
roads.register_section('9b_5b',   '9b',  '5b',  1200)
roads.register_section('15b_19b', '15b', '19b', 1200)
roads.register_section('19b_15b','19b',  '15b', 1200)

#  sections for transition
roads.register_section('1_1b', '1', '1b', 0)
roads.register_section('1b_1', '1b', '1', 0)
roads.register_section('3_3b', '3', '3b', 0)
roads.register_section('3b_3', '3b', '3', 0)
roads.register_section('5_5b', '5', '5b', 0)
roads.register_section('5b_5', '5b', '5', 0)
roads.register_section('9_9b', '9', '9b', 0)
roads.register_section('9b_9', '9b', '9', 0)
roads.register_section('15_15b', '15', '15b', 0)
roads.register_section('15b_15', '15b', '15', 0)
roads.register_section('19_19b', '19', '19b', 0)
roads.register_section('19b_19', '19b', '19', 0)
roads.register_section('21_21b', '21', '21b', 0)
roads.register_section('21b_21', '21b', '21', 0)
roads.register_section('23_23b', '23', '23b', 0)
roads.register_section('23b_23', '23b', '23', 0)
roads.register_section('6_6b', '6', '6b', 0)
roads.register_section('6b_6', '6b', '6', 0)
roads.register_section('7_7b', '7', '7b', 0)
roads.register_section('7b_7', '7b', '7', 0)
roads.register_section('8_8b', '8', '8b', 0)
roads.register_section('8b_8', '8b', '8', 0)
roads.register_section('11_11b', '11', '11b', 0)
roads.register_section('11b_11', '11b', '11', 0)
roads.register_section('13_13b', '13', '13b', 0)
roads.register_section('13b_13', '13b', '13', 0)
roads.register_section('16_16b', '16', '16b', 0)
roads.register_section('16b_16', '16b', '16', 0)
roads.register_section('17_17b', '17', '17b', 0)
roads.register_section('17b_17', '17b', '17', 0)
roads.register_section('18_18b', '18', '18b', 0)
roads.register_section('18b_18', '18b', '18', 0)



#1. bus line 1b_21b
roads.register_stop('S1b',   '1b_21b', 0.00)
roads.register_stop('S6b',   '1b_21b', 0.25)
roads.register_stop('S11b',  '1b_21b', 0.50)
roads.register_stop('S16b',  '1b_21b', 0.75)
roads.register_stop('S21b',  '1b_21b', 1.00)

#2. bus line 21b_1b
roads.register_stop('Sr21b', '21b_1b', 0.00)
roads.register_stop('Sr16b', '21b_1b', 0.25)
roads.register_stop('Sr11b', '21b_1b', 0.50)
roads.register_stop('Sr6b',  '21b_1b', 0.75)
roads.register_stop('Sr1b',  '21b_1b', 1.00)

#3. bus line 3b_23b
roads.register_stop('S3b',   '3b_23b', 0.00)
roads.register_stop('S8b',   '3b_23b', 0.25)
roads.register_stop('S13b',  '3b_23b', 0.50)
roads.register_stop('S18b',  '3b_23b', 0.75)
roads.register_stop('S23b',  '3b_23b', 1.00)

#4. bus line 23b_3b
roads.register_stop('Sr23b',  '23b_3b', 0.00)
roads.register_stop('Sr18b',  '23b_3b', 0.25)
roads.register_stop('Sr13b',  '23b_3b', 0.50)
roads.register_stop('Sr8b',   '23b_3b', 0.75)
roads.register_stop('Sr3b',   '23b_3b', 1.00)

#5. bus line 5b_9b
roads.register_stop('S5b',     '5b_9b', 0.00)
roads.register_stop('S6b',     '5b_9b', 0.25)
roads.register_stop('S7b',     '5b_9b', 0.50)
roads.register_stop('S8b',     '5b_9b', 0.75)
roads.register_stop('S9b',     '5b_9b', 1.00)

#6. bus line 9b_5b
roads.register_stop('Sr9b',    '9b_5b', 0.00)
roads.register_stop('Sr8b',    '9b_5b', 0.25)
roads.register_stop('Sr7b',    '9b_5b', 0.50)
roads.register_stop('Sr6b',    '9b_5b', 0.75)
roads.register_stop('Sr5b',    '9b_5b', 1.00)

#7. bus line 15b_19b
roads.register_stop('S15b',  '15b_19b', 0.00)
roads.register_stop('S16b',  '15b_19b', 0.25)
roads.register_stop('S17b',  '15b_19b', 0.50)
roads.register_stop('S18b',  '15b_19b', 0.75)
roads.register_stop('S19b',  '15b_19b', 1.00)

#8. bus line 19b_15b
roads.register_stop('Sr19b', '19b_15b', 0.00)
roads.register_stop('Sr18b', '19b_15b', 0.25)
roads.register_stop('Sr17b', '19b_15b', 0.50)
roads.register_stop('Sr16b', '19b_15b', 0.75)
roads.register_stop('Sr15b', '19b_15b', 1.00)
















roads.register_node('5b', [500, 1000])
roads.register_node('3b', [500, 0])
roads.register_section('5b_3b', '5b', '3b', 1000)
roads.register_section('3b_5b', '3b', '5b', 1000)
roads.register_section('5_5b', '5', '5b', 0)
roads.register_section('5b_5', '5b', '5', 0)
roads.register_section('3_3b', '3', '3b', 0)
roads.register_section('3b_3', '3b', '3', 0)

roads.register_stop('S5b', '5b_3b', 0.)
roads.register_stop('S3b', '5b_3b', 1.)
roads.register_stop('S3br', '3b_5b', 0.)
roads.register_stop('S5br', '3b_5b', 1.)

roads.add_zone(construct_zone_from_sections(roads, "Res_bus", ["5b_3b", "3b_5b", '5_5b', '5b_5', '3_3b', '3b_3']))

# time_slots = [Time("06:59:59"), Time("07:09:50"), Time("07:19:50"), Time("07:29:50"), Time("07:39:50")] # before one simulation step
time_slots = [Time("07:00:00"), Time("07:05:00"), Time("07:10:00"),Time("07:15:00")] # before one simulation step
# flags = [1, 0, 0, 1] # 1 is banning, 0 is not banning


#%%
personal_car = PersonalMobilityService('PV')
personal_car.attach_vehicle_observer(CSVVehicleObserver('pv_vehs.csv'))
car_layer = generate_layer_from_roads(roads, 'CAR', mobility_services=[personal_car], banned_nodes=['3b', '5b'],
                                     banned_sections=['5b_3b', '3b_5b', '5_5b', '5b_5', '3_3b', '3b_3'])
# car_layer = generate_layer_from_roads(roads, 'CAR', mobility_services=[personal_car])

# uber = OnDemandMobilityService('UBER', 0)
uber = PersonalMobilityService('UBER')
uber.attach_vehicle_observer(CSVVehicleObserver('uber_vehs.csv'))
rh_layer = generate_layer_from_roads(roads, 'RH', mobility_services=[uber])

# uber.create_waiting_vehicle('RH_2')
# uber.create_waiting_vehicle('RH_2')
# uber.create_waiting_vehicle('RH_2')
# uber.create_waiting_vehicle('RH_2')
# uber.create_waiting_vehicle('RH_2')
# uber.create_waiting_vehicle('RH_2')
# uber.create_waiting_vehicle('RH_2')
# uber.create_waiting_vehicle('RH_2')
# uber.create_waiting_vehicle('RH_2')



bus_service = PublicTransportMobilityService('BUS')
bus_layer = PublicTransportLayer(roads, 'BUS', Bus, 15, services=[bus_service],
                                observer=CSVVehicleObserver("veh_bus.csv"))

bus_layer.create_line("Lr",["S3br", "S5br"],[["3b_5b"]],
                        timetable=TimeTable.create_table_freq('07:00:00', '07:15:00', Dt(minutes=5))+\
                        TimeTable.create_table_freq('07:15:00', '07:30:00', Dt(minutes=2))+\
                        TimeTable.create_table_freq('07:30:00', '08:00:00', Dt(minutes=5)))
bus_layer.create_line("L", ["S5b", "S3b"],[["5b_3b"]],
                        timetable=TimeTable.create_table_freq('07:00:00', '07:15:00', Dt(minutes=5))+\
                        TimeTable.create_table_freq('07:15:00', '07:30:00', Dt(minutes=2))+\
                        TimeTable.create_table_freq('07:30:00', '08:00:00', Dt(minutes=5)))

odlayer = generate_matching_origin_destination_layer(roads)

mlgraph = MultiLayerGraph([car_layer, rh_layer, bus_layer],odlayer,1)
# mlgraph = MultiLayerGraph([car_layer,rh_layer],odlayer,1)


demand = BaseDemandManager([                            
                            User("U0",  [0, 1000], [1000, 0], Time("07:00:00"),['UBER']),
                            User("U1",  [0, 1000], [1000, 0], Time("07:01:00"),['UBER']),
                            User("U2",  [0, 1000], [1000, 0], Time("07:02:00"),['UBER']),
                            User("U3",  [0, 1000], [1000, 0], Time("07:03:00"),['UBER']),
                            User("U4",  [0, 1000], [1000, 0], Time("07:04:00"),['UBER']),
                            User("U5",  [0, 1000], [1000, 0], Time("07:05:00"),['UBER']),
                            User("U6",  [0, 1000], [1000, 0], Time("07:06:00"),['UBER']),
                            User("U7",  [0, 1000], [1000, 0], Time("07:07:00"),['UBER']),
                            User("U8",  [0, 1000], [1000, 0], Time("07:08:00"),['UBER']),
                            User("U9",  [0, 1000], [1000, 0], Time("07:09:00"),['UBER']),
                            User("U10", [0, 1000], [1000, 0], Time("07:10:00"),['UBER']),
                            User("U11", [0, 1000], [1000, 0], Time("07:11:00"),['UBER']),
                            User("U12", [0, 1000], [1000, 0], Time("07:12:00"),['UBER']),
                            User("U13", [0, 1000], [1000, 0], Time("07:13:00"),['UBER']),
                            User("U14", [0, 1000], [1000, 0], Time("07:14:00"),['UBER']),
                            User("U15", [0, 1000], [1000, 0], Time("07:15:00"),['UBER']),
                            User("U16", [0, 1000], [1000, 0], Time("07:16:00"),['UBER']),
                            User("U17", [0, 1000], [1000, 0], Time("07:17:00"),['UBER']),
                            User("U18", [0, 1000], [1000, 0], Time("07:18:00"),['UBER']),
                            User("U19", [0, 1000], [1000, 0], Time("07:19:00"),['UBER']),
                            User("U20", [0, 1000], [1000, 0], Time("07:20:00"),['UBER']),
                            ])
demand.add_user_observer(CSVUserObserver('users.csv'))


decision_model = DummyDecisionModel(mlgraph, outfile="paths.csv", verbose_file=True)


#%%
def dynamic(graph, tcurrent):
    global time_slots
    global flags
    # Handling the special cases where all flags are 0 or 1
    if all(flag == 0 for flag in flags):
        return []  # No active period
    elif all(flag == 1 for flag in flags):
        return [("RH_5_5b", "UBER", 0)]  # Always active period


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
                return [("RH_5_5b", "UBER", 0)] # try to banning the connection


    # If tcurrent does not match any active periods
    return []

# def dynamic_(graph, tcurrent):
#     if tcurrent >= Time('07:05:30') and tcurrent < Time('07:05:40'):
#         return [("RH_5_5b", "UBER", 0)]
#     return []

mlgraph.dynamic_space_sharing.set_dynamic(dynamic, 0)

def mfdspeed_RES(dacc):
    acc = dacc['CAR']
    # if dacc['CAR'] >0:
    #     dspeed = {'CAR': 2}
    # else:
    #     dspeed = {'CAR': 5}
    speed = 4-acc/5
    if speed < 0:
        speed = 0
    dspeed = {'CAR': speed}
    return dspeed

def mfdspeed_Res_bus(dacc):
    speed =  4
    dspeed = {'CAR': speed, 'BUS': speed}

    # dspeed = {'CAR': 4, 'BUS': 4}
    return dspeed

flow_motor = MFDFlowMotor(outfile='reservoirs.csv')
flow_motor.add_reservoir(Reservoir(roads.zones["RES"], ['CAR'], mfdspeed_RES))
flow_motor.add_reservoir(Reservoir(roads.zones["Res_bus"], ['CAR','BUS'], mfdspeed_Res_bus))


supervisor = Supervisor(time_slots,
                        flags,
                        mlgraph,
                        demand,
                        flow_motor,
                        decision_model,
                        logfile='log.txt',
                        loglevel=LOGLEVEL.INFO)

set_all_mnms_logger_level(LOGLEVEL.INFO)
# %%
flow_dt = Dt(seconds=10)
affectation_factor = 6
supervisor.run(Time("06:59:00"),Time("08:00:00"),flow_dt,affectation_factor)
# %%


