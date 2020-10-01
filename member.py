import random

import config
import member_address

MEMBERS_INITIAL_CAPACITY = 32
MEMBERS_EXTENSION_FACTOR = 2
MEMBERS_LOAD_FACTOR = 0.75

class Member:
    def __init__(self, uid=0, version=config.PROTOCOL_VERSION, address=member_address.Address()):
        self.version = config.PROTOCOL_VERSION
        self.uid = uid
        self.address = address

    def copy(self, member):
        member.version = self.version
        member.uid = self.uid
        member.address = self.address

    def equals(self, member):
        return (self.uid == member.uid and
               self.version == member.version and
               self.address.equals(member.address))

    def destroy(self):
        pass

    def decode(self, buffer):
        self.version = int(buffer[:4].decode(config.FORMAT).strip())   # 4-byte
        self.uid = int(buffer[4:8].decode(config.FORMAT).strip())      # 4-bytes
        addr_decode = self.address.decode(buffer[8:])
        return 4 + 4 + addr_decode

    def encode(self):
        encoded_version = bytes(f'{self.version:>04}', config.FORMAT)  # 4-byte
        encoded_uid = bytes(f'{self.uid:>04}', config.FORMAT)          # 4-byte
        encoded_address = self.address.encode()
        return encoded_version + encoded_uid + encoded_address


class MemberList:
    def __init__(self):
        self.set = []

    def get_set(self):
        return self.set

    def get_size(self):
        return len(self.set)

    def encode(self):
        encoded_size = bytes(f'{self.get_size():>04}', config.FORMAT)    # 4-byte
        composit_encoded_message = encoded_size
        
        for member in self.set:
            encoded_message = member.encode()
            composit_encoded_message += encoded_message
        
        return composit_encoded_message

    def decode(self, buffer):
        size = int(buffer[:4].decode(config.FORMAT).strip())    # 4-byte

        offset = 4
        i = 0
        while(i < size):
            i += 1
            member = Member()
            offset += member.decode(buffer[offset:])
            self.set.append(member)

        return offset

    def put(self, new_members):
        members = []

        for new_member in new_members:
            exists = False
            for cur in self.set:
                if (cur.equals(new_member)):
                    exists = True
                    break

            if not exists:
                members.append(new_member)
        
        for candidate in members:
            self.set.append(candidate)

    def remove(self, member):
        exists = False
        for cur in self.set:
            if (cur.equals(member)):
                exists = True
                break
        
        if exists:
            del self.set[member]

    def find_by_addr(self, addr):
        for cur in self.set:
            if cur.address.equals(addr):
                return cur
        
        return False

    def remove_by_addr(self, addr):
        id = 0
        for cur in self.set:
            if cur.address.equals(addr):
                del self.set[id]
                break
            id += 1

    def random_members(self, count):
        if (self.get_size() == 0):
            return False

        n = count
        if (self.get_size() < count):
            n = self.get_size()

        members = []
        selectedIndexes = set()
        while len(selectedIndexes) < n:
            selectedIndexes.add(random.randint(0, self.get_size()-1))
        
        for i in selectedIndexes:
            members.append(self.set[i])

        return members

    def destroy(self):
        self.set = []

def test():
    m = Member()
    m.address = member_address.from_string('127.0.0.1:8080')
    encoded_member = m.encode()

    n = Member()
    bytes_decoded = n.decode(encoded_member)

    print(f'{len(encoded_member)} and {bytes_decoded} -> {n.address.to_string()}')

    
    n.address = member_address.from_string('127.0.0.1:7172')

    ml = MemberList()
    new_members = []
    new_members.append(m)
    new_members.append(n)
    ml.put(new_members)

    encoded_member = ml.encode()
    ml2 = MemberList()
    bytes_decoded = ml2.decode(encoded_member)

    print(f'{len(encoded_member)} and {bytes_decoded} -> {ml2.set[0].address.to_string()}')

    m = ml.find_by_addr(n.address)
    print(m.address.to_string())

    new_members = []
    n.address = member_address.from_string('127.0.0.1:6161')
    new_members.append(n)

    ms = ml.random_members(2)
    print(len(ms))

    ms = ml.random_members(4)
    print(len(ms))

    ml.remove_by_addr(n.address)
    print(ml.get_size())

    ml.destroy()
    print(ml.get_size())

# test()