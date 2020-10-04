import message

class MessageFactory:
    __instance = None

    @staticmethod 
    def getInstance():
        if MessageFactory.__instance == None:
            MessageFactory()
        return MessageFactory.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if MessageFactory.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            MessageFactory.__instance = self

    def create(self, message_type, sequence_number = 0):
        if message_type == message.MESSAGE_HELLO_TYPE:
            return message.Hello(message_type, sequence_number)

        if message_type == message.MESSAGE_WELCOME_TYPE:
            return message.Welcome(message_type, sequence_number)

        if message_type == message.MESSAGE_ACK_TYPE:
            return message.Ack(message_type, sequence_number)

        if message_type == message.MESSAGE_MEMBER_LIST_TYPE:
            return message.MemberList(message_type, sequence_number)

        if message_type == message.MESSAGE_DATA_TYPE:
            return message.Data(message_type, sequence_number)

        if message_type == message.MESSAGE_STATUS_TYPE:
            return message.Status(message_type, sequence_number)

        return False
