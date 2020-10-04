import message_handler_impl

class MessageHandlerFactory:
    __instance = None

    @staticmethod 
    def getInstance():
        if MessageHandlerFactory.__instance == None:
            MessageHandlerFactory()
        return MessageHandlerFactory.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if MessageHandlerFactory.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            MessageHandlerFactory.__instance = self

    def getHandler(self):
        return message_handler_impl.MessageHandlerImpl()
