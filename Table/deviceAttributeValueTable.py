from sqlalchemy import Table, Column, Integer, String, MetaData


class deviceAttributeValueTable:
    def __init__(self, metadata: MetaData):
        self.deviceAttributeValueTable = Table('DeviceAttributeValue', metadata,
                                               Column('DeviceId', String, primary_key=True, nullable=False),
                                               Column('DeviceUnicastId', Integer, nullable=False),
                                               Column('DeviceAttributeId', Integer, primary_key=True, nullable=False),
                                               Column('Value', Integer),
                                               Column('UpdateDay', Integer),
                                               Column('UpdateTime', Integer),
                                               )
