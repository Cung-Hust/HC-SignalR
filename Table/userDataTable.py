from sqlalchemy import DateTime, Boolean
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.sql.sqltypes import Float


class userDataTable:
    def __init__(self, metadata: MetaData):
        self.userDataTable = Table('UserData', metadata,
                                   Column('Id', Integer, primary_key=True, nullable=False),
                                   Column('RefreshToken', String),
                                   Column('DormitoryId', String),
                                   Column('Latitude', Float),
                                   Column('Longitude', Float),
                                   Column('AllowChangeAccount', Boolean),
                                   Column('CreateAt', DateTime),
                                   Column('UpdateAt', DateTime),
                                   )
