from Repository.userDataRepo import userDataRepo
from Model.userData import userData
from sqlalchemy import Table
from sqlalchemy.engine.base import Connection


class MetaUserDataServices(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(MetaUserDataServices, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class userDataServices(metaclass=MetaUserDataServices):
    __userDataRepo: userDataRepo
    
    def __init__(self, UserDataTable: Table, context: Connection):
        self.__userDataRepo = userDataRepo(UserDataTable, context=context)
        
    def AddNewUserData(self, newUserData: userData):

        self.__userDataRepo.CreateWithParams(newUserData)
        
    def UpdateUserDataById(self, id: int, newUserData: userData):
        self.__userDataRepo.UpdateById(id, newUserData)
        
    def FindUserDataById(self, id:int):
        rel = self.__userDataRepo.FindwithId(Id=id)
        return rel