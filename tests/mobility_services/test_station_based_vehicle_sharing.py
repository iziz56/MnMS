import tempfile
import unittest
from pathlib import Path
import pandas as pd

from mnms.generation.roads import generate_line_road
from mnms.graph.layers import MultiLayerGraph, SharedVehicleLayer
from mnms.generation.layers import generate_matching_origin_destination_layer, generate_layer_from_roads
from mnms.mobility_service.vehicle_sharing import VehicleSharingMobilityService
from mnms.tools.observer import CSVUserObserver, CSVVehicleObserver
from mnms.vehicles.veh_type import Bike, Bus
from mnms.travel_decision.dummy import DummyDecisionModel
from mnms.flow.MFD import MFDFlowMotor, Reservoir
from mnms.simulation import Supervisor
from mnms.demand import BaseDemandManager, User
from mnms.time import TimeTable, Time, Dt
from mnms.mobility_service.public_transport import PublicTransportMobilityService
from mnms.graph.layers import MultiLayerGraph, PublicTransportLayer


class TestStationBasedVehicleSharing(unittest.TestCase):
    def setUp(self):
        """Initiates the test.
        """
        self.temp_dir_results = tempfile.TemporaryDirectory()
        self.dir_results = Path(self.temp_dir_results.name)

        pass

    def tearDown(self):
        """Concludes and closes the test.
        """
        self.temp_dir_results.cleanup()

    def test_run_and_results(self):
        """Check behavior of station-based vehicle sharing.
        """
        # Create the scenario
        roads = generate_line_road([0, 0], [0, 4000], 5)

        odlayer = generate_matching_origin_destination_layer(roads)

        velov = VehicleSharingMobilityService("VELOV", 0, 0)
        velov.attach_vehicle_observer(CSVVehicleObserver(self.dir_results / "veh_velov.csv"))
        velov_layer = generate_layer_from_roads(roads, 'BIKESHARING', SharedVehicleLayer, Bike, 5.55, [velov])

        mlgraph = MultiLayerGraph([velov_layer], odlayer)

        mlgraph.layers['BIKESHARING'].mobility_services['VELOV'].create_station('S0', '0', '', 10, 3) # use road node id
        mlgraph.layers['BIKESHARING'].mobility_services['VELOV'].create_station('S2', '', 'BIKESHARING_2', 10, 2) # use layer node id
        mlgraph.layers['BIKESHARING'].mobility_services['VELOV'].create_station('S4', '4', '', 10, 0)

        mlgraph.connect_origindestination_layers(1001)

        decision_model = DummyDecisionModel(mlgraph, outfile=self.dir_results / "path.csv")

        def mfdspeed(dacc):
            dspeed = {'BIKE': 5.55}
            return dspeed
        flow_motor = MFDFlowMotor(outfile= self.dir_results / "flow.csv")
        flow_motor.add_reservoir(Reservoir(mlgraph.roads.zones['RES'], ['BIKE'], mfdspeed))

        demand = BaseDemandManager([User("U0", [0, 0], [0, 4000], Time("07:00:00")),
            User("U1", [0, 0], [0, 3000], Time("07:00:00")),
            User("U2", [0, 0], [0, 2000], Time("07:00:00")),
            User("U3", [0, 0], [0, 4000], Time("07:00:00")),
            User("U4", [0, 1000], [0, 4000], Time("07:00:00")),
            User("U5", [0, 2000], [0, 4000], Time("07:10:00"))])
        demand.add_user_observer(CSVUserObserver(self.dir_results / 'user.csv'))

        supervisor = Supervisor(mlgraph,
                                 demand,
                                 flow_motor,
                                 decision_model)

        # Run
        flow_dt = Dt(minutes=1)
        supervisor.run(Time("07:00:00"),
                        Time("07:40:00"),
                        flow_dt,
                        10)

        # Check results
        with open(self.dir_results / "user.csv") as f:
            df = pd.read_csv(f, sep=';')

        df0 = df[df['ID'] == 'U0']
        link_list_0 = [l for i,l in enumerate(df0['LINK'].tolist()) if i == 0 or (i > 0 and l != df0['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_0, ['ORIGIN_0 BIKESHARING_0', 'BIKESHARING_0 BIKESHARING_1', 'BIKESHARING_1 BIKESHARING_2', 'BIKESHARING_2 BIKESHARING_3', 'BIKESHARING_3 BIKESHARING_4', 'BIKESHARING_4 DESTINATION_4'])
        self.assertGreaterEqual(Time(df0['TIME'].iloc[-1]), Time('07:12:00').remove_time(flow_dt))
        self.assertLessEqual(Time(df0['TIME'].iloc[-1]), Time('07:12:00').add_time(flow_dt))

        df1 = df[df['ID'] == 'U1']
        link_list_1 = [l for i,l in enumerate(df1['LINK'].tolist()) if i == 0 or (i > 0 and l != df1['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_1, ['ORIGIN_0 BIKESHARING_0', 'BIKESHARING_0 BIKESHARING_1', 'BIKESHARING_1 BIKESHARING_2', 'BIKESHARING_2 DESTINATION_3'])
        self.assertGreaterEqual(Time(df1['TIME'].iloc[-1]), Time('07:17:44.23').remove_time(flow_dt))
        self.assertLessEqual(Time(df1['TIME'].iloc[-1]), Time('07:17:44.23').add_time(flow_dt))

        df2 = df[df['ID'] == 'U2']
        link_list_2 = [l for i,l in enumerate(df2['LINK'].tolist()) if i == 0 or (i > 0 and l != df2['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_2, ['ORIGIN_0 BIKESHARING_0', 'BIKESHARING_0 BIKESHARING_1', 'BIKESHARING_1 BIKESHARING_2', 'BIKESHARING_2 DESTINATION_2'])
        self.assertGreaterEqual(Time(df2['TIME'].iloc[-1]), Time('07:06:00').remove_time(flow_dt))
        self.assertLessEqual(Time(df2['TIME'].iloc[-1]), Time('07:06:00').add_time(flow_dt))

        df3 = df[df['ID'] == 'U3']
        self.assertEqual(df3['STATE'].iloc[-1], "STOP")

        df4 = df[df['ID'] == 'U4']
        link_list_4 = [l for i,l in enumerate(df4['LINK'].tolist()) if i == 0 or (i > 0 and l != df4['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_4, ['ORIGIN_1 BIKESHARING_2', 'BIKESHARING_2 BIKESHARING_3', 'BIKESHARING_3 BIKESHARING_4', 'BIKESHARING_4 DESTINATION_4'])
        self.assertGreaterEqual(Time(df4['TIME'].iloc[-1]), Time('07:17:44.23').remove_time(flow_dt))
        self.assertLessEqual(Time(df4['TIME'].iloc[-1]), Time('07:17:44.23').add_time(flow_dt))

        df5 = df[df['ID'] == 'U5']
        link_list_5 = [l for i,l in enumerate(df5['LINK'].tolist()) if i == 0 or (i > 0 and l != df5['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_5, ['ORIGIN_2 BIKESHARING_2', 'BIKESHARING_2 BIKESHARING_3', 'BIKESHARING_3 BIKESHARING_4', 'BIKESHARING_4 DESTINATION_4'])
        self.assertGreaterEqual(Time(df5['TIME'].iloc[-1]), Time('07:16:00').remove_time(flow_dt))
        self.assertLessEqual(Time(df5['TIME'].iloc[-1]), Time('07:16:00').add_time(flow_dt))

        s0 = mlgraph.layers['BIKESHARING'].mobility_services['VELOV'].stations['S0']
        self.assertEqual(len(s0.waiting_vehicles), 0)

        s2 = mlgraph.layers['BIKESHARING'].mobility_services['VELOV'].stations['S2']
        self.assertEqual(len(s2.waiting_vehicles), 2)

        s4 = mlgraph.layers['BIKESHARING'].mobility_services['VELOV'].stations['S4']
        self.assertEqual(len(s4.waiting_vehicles), 3)


    def test_run_and_results_with_pt(self):
        """Check behavior of station-based vehicle sharing with intermodality with a public transportation service.
        """
        # Create the scenario
        roads = generate_line_road([0, 0], [0, 5000], 6)

        roads.register_stop('PT0', '0_1', 0.)
        roads.register_stop('PT1', '1_2', 0.9)

        bus_service = PublicTransportMobilityService('BUS')
        pt_layer = PublicTransportLayer(roads, 'BUS', Bus, 10, services=[bus_service],
                                       observer=CSVVehicleObserver(self.dir_results / "veh_bus.csv"))
        pt_layer.create_line('L0',
                            ['PT0', 'PT1'],
                            [['0_1', '1_2']],
                            TimeTable.create_table_freq('07:00:00', '08:00:00', Dt(minutes=5)))

        odlayer = generate_matching_origin_destination_layer(roads)

        velov = VehicleSharingMobilityService("VELOV", 0, 0)
        velov.attach_vehicle_observer(CSVVehicleObserver(self.dir_results / "veh_velov.csv"))
        velov_layer = generate_layer_from_roads(roads, 'BIKESHARING', SharedVehicleLayer, Bike, 5, [velov])

        mlgraph = MultiLayerGraph([velov_layer, pt_layer], odlayer, connection_distance=1001)

        mlgraph.layers['BIKESHARING'].mobility_services['VELOV'].create_station('V2', '2', '', 10, 4) # use road node id
        mlgraph.layers['BIKESHARING'].mobility_services['VELOV'].create_station('V5', '', 'BIKESHARING_5', 3, 0) # use layer node id

        mlgraph.connect_origindestination_layers(1001)
        mlgraph.connect_layers("TRANSIT_LINK", "L0_PT1", "BIKESHARING_2", 100, {})

        decision_model = DummyDecisionModel(mlgraph, outfile=self.dir_results / "path.csv")

        def mfdspeed(dacc):
            dspeed = {'BUS': 10, 'BIKE': 5.55}
            return dspeed
        flow_motor = MFDFlowMotor(outfile= self.dir_results / "flow.csv")
        flow_motor.add_reservoir(Reservoir(mlgraph.roads.zones['RES'], ['BIKE'], mfdspeed))

        demand = BaseDemandManager([User("U0", [0, 0], [0, 5000], Time("07:00:00")),
            User("U1", [0, 2000], [0, 5000], Time("07:00:00")),
            User("U2", [0, 2000], [0, 4000], Time("07:00:00")),
            User("U3", [0, 0], [0, 4000], Time("07:01:00"))])
        demand.add_user_observer(CSVUserObserver(self.dir_results / 'user.csv'))

        supervisor = Supervisor(mlgraph,
                                 demand,
                                 flow_motor,
                                 decision_model)

        # Run
        flow_dt = Dt(minutes=1)
        supervisor.run(Time("07:00:00"),
                        Time("07:40:00"),
                        flow_dt,
                        10)

        # Check results
        with open(self.dir_results / "user.csv") as f:
            df = pd.read_csv(f, sep=';')

        df0 = df[df['ID'] == 'U0']
        link_list_0 = [l for i,l in enumerate(df0['LINK'].tolist()) if i == 0 or (i > 0 and l != df0['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_0, ['ORIGIN_0 L0_PT0', 'L0_PT0 L0_PT1', 'L0_PT1 BIKESHARING_2', 'BIKESHARING_2 BIKESHARING_3', 'BIKESHARING_3 BIKESHARING_4', 'BIKESHARING_4 BIKESHARING_5', 'BIKESHARING_5 DESTINATION_5'])
        self.assertGreaterEqual(Time(df0['TIME'].iloc[-1]), Time('07:19:20.42').remove_time(flow_dt))
        self.assertLessEqual(Time(df0['TIME'].iloc[-1]), Time('07:19:20.42').add_time(flow_dt))

        df1 = df[df['ID'] == 'U1']
        link_list_1 = [l for i,l in enumerate(df1['LINK'].tolist()) if i == 0 or (i > 0 and l != df1['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_1, ['ORIGIN_2 BIKESHARING_2', 'BIKESHARING_2 BIKESHARING_3', 'BIKESHARING_3 BIKESHARING_4', 'BIKESHARING_4 BIKESHARING_5', 'BIKESHARING_5 DESTINATION_5'])
        self.assertGreaterEqual(Time(df1['TIME'].iloc[-1]), Time('07:09:00').remove_time(flow_dt))
        self.assertLessEqual(Time(df1['TIME'].iloc[-1]), Time('07:09:00').add_time(flow_dt))

        df2 = df[df['ID'] == 'U2']
        link_list_2 = [l for i,l in enumerate(df2['LINK'].tolist()) if i == 0 or (i > 0 and l != df2['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_2, ['ORIGIN_2 BIKESHARING_2', 'BIKESHARING_2 BIKESHARING_3', 'BIKESHARING_3 BIKESHARING_4', 'BIKESHARING_4 BIKESHARING_5', 'BIKESHARING_5 DESTINATION_4'])
        self.assertGreaterEqual(Time(df2['TIME'].iloc[-1]), Time('07:20:45').remove_time(flow_dt))
        self.assertLessEqual(Time(df2['TIME'].iloc[-1]), Time('07:20:45').add_time(flow_dt))

        df3 = df[df['ID'] == 'U3']
        link_list_3 = [l for i,l in enumerate(df3['LINK'].tolist()) if i == 0 or (i > 0 and l != df3['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_3, ['TODO: Solve this test']) # TODO: solve this test U3 should not be able to park bike because of station capacity

        bs2 = mlgraph.layers['BIKESHARING'].mobility_services['VELOV'].stations['V2']
        self.assertEqual(len(bs2.waiting_vehicles), 0)

        bs5 = mlgraph.layers['BIKESHARING'].mobility_services['VELOV'].stations['V5']
        self.assertEqual(len(bs5.waiting_vehicles), 3)
