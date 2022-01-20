import argparse
import pdb
import datetime
import logging
import logging.config
from configobj import ConfigObj
import src.log as log

yestd = (datetime.datetime.now() - datetime.timedelta(1)).strftime("%Y%m%d")
today = datetime.datetime.now().strftime("%Y%m%d")


def parse_arg():
    parser = argparse.ArgumentParser(
        description="opt from argparse can overwrite the config file."
    )
    parser.add_argument(
        "-s", dest="start_date", default=yestd, help="an integer for the accumulator"
    )
    parser.add_argument(
        "-e", dest="end_date", default=today, help="an integer for the accumulator"
    )
    parser.add_argument(
        "-f",
        dest="force_meta_download",
        action="store_true",
        default=False,
        help="skip incrementally scan in meta data, append meta anyway, this will NOT cause duplicated data",
    )
    parser.add_argument(
        "-r",
        "--runner",
        dest="runner",
        nargs="+",
        default=["meta", "main"],
        help="meta, main",
    )
    arg = parser.parse_args()
    config = config_from_file()
    config.update(arg.__dict__)
    get_logger(config["logconf_path"], __name__).info(
        "use config: {}".format(config)
    )
    return config


def get_logger(log_path, name):
    if not name in log.Loggers:
        logging.config.fileConfig(log_path)
        log.Loggers[name] = logging.getLogger(name)
    return log.Loggers[name]


def config_from_file(path="./etc/main.conf"):
    config = ConfigObj(path)
    return config
