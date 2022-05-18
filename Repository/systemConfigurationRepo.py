from Model.systemConfiguration import systemConfiguration
from sqlalchemy import Table
from sqlalchemy.sql.expression import BinaryExpression
import datetime
from sqlalchemy.engine.base import Connection


class systemConfigurationRepo:
    __systemConfigurationTable: Table
    __context: Connection
    
    def __init__(self, SystemConfigurationTable: Table, context: Connection):
        self.__systemConfigurationTable = SystemConfigurationTable
        self.__context = context
    
    def CreateWithParams(self, sysCon: systemConfiguration):
        ins = self.__systemConfigurationTable.insert()
        values = {
            "IsConnect" : str(sysCon.IsConnect),
            "DisconnectTime": sysCon.DisconnectTime,
            "ReconnectTime": sysCon.ReconnectTime,
            "IsSync": str(sysCon.IsSync),
            "CreateAt": datetime.datetime.now()
        }
        self.__context.execute(ins, values)

    def RemoveById(self, id:int):
        ins = self.__systemConfigurationTable.delete().where(self.__systemConfigurationTable.c.Id == id)
        self.__context.execute(ins)
        
    def RemoveByCondition(self, systemConfiCondition: BinaryExpression):
        ins = self.__systemConfigurationTable.delete().where(systemConfiCondition)
        self.__context.execute(ins)
    
    def UpdateById(self, id:int, newSysConfig: systemConfiguration):
        ins = self.__systemConfigurationTable.update().where(self.__systemConfigurationTable.c.Id == id).values({"IsConnect": str(newSysConfig.IsConnect),
                                                                                                                 "DisconnectTime": newSysConfig.DisconnectTime,
                                                                                                                "ReconnectTime": newSysConfig.ReconnectTime,
                                                                                                                "IsSync": str(newSysConfig.IsSync),
                                                                                                                "UpdateAt": datetime.datetime.now()})
        self.__context.execute(ins)
    
    def FindwithId(self, id:int):
        ins = self.__systemConfigurationTable.select().where(self.__systemConfigurationTable.c.Id == id)
        rel = self.__context.execute(ins)
        return rel
            
    def FindWithCondition(self, condition: BinaryExpression):
        """[summary]

        Args:
            condition (BinaryExpression): [description]

        Returns:
            [type]: [description]
        """
        ins = self.__systemConfigurationTable.select().where(condition)
        rel = self.__context.execute(ins)
        return rel
    
    def FindAll(self):
            ins = self.__systemConfigurationTable.select()
            rel = self.__context.execute(ins)
            return rel