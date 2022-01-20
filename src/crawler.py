import re
import os
import abc
import time
import requests
import pandas as pd
from retrying import retry
from bs4 import BeautifulSoup

from src.utils import get_logger
from src.exception import NoDataError


class DataWork():
    '''base class, define some varible that would be shared in meta worker and main worker'''

    def __init__(self, config, logger=None):
        self.config = config
        self.base_url = self.config['base_url']
        self.host = self.config['host']
        self.meta_path = self.config['meta_path']
        self.data_path = self.config['data_path']
        self.log_cfg_path = self.config['logconf_path']
        self.time_sleep = float(self.config['time_sleep'])
        self.logger = self.set_logger()

    @property
    def headers(self):
        dic = {'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                              ' (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36')}
        return dic

    def set_logger(self):
        return get_logger(self.log_cfg_path, __name__)

    @abc.abstractmethod
    def run(self):
        return

    @retry(wait_random_min=1000, wait_random_max=20000, stop_max_attempt_number=5)
    def get_data(self, url):
        rsp = requests.get(url, headers=self.headers)
        return rsp


class MainDataWork(DataWork):
    '''main datawork is to downloading the data according to the metawork and save it into csv'''

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.start_date = self.config['start_date']
        self.end_date = self.config['end_date']

    def read_meta(self, fp_meta: str) -> pd.DataFrame:
        """read meta infos, and filter the dates"""
        self.logger.debug("select data from {}-{}".format(self.start_date, self.end_date))
        df = pd.read_csv(fp_meta, sep='|', index_col=False, names=MetaDataWork.meta_col)
        df.loc[:, 'date'] = pd.to_datetime(df.date)
        dfa = df.query("(@self.start_date < = date) & (@self.end_date >= date)")
        return dfa

    def run(self):
        '''main processing logic'''
        try:
            self.work()
        except NoDataError:
            self.logger.error('there is no data on website, crawler stop!')

    def work(self):
        df = self.read_meta(self.meta_path)
        for i, tup in df.iterrows():
            date, url = tup
            rsp = self.get_data(url)
            dfs = pd.read_html(rsp.text, header=0)
            if dfs:
                df = dfs[0]
            else:
                raise NoDataError(rsp)
            fp = date.strftime(self.data_path)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            df.to_csv(fp, sep='|', index=False)
            self.logger.debug("save -> {} len:{}".format(fp, df.shape[0]))
            time.sleep(self.time_sleep)


class MetaDataWork(DataWork):
    """meta data only have 1 mode, once there is no new data on the page
       https://www.sge.com.cn/sjzx/mrhqsj?p={page}, it will stop iteration.
       so hist data should be run under your watching. when production recovery,
       please use -f if necessary to back-filling the historical gaps."""

    meta_col = ['date', 'url']

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.start_date = self.config['start_date']
        self.end_date = self.config['end_date']
        self.force_meta_download = self.config['force_meta_download']
        self.meta_col = MetaDataWork.meta_col

    def run(self):
        """once all of th page data in the meta path, stop iteration
        """
        self.logger.info("run meta worker")
        i = 0
        while 1:
            i += 1
            url = self.base_url.format(pnum=i)
            self.logger.debug("ready to get {}".format(url))
            tups = self.retrive_base_urls(url)
            self.logger.debug("get {} data".format(len(tups)))
            is_more = self.save_meta(tups)
            if not is_more and not self.force_meta_download:
                self.logger.info("no more new data, stop at {}".format(url))
                break
            time.sleep(1)

    def save_meta(self, tups: tuple) -> bool:
        """save only incremental meta data which is not occur in meta csv,
        and return the status code [bool]
        """
        cols = self.meta_col
        df_exist = pd.DataFrame([], columns=cols)
        if os.path.isfile(self.meta_path):
            df_exist = pd.read_csv(self.meta_path, sep='|', names=cols)
        df = pd.DataFrame(tups, columns=cols)
        is_in = df['date'].isin(df_exist['date'])  # True is for exist
        os.makedirs(os.path.dirname(self.meta_path), exist_ok=True)
        df_save = df.loc[~ is_in, :]
        if not df_save.empty:
            df_save.to_csv(self.meta_path, sep='|', index=False, mode='a', header=False)  # save exist
            self.logger.info("append -> {} len {}".format(self.meta_path, df_save.shape[0]))
        return ~ is_in.all()

    def retrive_base_urls(self, burl):
        """get meta data from entry page"""
        rsp = self.get_data(burl)
        soup = BeautifulSoup(rsp.text, 'html.parser')
        res = []
        for mya in soup.find_all('a'):
            href = mya.get('href')
            if href and re.match(re.compile(r'/sjzx/mrhqsj/\d*'), href):
                spans = mya.find_all('span', class_='fr')
                if len(spans) != 1:
                    raise ValueError("unexpected html structure in {}".format(mya))
                res.append((spans[0].text, self.host + href))
        return res
