from datetime import datetime, date
import logging
import os


EXPIRIES = ['13-06-2019' , '20-06-2019' , '27-06-2019' ]


MAX_LOGIN_TRIES = 10

BUY = 'B'
SELL = 'S'

TIMEOUT = 10


def round_off(num, div=0.1):
    x = div * round(num / div)
    return float(x)


def get_trade_hours(date):
    o = datetime.strptime(date.strftime('%d-%m-%y') + '-09:15', '%d-%m-%y-%H:%M')
    c = datetime.strptime(date.strftime('%d-%m-%y') + '-15:15', '%d-%m-%y-%H:%M')
    return o, c


def ts_to_datetime(ts=None):
    if ts is None:
        return ts
    return datetime.fromtimestamp(int(ts) / 1000)


def thursdays():
    from calendar import Calendar
    c = Calendar()
    days = []
    thursday = 3
    for i in range(1, 13):
        for d in c.itermonthdates(2019, i):
            if d.weekday() == thursday:
                days.append(d)
    with open('thursdays.txt', 'w') as f:
        for day in days:
            f.write(day.strftime('%d-%m-%Y\n'))


def get_expiry_dates(month=1):
    dates = []
    for e in EXPIRIES:
        d = int(e[0:2])
        m = int(e[3:5])
        Y = int(e[6:])
        if m == month:
            dates.append(date(day=d, month=m, year=Y))
    return dates


def create_logger(name, console=False, level=logging.INFO):
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    name = name + date.today().strftime(' %m-%d-%Y') + '.log'
    fmt = logging.Formatter('[{asctime} - {levelname}] {name} - {message}',
                            datefmt='%H:%M:%S',
                            style='{')
    if console:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        ch.setLevel(level)
        logger.addHandler(ch)
    fh = logging.FileHandler(os.path.join(log_dir, name))
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    return logger

if __name__ == '__main__':
    thursdays()
