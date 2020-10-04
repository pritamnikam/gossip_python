import config
import demo_member
import util
import member_address

class NodeMember(demo_member.DemoMember):
    def __init__(self, address, seed_addresses, log_file):
        demo_member.DemoMember.__init__(self, address, seed_addresses, log_file)
        
        # send data every 5 seconds
        self.send_data_interval = 5
        self.previous_data_msg_ts = util.get_time()

    def data_receiver(self, data):
        self.logger.info('data: %s', data)

    def start_helper(self):
        # Force service to send a Hello message.
        self.gossip_daemon.send()

        self.previous_data_msg_ts = util.get_time()

    def run_helper(self):
        # Send some data periodically.
        current_time = util.get_time()
        if (self.previous_data_msg_ts + self.send_data_interval <= current_time):
            self.previous_data_msg_ts = current_time
            encoded_message_with_ts = bytes(f'Hi there! {self.previous_data_msg_ts}', config.FORMAT)
            encoded_message_size = bytes(f'{len(encoded_message_with_ts):>04}', config.FORMAT)
            composit_encoded_messsage = encoded_message_size + encoded_message_with_ts
            self.gossip_daemon.send_data(composit_encoded_messsage, self.seed_addresses[0])

if __name__ == "__main__":
    LOG_FILE = 'log_demo_node.txt'
    my_address = member_address.Address.from_multiaddr('/ip/127.0.0.1/port/7070')
    seed_address = member_address.Address.from_multiaddr('/ip/127.0.0.1/port/8080')
    node = NodeMember(my_address, [seed_address], LOG_FILE)
    node.start()
