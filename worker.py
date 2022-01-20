from src.crawler import MainDataWork, MetaDataWork
from src.utils import parse_arg

'''
this is a entry point file.
'''

jobs = {
    'meta':[MetaDataWork],
    'main':[MainDataWork],
}


def main():
    config = parse_arg()
    for key, workers in jobs.items():
        if key in config['runner']:
            for work in workers:
                work(config).run()


if __name__ == '__main__':
    main()

