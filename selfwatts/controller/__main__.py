import logging
import random
from argparse import ArgumentParser

from selfwatts.controller import __version__ as selfwatts_version
from selfwatts.controller.libpfm_wrapper import get_available_pmus
from selfwatts.controller.invoker import HwpcSensorInvoker
from selfwatts.controller.database import MongoDatabaseAdapter
from selfwatts.controller.controller import SelfWattsController


def generate_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(description='SelfWatts Controller.')
    parser.add_argument('--random-seed', type=int, default=None)
    parser.add_argument('--hostname', type=str, required=True)
    parser.add_argument('--frequency', type=int, default=1000)
    parser.add_argument('--pmu', type=str, required=True, choices=get_available_pmus())
    parser.add_argument('--pmu-fixed-events', type=str, nargs='*', default=[])
    parser.add_argument('--mongodb-uri', type=str, required=True)
    parser.add_argument('--mongodb-database', type=str, default='selfwatts')
    parser.add_argument('--mongodb-collection', type=str, default='controller')
    return parser

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname).1s: %(asctime)s controller: %(message)s', datefmt='%y-%m-%d %H:%M:%S', level=logging.DEBUG)
    logging.info('SelfWatts Controller version ' + selfwatts_version)

    try:
        args = generate_arg_parser().parse_args()
        random.seed(args.random_seed)
        sensor = HwpcSensorInvoker(args.hostname, args.frequency, args.mongodb_uri, args.mongodb_database, 'sensor')
        db = MongoDatabaseAdapter(args.mongodb_uri, args.mongodb_database, args.mongodb_collection)
        controller = SelfWattsController(args.hostname, args.pmu, args.pmu_fixed_events, db, sensor)
        controller.handle_control_events()
    except KeyboardInterrupt:
        pass

    exit(0)

