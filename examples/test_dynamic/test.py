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

#%%
roads = generate_manhattan_road(3, 500, extended=False)
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
time_slots = [Time("07:00:00"), Time("07:05:00"), Time("07:10:00")] # before one simulation step
flags = [1, 0, 1] # 1 is banning, 0 is not banning


#%%
personal_car = PersonalMobilityService('PV')
personal_car.attach_vehicle_observer(CSVVehicleObserver('pv_vehs.csv'))
car_layer = generate_layer_from_roads(roads, 'CAR', mobility_services=[personal_car], banned_nodes=['3b', '5b'],
                                     banned_sections=['5b_3b', '3b_5b', '5_5b', '5b_5', '3_3b', '3b_3'])
# car_layer = generate_layer_from_roads(roads, 'CAR', mobility_services=[personal_car])

uber = OnDemandMobilityService('UBER', 0)
uber.attach_vehicle_observer(CSVVehicleObserver('uber_vehs.csv'))
rh_layer = generate_layer_from_roads(roads, 'RH', mobility_services=[uber])
uber.create_waiting_vehicle('RH_3')
uber.create_waiting_vehicle('RH_2')


bus_service = PublicTransportMobilityService('BUS')
bus_layer = PublicTransportLayer(roads, 'BUS', Bus, 15, services=[bus_service],
                                observer=CSVVehicleObserver("veh_bus.csv"))
bus_layer.create_line("L",["S5b", "S3b"],[["5b_3b"]],
                        timetable=TimeTable.create_table_freq('07:00:00', '07:15:00', Dt(minutes=5))+TimeTable.create_table_freq('07:15:00', '07:30:00', Dt(minutes=1))+TimeTable.create_table_freq('07:30:00', '08:00:00', Dt(minutes=5)))
bus_layer.create_line("Lr",["S3b", "S5b"],[["3b_5b"]],
                        timetable=TimeTable.create_table_freq('07:00:00', '08:00:00', Dt(minutes=2)))

odlayer = generate_matching_origin_destination_layer(roads)

mlgraph = MultiLayerGraph([car_layer, rh_layer, bus_layer],odlayer,1)
# mlgraph = MultiLayerGraph([car_layer,rh_layer],odlayer,1)


demand = BaseDemandManager([User("U0", [0, 1000], [1000, 0], Time("07:00:00")),
                            User("U1", [0, 1000], [1000, 0], Time("07:05:00")),
                            User("U2", [0, 1000], [1000, 0], Time("07:05:00")),
                            User("U3", [0, 1000], [1000, 0], Time("07:20:00"))])
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
        return [("RH_5_5b", "UBER", 30)]  # Always active period


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
            if start_time <= tcurrent < end_time:
                return [("RH_5_5b", "UBER", 30)] # try to banning the connection


    # If tcurrent does not match any active periods
    return []

# def dynamic_(graph, tcurrent):
#     if tcurrent >= Time('07:05:30') and tcurrent < Time('07:05:40'):
#         return [("RH_5_5b", "UBER", 3)]
#     return []

mlgraph.dynamic_space_sharing.set_dynamic(dynamic, 0)


def mfdspeed_RES(dacc):
    if dacc['CAR'] >=1:
        dspeed = {'CAR': 2}
    else:
        dspeed = {'CAR': 5}
    return dspeed
def mfdspeed_Res_bus(dacc):
    dspeed = {'CAR': 4, 'BUS': 4}
    return dspeed

flow_motor = MFDFlowMotor(outfile='reservoirs.csv')
flow_motor.add_reservoir(Reservoir(roads.zones["RES"], ['CAR'], mfdspeed_RES))
flow_motor.add_reservoir(Reservoir(roads.zones["Res_bus"], ['CAR'], mfdspeed_Res_bus))


supervisor = Supervisor(mlgraph,
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
