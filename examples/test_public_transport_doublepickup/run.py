import tempfile
import unittest
from pathlib import Path

from mnms.demand import BaseDemandManager, User
from mnms.flow.MFD import MFDFlow, Reservoir
from mnms.generation.layers import generate_matching_origin_destination_layer
from mnms.generation.roads import generate_line_road
from mnms.graph.layers import MultiLayerGraph, PublicTransportLayer
from mnms.mobility_service.public_transport import PublicTransportMobilityService
from mnms.simulation import Supervisor
from mnms.time import Time, Dt, TimeTable
from mnms.tools.observer import CSVUserObserver, CSVVehicleObserver
from mnms.travel_decision.dummy import DummyDecisionModel
from mnms.vehicles.veh_type import Bus


roads = generate_line_road([0, 0], [0, 5000], 2)
roads.register_stop('S0', '0_1', 0)
roads.register_stop('S1', '0_1', 0.2)
roads.register_stop('S2', '0_1', 0.4)
roads.register_stop('S3', '0_1', 0.6)
roads.register_stop('S4', '0_1', 0.8)
roads.register_stop('S5', '0_1', 1)

bus_service = PublicTransportMobilityService('B0')
pblayer = PublicTransportLayer(roads, 'BUS', Bus, 10, services=[bus_service],
                               observer=CSVVehicleObserver("veh.csv"))

pblayer.create_line('L0',
                    ['S0', 'S1', 'S2', 'S3', 'S4', 'S5'],
                    [['0_1'], ['0_1'], ['0_1'], ['0_1'], ['0_1']],
                    TimeTable.create_table_freq('07:00:00', '08:00:00', Dt(minutes=10)))

odlayer = generate_matching_origin_destination_layer(roads)


mlgraph = MultiLayerGraph([pblayer],
                          odlayer,
                          100)

# Demand
# U0(S1->S3) and U1(S2->S4) depart at the same timestep 7:00:00
# U2(S2->S4) and U3(S1->S3) depart at the same timestep 7:10:00
# U4(S1->S3) and U5(S2->S4) depart at different but close timesteps 7:09:00 and 7:11:00
# U6(S1->S3), U7(S2->S4) and U8(S0->S5) depart at the same timestep 7:30:00
demand = BaseDemandManager([User("U0", [0, 1000], [0, 3000], Time("07:00:00")),
    User("U1", [0, 2000], [0, 4000], Time("07:00:00")),
    User("U2", [0, 2000], [0, 4000], Time("07:10:00")),
    User("U3", [0, 1000], [0, 3000], Time("07:10:00")),
    User("U4", [0, 1000], [0, 3000], Time("07:19:00")),
    User("U5", [0, 2000], [0, 4000], Time("07:21:00")),
    User("U6", [0, 3000], [0, 4000], Time("07:30:00")),
    User("U7", [0, 1000], [0, 2000], Time("07:30:00")),
    User("U8", [0, 1000], [0, 5000], Time("07:38:00")),
    User("U9", [0, 2000], [0, 3000], Time("07:41:00")),
    User("U10", [0, 3000], [0, 4000], Time("07:47:00"))])
demand.add_user_observer(CSVUserObserver('user.csv'))

# Decison Model
decision_model = DummyDecisionModel(mlgraph, outfile="path.csv")

# Flow Motor
def mfdspeed(dacc):
    dacc['BUS'] = 10
    return dacc

flow_motor = MFDFlow()
flow_motor.add_reservoir(Reservoir('RES', ['BUS'], mfdspeed))

supervisor = Supervisor(mlgraph,
                        demand,
                        flow_motor,
                        decision_model)

supervisor.run(Time("07:00:00"),
               Time("08:00:00"),
               Dt(minutes=1),
               1)
