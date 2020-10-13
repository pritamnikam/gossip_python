import sys

import config
import member_address
import member

VC_BEFORE = 0
VC_AFTER  = 1
VC_EQUAL  = 2
VC_CONFLICT  = 3

class VectorRecord:
    def __init__(self, sequence_number = 0, member_id = ''):
        self.sequence_number = sequence_number
        self.member_id = member_id

    def size(self):
        return sys.getsizeof(self.sequence_number) + len(self.member_id)

    def decode(self, buffer):
        self.sequence_number = int(buffer[:4].decode(config.FORMAT).strip()) # 4-bytes
        member_id_length = int(buffer[4:8].decode(config.FORMAT).strip())    # 4-bytes
        self.member_id = buffer[8:member_id_length+8].decode(config.FORMAT)
        return 8 + member_id_length

    def encode(self):
        encoded_sequence_number = bytes(f'{self.sequence_number:>04}', config.FORMAT)  # 4-byte
        encoded_member_id_length = bytes(f'{len(self.member_id):>04}', config.FORMAT)  # 4-byte
        encoded_member_id = bytes(f'{self.member_id}', config.FORMAT)                  # member_id_length-bytes
        return encoded_sequence_number + encoded_member_id_length + encoded_member_id

    def to_string(self):
        return f'(sequence_number: {self.sequence_number}, member_id: {self.member_id})'

    def copy(self, other):
        self.member_id = other.member_id
        self.sequence_number = other.sequence_number

class VectorClock:
    def __init__(self):
        self.current_idx = 0
        self.records = []  # VectorRecord
        self.cache = {}    # map<member_id, VectorRecord>
        self.capacity = config.MESSAGE_MAX_SIZE
    
    def size(self):
        total_size = 0
        for record in self.records:
           total_size += record.size()

        return total_size

    def find_record(self, member):
        member_id = create_member_id(member)
        if not member_id:
            return False

        if not member_id in self.cache:
            return False

        return self.cache[member_id]

    def set_sequence_number_for_member(self, member, seq_num):
        member_id = create_member_id(member)
        return self.set_sequence_number_by_id(member_id, seq_num)
        
    def set_sequence_number_by_id(self, member_id, sequence_number):
        # insert (or override) the latest record with the new record.
        if not member_id in self.cache:
            # Add the entry to records
            record = VectorRecord(sequence_number, member_id)
            
            # capacity full
            if self.size() >= self.capacity:
                self.records.pop()

        else:
            record = self.cache[member_id]
            self.records.remove(record)
            record.sequence_number = sequence_number

        self.cache[member_id] = record
        self.records.insert(0, record)
        return record


    def increment_sequence_number_for_member(self, member):
        member_id = create_member_id(member)
        record = self.find_record(member)
        if not record:
            return False
        
        del self.records[record]
        record.sequence_number += 1
        self.cache[member_id] = record
        self.records.insert(0, record)
        return record

    def to_string(self):
        str = f'current_idx: {self.current_idx}, records: ['
        for record in self.records:
            str += record.to_string()
            str += ', '
        
        return str + ' ]'

    def copy(self, other):
        self.records = []
        self.current_idx = other.current_idx
        for record in other.records:
            self.records.append(record)

    def resolve_comp_result(self, old, new):
        if old != VC_EQUAL and new != old:
            return VC_CONFLICT
        return new

    def compare(self, other, merge):
        result = VC_EQUAL
        for record in self.records:
            found = other.find_by_member_id(record.member_id)
            if not found:
                result = self.resolve_comp_result(result, VC_AFTER)
            else:
                first_seq_num = record.sequence_number
                second_seq_num = found.sequence_number
                if (first_seq_num > second_seq_num):
                    result = self.resolve_comp_result(result, VC_AFTER)
                else:
                    if (second_seq_num > first_seq_num):
                        result = self.resolve_comp_result(result, VC_BEFORE)
                        if merge:
                            record.sequence_number = second_seq_num

        return result

    def compare_with_record(self, record, merge):
        result = VC_EQUAL
        found = self.find_by_member_id(record.member_id)
        if not found:
            result = VC_BEFORE
            if merge:
                self.set_sequence_number_by_id(record.member_id, record.sequence_number)
        else:
            first_seq_num = found.sequence_number
            second_seq_num = record.sequence_number
            if (first_seq_num > second_seq_num):
                result = VC_AFTER
            else:
                if (first_seq_num < second_seq_num):
                    result = VC_BEFORE
                    if merge:
                        found.sequence_number = second_seq_num


        return result

    def decode(self, buffer):
        self.current_idx = int(buffer[:4].decode(config.FORMAT).strip()) # 4-bytes
        size = int(buffer[4:8].decode(config.FORMAT).strip())            # 4-bytes

        bytes_decoded = 8
        i = 0
        while i < size:
            i += 1
            record = VectorRecord()
            bytes_decoded += record.decode(buffer[bytes_decoded:])
            self.records.append(record)
        
        return bytes_decoded

    def encode(self):
        encoded_current_idx = bytes(f'{self.current_idx:>04}', config.FORMAT)  # 4-byte
        encoded_size = bytes(f'{len(self.records):>04}', config.FORMAT)        # 4-byte
        composit_encoded_message = encoded_current_idx + encoded_size
        for record in self.records:
            encoded_record = record.encode()
            composit_encoded_message += encoded_record
        
        return composit_encoded_message

    def find_by_member_id(self, member_id):
        for member in self.records:
            if (member.member_id == member_id):
                return member
        return False

# multi addrs format member-id
def create_member_id(member):
    return f'{member.address.to_multiaddr()}/uid/{member.uid}'

