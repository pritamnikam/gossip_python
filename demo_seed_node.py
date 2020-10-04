import config
import demo_member
import util
import member_address

class SeedNodeMember(demo_member.DemoMember):
    def __init__(self, address, log_file):
        demo_member.DemoMember.__init__(self, address, [], log_file)

    def data_receiver(self, data):
        self.logger.info('data: %s', data)

    def start_helper(self):
        pass 

    def run_helper(self):
        pass

if __name__ == "__main__":
    LOG_FILE = 'log_demo_seed_node.txt'
    my_address = member_address.Address.from_multiaddr('/ip/127.0.0.1/port/8080')
    node = SeedNodeMember(my_address, LOG_FILE)
    node.start()