from Repository.deviceAttributeValueRepo import deviceAttributeValueRepo
from sqlalchemy import Table
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.expression import BinaryExpression


class MetaDeviceAttributeValueServices(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(MetaDeviceAttributeValueServices, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class deviceAttributeValueServices(metaclass=MetaDeviceAttributeValueServices):
    __deviceAttributeValueRepo: deviceAttributeValueRepo
    
    def __init__(self, deviceAttributeValueTable: Table, context: Connection):
        self.__deviceAttributeValueRepo = \
            deviceAttributeValueRepo(DeviceAttributeValueTable=deviceAttributeValueTable, context=context)
        
    def FindDeviceAttributeValueWithCondition(self, condition: BinaryExpression):
        rel = self.__deviceAttributeValueRepo.FindWithCondition(condition)
        return rel