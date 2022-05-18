from ModelServices.systemConfigurationServices import systemConfigurationServices
from ModelServices.userDataService import userDataServices
from ModelServices.deviceAttributeValueServices import deviceAttributeValueServices
from Table.tableManager import tableManager
from sqlalchemy.engine.base import Connection


class MetaService(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(MetaService, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class modelServicesManager(metaclass=MetaService):
    __systemConfigurationServices: systemConfigurationServices
    __userDataService: userDataServices
    __deviceAttributeValueService: deviceAttributeValueServices
        
    def __init__(self, table: tableManager, context: Connection):
        self.__systemConfigurationServices = systemConfigurationServices(table.SystemConfigurationTable, context)
        self.__userDataService = userDataServices(table.UserDataTable, context)
        self.__deviceAttributeValueService = deviceAttributeValueServices(table.DeviceAttributeValueTable, context)
        
    @property
    def SystemConfigurationServices(self):
        return self.__systemConfigurationServices
    
    @property
    def UserdataServices(self):
        return self.__userDataService
    
    @property
    def DeviceAttributeValueServices(self):
        return self.__deviceAttributeValueService
