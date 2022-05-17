from Model.userData import userData
from sqlalchemy import Table
from sqlalchemy.sql.expression import BinaryExpression
import datetime
from sqlalchemy.engine.base import Connection


class userDataRepo:
    __userDataTable: Table
    __context: Connection
    
    def __init__(self, UserDataTable: Table, context: Connection):
        self.__userDataTable = UserDataTable
        self.__context = context
    
    def CreateWithParams(self, userData: userData):
        ins = self.__userDataTable.insert()
        values = {
            "RefreshToken" : userData.RefreshToken,
            "DormitoryId": userData.DormitoryId,
            "AllowChangeAccount": userData.AllowChangeAccount,
            "CreateAt": datetime.datetime.now()
        }
        self.__context.execute(ins, values)

    def RemoveById(self, id: int):
        ins = self.__userDataTable.delete().where(self.__userDataTable.c.Id == id)
        self.__context.execute(ins)
        
    def RemoveByCondition(self, userDataCondition: BinaryExpression):
        ins = self.__userDataTable.delete().where(userDataCondition)
        self.__context.execute(ins)
    
    def UpdateById(self, id: int, newUserData: userData):
        ins = self.__userDataTable.update().where(self.__userDataTable.c.Id == id).\
            values({"RefreshToken": newUserData.RefreshToken,
                    "DormitoryId": newUserData.DormitoryId,
                    "AllowChangeAccount": newUserData.AllowChangeAccount,
                    "UpdateAt": datetime.datetime.now()})
        self.__context.execute(ins)

    def FindwithId(self, Id: int):
        ins = self.__userDataTable.select().where(self.__userDataTable.c.Id == Id)
        rel = self.__context.execute(ins)
        return rel
            
    def FindWithCondition(self, condition: BinaryExpression):
        ins = self.__userDataTable.select().where(condition)
        rel = self.__context.execute(ins)
        return rel
    
    def FindAll(self):
            ins = self.__userDataTable.select()
            rel = self.__context.execute(ins)
            return rel