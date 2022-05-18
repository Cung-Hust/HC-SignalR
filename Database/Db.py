from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine.base import Connection
import Constant.constant as const
from Table.tableManager import tableManager
from ModelServices.modelServicesManager import modelServicesManager


class MetaDb(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(MetaDb, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Db(metaclass=MetaDb):
    __metadata = MetaData()
    __engine: create_engine
    __connect: Connection
    __dbTable: tableManager
    __servicesManager: modelServicesManager

    def init(self):
        self.__engine = create_engine(
            "sqlite:///" + const.DB_NAME,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.__dbTable = tableManager(self.__metadata)
        self.__metadata.create_all(self.__engine)
        self.__connect = self.__engine.connect()
        self.__servicesManager = modelServicesManager(self.__dbTable, self.__connect)

    @property
    def Table(self):
        return self.__dbTable

    @property
    def Services(self):
        return self.__servicesManager
