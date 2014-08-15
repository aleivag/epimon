__author__ = 'aleivag'

from sqlalchemy import Column, Integer, Unicode, PickleType, Enum, Boolean

from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

class Model(object):
    def __init__(self, engine):

        self.Base = declarative_base(bind=engine)
        self.metadata = self.Base.metadata
        self.sessionmaker = sessionmaker(bind=engine)

        class Work(self.Base):
            __tablename__ = 'work'

            id = Column(Integer, primary_key=True)

            reschedule_event = Column(Enum('BEFORE_EVENT', 'AFTER_EVENT', 'ONE_TIME'), default='AFTER_EVENT', nullable=False)
            data_point = Column(Enum('REAL_TIME'), default='REAL_TIME', nullable=False)
            peridiocity = Column(Enum('5', '15', '30', '60', '90', '120', '300'), nullable=False)


            test = Column(Unicode(80), nullable=False)
            arguments = Column(PickleType, default={}, nullable=False)

            enable = Column(Boolean, default=True, nullable=False)
            session = Column(Unicode(45), default='', nullable=False)


        self.Work = Work