import vector_clock
import message
import config
import member
import member_address


class DataLogRecord:
    def __init__(self):
        self.version = vector_clock.VectorRecord()
        self.data = []

    def create_data_message(self):
        data = message.Data(message.MESSAGE_DATA_TYPE, 0)
        data.data_version.copy(self.version)
        data.data = self.data
        return data



class DataLog:
    def __init__(self):
        self.records = []  # DataLogRecord
        self.current_idx = 0

    def add_data_log(self, data_message):
        for record in self.records:
            if (record.version.member_id == data_message.data_version.member_id):
                # Save only the latest data message from each originator.
                record.data = data_message.data
                record.version.sequence_number = data_message.data_version.sequence_number
                return

        # The data message with the same originator was not found.
        record = DataLogRecord()
        record.data = data_message.data
        record.version.copy(data_message.data_version)
        self.records.append(record)


def test():
    m = member.Member()
    m.uid = '3243'
    m.address = member_address.Address.from_string('127.0.0.1:8080')    
    vr = vector_clock.VectorRecord()
    vr.sequence_number = 100
    vr.member_id = vector_clock.create_member_id(m)

    dt = message.Data(message.MESSAGE_DATA_TYPE, 100)
    dt.data_version = vr
    dt.data = bytes(f'test bytes', config.FORMAT)

    dl = DataLog()
    dl.add_data_log(dt)

    record = dl.records[0]
    dt1 = record.create_data_message()
    print('dt1 : ', dt1.data)

# test()

