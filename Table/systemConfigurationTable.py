from sqlalchemy import DateTime
from sqlalchemy import Table, Column, Integer, String, MetaData


class systemConfigurationTable:
    def __init__(self, metadata: MetaData):
        self.systemConfigurationTable = Table('SystemConfiguration', metadata,
                                              Column('Id', Integer, primary_key=True, nullable=False),
                                              Column('IsConnect', String),
                                              Column('DisconnectTime', DateTime),
                                              Column('ReconnectTime', DateTime),
                                              Column('IsSync', String),
                                              Column('CreateAt', DateTime),
                                              Column('UpdateAt', DateTime),
                                              )
