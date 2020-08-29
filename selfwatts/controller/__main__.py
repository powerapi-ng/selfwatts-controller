import logging
from argparse import ArgumentParser

from selfwatts.controller import __version__ as selfwatts_version
from selfwatts.controller.libpfm_wrapper import get_available_pmus
from selfwatts.controller.invoker import HwpcSensorInvoker
from selfwatts.controller.database import MongoDatabaseAdapter
from selfwatts.controller.controller import SelfWattsController


def generate_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(description='SelfWatts Controller.')
    parser.add_argument('--hostname', type=str, required=True)
    parser.add_argument('--pmu', type=str, required=True, choices=get_available_pmus())
    parser.add_argument('--mongodb-uri', type=str, required=True)
    parser.add_argument('--mongodb-database', type=str, default='selfwatts')
    parser.add_argument('--mongodb-collection', type=str, default='controller')
    return parser

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG) 
    logging.info('SelfWatts Controller version ' + selfwatts_version)

    try:
        args = generate_arg_parser().parse_args()
        sensor = HwpcSensorInvoker(args.hostname, args.mongodb_uri, args.mongodb_database, 'sensor')
        db = MongoDatabaseAdapter(args.mongodb_uri, args.mongodb_database, args.mongodb_collection)
        controller = SelfWattsController(args.hostname, args.pmu, db, sensor)
        controller.handle_control_events()
    except KeyboardInterrupt:
        pass

    exit(0)

