import vector_clock
import message
import config


class DataLogRecord:
    def __init__(self):
        self.version = vector_clock.VectorRecord()
        self.data_size = 0
        self.data = []

    def create_message(self):
        msg = message.Data(message.MESSAGE_DATA_TYPE, 0)
        msg.data_version.Copy(self.version)
        msg.data = self.data.copy()
        msg.data_size = self.data_size
        return msg


class DataLog:
    def __init__(self):
        self.messages = []  # DataLogRecord
        self.size = 0
        self.current_idx = 0

    def gossip_data_log(self, msg):
        record = None
        for i in range(self.size):
            # Save only the latest data message from each originator.
            if (self.messages[i].version.member_id == msg.data_version.member_id):
                record = self.messages[i]
                record.version.sequence_number = msg.data_version.sequence_number
                break

        if (record == None):
            # The data message with the same originator was not found.
            new_idx = self.current_idx
            record = self.messages[new_idx]
            record.version.copy(msg.data_version)

            if (self.size < config.DATA_LOG_SIZE):
                self.size += 1

            self.current_idx += 1
            if (self.current_idx >= config.DATA_LOG_SIZE):
                self.current_idx = 0
        
        record.data_size = msg.data_size
        record.data = msg.data.copy()

