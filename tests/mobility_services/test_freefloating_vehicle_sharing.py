import tempfile
import unittest
from pathlib import Path
import pandas as pd

from mnms.generation.roads import generate_line_road, RoadDescriptor
from mnms.graph.zone import Zone
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


class TestFreeFloatingVehicleSharing(unittest.TestCase):
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

    def test_simple_freefloating(self):
        """Check behavior of free-floating vehicle sharing.
        """
        # Create the scenario
        roads = generate_line_road([0, 0], [0, 3000], 4)

        odlayer = generate_matching_origin_destination_layer(roads)

        ffvelov = VehicleSharingMobilityService("FFVELOV", 1, 0)
        ffvelov.attach_vehicle_observer(CSVVehicleObserver(self.dir_results / "veh_ffvelov.csv"))
        ffvelov_layer = generate_layer_from_roads(roads, 'BIKESHARING', SharedVehicleLayer, Bike, 5.55, [ffvelov])

        mlgraph = MultiLayerGraph([ffvelov_layer], odlayer)

        ffvelov.init_free_floating_vehicles('0',1)

        mlgraph.connect_origindestination_layers(500)

        decision_model = DummyDecisionModel(mlgraph, outfile=self.dir_results / "path.csv")

        def mfdspeed(dacc):
            dspeed = {'BIKE': 5.55}
            return dspeed
        flow_motor = MFDFlowMotor(outfile= self.dir_results / "flow.csv")
        flow_motor.add_reservoir(Reservoir(mlgraph.roads.zones['RES'], ['BIKE'], mfdspeed))

        demand = BaseDemandManager([User("U0", [0, 0], [0, 2000], Time("07:00:00")),
            User("U1", [0, 2000], [0, 3000], Time("07:08:00"))])
        demand.add_user_observer(CSVUserObserver(self.dir_results / 'user.csv'))

        supervisor = Supervisor(mlgraph,
                                 demand,
                                 flow_motor,
                                 decision_model)

        # Run
        flow_dt = Dt(minutes=1)
        supervisor.run(Time("07:00:00"),
                        Time("07:15:00"),
                        flow_dt,
                        8)

        # Check results
        with open(self.dir_results / "user.csv") as f:
            df = pd.read_csv(f, sep=';')
        df0 = df[df['ID'] == 'U0']
        link_list_0 = [l for i,l in enumerate(df0['LINK'].tolist()) if i == 0 or (i > 0 and l != df0['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_0, ['ORIGIN_0 BIKESHARING_0', 'BIKESHARING_0 BIKESHARING_1', 'BIKESHARING_1 BIKESHARING_2', 'BIKESHARING_2 DESTINATION_2'])
        self.assertGreaterEqual(Time(df0['TIME'].iloc[-1]), Time('07:06:00').remove_time(flow_dt))
        self.assertLessEqual(Time(df0['TIME'].iloc[-1]), Time('07:06:00').add_time(flow_dt))

        df1 = df[df['ID'] == 'U1']
        link_list_1 = [l for i,l in enumerate(df1['LINK'].tolist()) if i == 0 or (i > 0 and l != df1['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_1, ['ORIGIN_2 BIKESHARING_2', 'BIKESHARING_2 BIKESHARING_3', 'BIKESHARING_3 DESTINATION_3'])
        self.assertGreaterEqual(Time(df1['TIME'].iloc[-1]), Time('07:11:00').remove_time(flow_dt))
        self.assertLessEqual(Time(df1['TIME'].iloc[-1]), Time('07:11:00').add_time(flow_dt))

        ffvelov_stations = supervisor._mlgraph.layers['BIKESHARING'].mobility_services['FFVELOV'].stations
        self.assertEqual(len(ffvelov_stations), 1)
        self.assertEqual(list(ffvelov_stations.keys())[0], 'ff_station_FFVELOV_BIKESHARING_3')
        self.assertEqual(len(ffvelov_stations['ff_station_FFVELOV_BIKESHARING_3'].waiting_vehicles), 1)

    def test_competition_for_freefloating_vehicle(self):
        """Check behavior of free-floating vehicle sharing when two travelers are interested by the same vehicle.
        """
        roads = RoadDescriptor()
        roads.register_node("0", [0, 0])
        roads.register_node("1", [500, 0])
        roads.register_node("2", [1000, 0])
        roads.register_node("3", [500, -500])
        roads.register_node("4", [500, -1500])

        roads.register_section("0_1", "0", "1", 500)
        roads.register_section("2_1", "2", "1", 500)
        roads.register_section("1_3", "1", "3", 500)
        roads.register_section("3_4", "3", "4", 1000)

        roads.add_zone(Zone("RES", {"0_1", "2_1", "1_3", "3_4"}, []))

        odlayer = generate_matching_origin_destination_layer(roads)

        ffvelov = VehicleSharingMobilityService("FFVELOV", 1, 0)
        ffvelov.attach_vehicle_observer(CSVVehicleObserver(self.dir_results / "veh_ffvelov.csv"))
        ffvelov_layer = generate_layer_from_roads(roads, 'BIKESHARING', SharedVehicleLayer, Bike, 5.55, [ffvelov])

        mlgraph = MultiLayerGraph([ffvelov_layer], odlayer)

        ffvelov.init_free_floating_vehicles('1', 1)
        ffvelov.init_free_floating_vehicles('3', 1)

        mlgraph.connect_origindestination_layers(501)
        mlgraph.connect_layers("INTRA_BIKESHRING_TRANSIT_0_1", "BIKESHARING_0", "BIKESHARING_1", 500, {})
        mlgraph.connect_layers("INTRA_BIKESHRING_TRANSIT_2_1", "BIKESHARING_2", "BIKESHARING_1", 500, {})
        mlgraph.connect_layers("INTRA_BIKESHRING_TRANSIT_1_3", "BIKESHARING_1", "BIKESHARING_3", 500, {})

        decision_model = DummyDecisionModel(mlgraph, outfile=self.dir_results / "path.csv")

        def mfdspeed(dacc):
            dspeed = {'BIKE': 5.55}
            return dspeed
        flow_motor = MFDFlowMotor(outfile= self.dir_results / "flow.csv")
        flow_motor.add_reservoir(Reservoir(mlgraph.roads.zones['RES'], ['BIKE'], mfdspeed))

        demand = BaseDemandManager([User("U0", [0, 0], [500, -1500], Time("07:00:00")),
            User("U1", [1000, 0], [500, -1500], Time("07:00:00"))])
        demand.add_user_observer(CSVUserObserver(self.dir_results / 'user.csv'))

        supervisor = Supervisor(mlgraph,
                                 demand,
                                 flow_motor,
                                 decision_model)

        # Run
        flow_dt = Dt(minutes=1)
        supervisor.run(Time("07:00:00"),
                        Time("07:15:00"),
                        flow_dt,
                        10)

        # Check results
        with open(self.dir_results / "user.csv") as f:
            df = pd.read_csv(f, sep=';')
        df0 = df[df['ID'] == 'U0']
        link_list_0 = [l for i,l in enumerate(df0['LINK'].tolist()) if i == 0 or (i > 0 and l != df0['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_0, ['ORIGIN_0 BIKESHARING_1', 'BIKESHARING_1 BIKESHARING_3', 'BIKESHARING_3 BIKESHARING_4', 'BIKESHARING_4 DESTINATION_4'])
        self.assertGreaterEqual(Time(df0['TIME'].iloc[-1]), Time('07:10:23').remove_time(flow_dt))
        self.assertLessEqual(Time(df0['TIME'].iloc[-1]), Time('07:10:23').add_time(flow_dt))

        # TODO: fix this with new demand management
        df1 = df[df['ID'] == 'U1']
        link_list_1 = [l for i,l in enumerate(df1['LINK'].tolist()) if i == 0 or (i > 0 and l != df1['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_0, ['ORIGIN_0 BIKESHARING_1', 'INTRA_BIKESHRING_TRANSIT_1_3', 'BIKESHARING_3 BIKESHARING_4', 'BIKESHARING_4 DESTINATION_4'])
        self.assertGreaterEqual(Time(df0['TIME'].iloc[-1]), Time('07:14:45').remove_time(flow_dt))
        self.assertLessEqual(Time(df0['TIME'].iloc[-1]), Time('07:14:45').add_time(flow_dt))

        self.assertEqual(0,1)

    def test_freefloating_with_pt(self):
        """Check behavior of free-floating vehicle sharing with intemrodality with a
        public transportation service.
        """
        # Create the scenario
        roads = generate_line_road([0, 0], [0, 3000], 4)

        roads.register_stop('L0_DIR1_0', '0_1', 0.)
        roads.register_stop('L0_DIR1_1', '1_2', 1.)
        roads.register_stop('L0_DIR2_0', '2_1', 0.)
        roads.register_stop('L0_DIR2_1', '1_0', 1.)

        odlayer = generate_matching_origin_destination_layer(roads)

        bus_service = PublicTransportMobilityService('BUS')
        pt_layer = PublicTransportLayer(roads, 'BUS', Bus, 10, services=[bus_service],
                                       observer=CSVVehicleObserver(self.dir_results / "veh_bus.csv"))
        pt_layer.create_line('L0_DIR1',
                            ['L0_DIR1_0', 'L0_DIR1_1'],
                            [['0_1', '1_2']],
                            TimeTable.create_table_freq('07:00:00', '08:00:00', Dt(minutes=2)))
        pt_layer.create_line('L0_DIR2',
                            ['L0_DIR2_0', 'L0_DIR2_1'],
                            [['2_1', '1_0']],
                            TimeTable.create_table_freq('07:00:00', '08:00:00', Dt(minutes=2)))

        ffvelov = VehicleSharingMobilityService("FFVELOV", 1, 0)
        ffvelov.attach_vehicle_observer(CSVVehicleObserver(self.dir_results / "veh_ffvelov.csv"))
        ffvelov_layer = generate_layer_from_roads(roads, 'BIKESHARING', SharedVehicleLayer, Bike, 5.55, [ffvelov])

        mlgraph = MultiLayerGraph([pt_layer, ffvelov_layer], odlayer)

        ffvelov.init_free_floating_vehicles('3',1)
        mlgraph.connect_origindestination_layers(200)
        # TODO: connection should be done dynamically when a ff station is created, fix this
        #mlgraph.connect_layers("TRANSIT_L0_DIR1_1_BIKESHARING_2", "L0_DIR1_L0_DIR1_1", "BIKESHARING_2", 0, {})
        #mlgraph.connect_layers("TRANSIT_BIKESHARING_2_L0_DIR2_0", "BIKESHARING_2", "L0_DIR2_L0_DIR2_0", 0, {})

        decision_model = DummyDecisionModel(mlgraph, outfile=self.dir_results / "path.csv")

        def mfdspeed(dacc):
            dspeed = {'BUS': 10, 'BIKE': 5.55}
            return dspeed
        flow_motor = MFDFlowMotor(outfile= self.dir_results / "flow.csv")
        flow_motor.add_reservoir(Reservoir(mlgraph.roads.zones['RES'], ['BIKE'], mfdspeed))

        demand = BaseDemandManager([User("U0", [0, 3000], [0, 0], Time("07:10:00")),
            User("U1", [0, 0], [0, 3000], Time("07:00:00"))])
        demand.add_user_observer(CSVUserObserver(self.dir_results / 'user.csv'))

        supervisor = Supervisor(mlgraph,
                                 demand,
                                 flow_motor,
                                 decision_model)

        # Run
        flow_dt = Dt(minutes=1)
        supervisor.run(Time("07:00:00"),
                        Time("07:30:00"),
                        flow_dt,
                        10)

        # Check results
        with open(self.dir_results / "user.csv") as f:
            df = pd.read_csv(f, sep=';')
        df0 = df[df['ID'] == 'U0']
        link_list_0 = [l for i,l in enumerate(df0['LINK'].tolist()) if i == 0 or (i > 0 and l != df0['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_0, ['ORIGIN_3 BIKESHARING_3', 'BIKESHARING_3 BIKESHARING_2', 'BIKESHARING_2 L0_DIR2_L0_DIR2_0', 'L0_DIR2_L0_DIR2_0 L0_DIR2_L0_DIR2_1', 'L0_DIR2_L0_DIR2_1 DESTINATION_0'])
        # TODO: check also arrival time

        df1 = df[df['ID'] == 'U1']
        link_list_1 = [l for i,l in enumerate(df1['LINK'].tolist()) if i == 0 or (i > 0 and l != df1['LINK'].tolist()[i-1])]
        self.assertEqual(link_list_1, ['ORIGIN_0 L0_DIR1_L0_DIR1_0', 'L0_DIR1_L0_DIR1_0 L0_DIR1_L0_DIR1_1', 'L0_DIR1_L0_DIR1_1 BIKESHARING_2', 'BIKESHARING_2 BIKESHARING_3', 'BIKESHARING_3 DESTINATION_3'])
        # TODO: check also arrival time
