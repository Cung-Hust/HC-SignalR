from abc import ABCMeta, abstractmethod


class IHandler(metaclass=ABCMeta):
    @abstractmethod
    def handler_mqtt_command(self, item):
        pass

    @abstractmethod
    def handler_mqtt_response(self, item):
        pass

    @abstractmethod
    def handler_signalr_command(self, item):
        pass

    @abstractmethod
    def handler_signalr_response(self, item):
        pass
