from Table.systemConfigurationTable import systemConfigurationTable
from Table.userDataTable import userDataTable
from Table.deviceAttributeValueTable import deviceAttributeValueTable
from sqlalchemy import MetaData


class tableManager:
    __systemConfigurationTable: systemConfigurationTable
    __userDataTable: userDataTable
    __deviceAttributeTable: deviceAttributeValueTable
        
    def __init__(self, metadata: MetaData):
        self.__systemConfigurationTable = systemConfigurationTable(metadata)
        self.__userDataTable = userDataTable(metadata)
        self.__deviceAttributeTable = deviceAttributeValueTable(metadata)
        
    @property 
    def DeviceAttributeValueTable(self):
        return self.__deviceAttributeTable.deviceAttributeValueTable
        
    @property
    def SystemConfigurationTable(self):
        return self.__systemConfigurationTable.systemConfigurationTable
    
    @property
    def UserDataTable(self):
        return self.__userDataTable.userDataTable