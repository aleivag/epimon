import time
from functools import partial
import os, pprint
import math
import uuid
from sqlalchemy import create_engine

from model import Model


class Host(object):

    def __init__(self, name, ip):
        self.name = name
        self.ip = ip

    def __repr__(self):
        return u"<Host %s>" % self.name


#inject argument in funtion

def get_func(path):
    data = path.split('.')
    uso = '.'.join(data[:-1])
    fnc = data[-1]
    out_func = None
    exec("from %s import %s as out_func" % (uso, fnc))
    return out_func


fixtures = {'host': Host(name="alpha", ip='67.218.42.78')}

#Multiprocesing type

import random
from multiprocessing import Process, Queue

class DBScheduler(Process):
    def __init__(self, outq, peridiocity, dburi, **kargs):
        Process.__init__(self, name='DBScheduler:%s' % peridiocity)

        self.outq = outq
        self.peridiocity = peridiocity

        self.dburi = dburi
        self.dbecho = kargs.pop('dbecho', False)

    def collect_work(self, max_time):
        t0 = time.time()
        time.sleep(max_time)

        e = create_engine(self.dburi, echo=self.dbecho)
        sessionid = str(uuid.uuid4())
        e.execute("""
UPDATE work
SET enable = 0, session='%s'
WHERE peridiocity = %s
    AND reschedule_event = 'AFTER_EVENT'
AND enable = 1""" % (sessionid, self.peridiocity))

        work = e.execute("""
SELECT id, reschedule_event, data_point
FROM work
WHERE peridiocity = %(peridiocity)s
AND enable = 1
UNION ALL
SELECT id, reschedule_event, data_point
FROM work
WHERE peridiocity = %(peridiocity)s
AND session = '%(sessionid)s'
        """ % dict(peridiocity=self.peridiocity, sessionid=sessionid))

        return map(
            lambda x: {
                'wid': x.id, 'peridiocity': self.peridiocity, 'inq-time': time.time(),
                'reschedule_event': x.reschedule_event, 'data-point': x.data_point,
                'q-name': self.name, 'lag-time': time.time() - t0
            }, work
        )

    def run(self):
        wt = 0
        while True:
            work_to_be_done = self.collect_work(self.peridiocity)
            if self.peridiocity == 15:
                z = len(work_to_be_done)
                b = len(filter(lambda x: x['reschedule_event'] == 'BEFORE_EVENT', work_to_be_done))
                print wt, z, b, z-b
                wt += self.peridiocity
            map(self.outq.put, work_to_be_done)

class OutReporter(Process):

    def __init__(self, inq, dburi, **kargs):
        Process.__init__(self, name='reporter')
        self.inq = inq
        self.dburi = dburi
        self.dbecho = kargs.pop('dbecho', False)

    def do_work(self, work):
        rtime = random.random()#*4.5 + 0.5
        time.sleep(rtime)

    def run(self):
        e = create_engine(self.dburi, echo=self.dbecho)
        for trial_run in xrange(10):
            w = self.inq.get()

            self.do_work(w)

            if w['reschedule_event'] == 'AFTER_EVENT':
                e.execute("""
UPDATE  work SET enable=1 where id=%(wid)s
                """ % w)

if __name__ == '__main__':

    uri = 'sqlite:////tmp/%s.sqlite' % str(uuid.uuid4())
    e = create_engine(uri, echo=True)

    model = Model(e)

    session = model.sessionmaker()
    model.metadata.create_all()

    q2 = Queue()

    irun = ['15', '30', '60', '90', '120', '300']

    main_query = "INSERT INTO work (enable,peridiocity,reschedule_event) VALUES %s"

    NJOBS = 100
    d = []
    for h in xrange(NJOBS):
        peridiocity = random.choice(irun)

        w = model.Work()
        w.peridiocity = peridiocity
        w.test = 'test.sleep.sleep'
        w.arguments = {'timeout': 0.5}
        session.add(w)

    w = model.Work()
    w.peridiocity = '15'
    w.test = 'web.http.standar.httping'
    w.arguments = {'host': None, 'report':'None', 'url': 'https://alpha.welcomeclient.com'}
    session.add(w)

    session.flush()
    session.commit()
    session.close()


    print "#starting scheded"

    isched = map(lambda x: DBScheduler(outq=q2, peridiocity=int(x), dburi=uri, dbecho=False), irun + ['5'])

    map(lambda x: x.start(), isched)

    NReporters = 100
    AReporters = []

    while True:
        for i in xrange(NReporters -len(AReporters)):
            rep = OutReporter(q2, dburi=uri, dbecho=False)
            rep.start()
            AReporters.append(rep)

        AReporters = filter(lambda x: x.is_alive(), AReporters)

        if NReporters - len(AReporters) > 0:
            print len(AReporters)


