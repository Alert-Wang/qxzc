
class NoDataError(Exception):

    def __init__(self, rsp, msg='there is no data found.'):
        self.rsp = rsp
        super().__init__(msg)

    def __str__(self):
        return f'rsp status:{self.rsp.status_code},  rsp.text:{self.rsp.text}'



