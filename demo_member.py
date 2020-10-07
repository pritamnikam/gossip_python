import select
import socket
import sys

import config
import util
import service

class DemoMember:
    def __init__(self, my_address, seed_addresses, log_file):
        self.my_address = my_address
        self.seed_addresses = seed_addresses
        self.logger = util.create_logger(config.LOG_FORMATTING, log_file)
        self.poll_interval = config.GOSSIP_TICK_INTERVAL
        self.gossip_daemon = None

    def data_receiver(self, data):
        pass

    def start_helper(self):
        pass

    def run_helper(self):
        pass

    def start(self):
        self.logger.info('Staring a gossip service daemon.')

        # Create a new instance.
        self.gossip_daemon = service.GossipService(self_address = self.my_address,
                                                  data_receiver = self.data_receiver,
                                                  logger = self.logger)

        # Join enques the hello message
        self.gossip_daemon.join(self.seed_addresses)

        # Run the start helper before we start the run-loop.
        self.start_helper()

        # Runs a thread that does the I/O.
        self.run()

    def stop(self):
        self.gossip_daemon.stop()
        sys.exit(0)

    def run(self):
        self.logger.info('Staring a thread for I/O operations.')

        recv_result = 0
        send_result = 0

        # Retrieve the socket descriptor.
        daemon_fd = self.gossip_daemon.socket_fd()

        # infinite loop to perform I/O:
        while True:
            endpoints = [daemon_fd]
            poll_internal_in_seconds = self.poll_interval / 1000
            read, _, error = select.select(endpoints, [], [], poll_internal_in_seconds)

            for sock in read:
                if sock is daemon_fd:
                    try:
                        # Tell server to read a message from the socket.
                        recv_result = self.gossip_daemon.receive()
                        if not recv_result:
                            self.logger.warning("Receive failed.")
                            return False

                    except Exception as e:
                        self.logger.warning("Socket error - %s.", str(e))
                        return False

            for sock in error:
                self.logger.warning("Socket closed - %s.", sock)
                sock.close() 

            # Try to trigger the Gossip tick event and recalculate
            # the poll interval.
            self.poll_interval = self.gossip_daemon.tick()
            if (self.poll_interval < 0):
                self.logger.warning('Poll interval has expired.')
                return False

            # Just call before send takes place.
            self.run_helper()

            # Tell service to write existing messages to the socket.
            send_result = self.gossip_daemon.send()
            if not send_result:
                self.logger.warning('Send has failed %s', send_result)
                # return False
