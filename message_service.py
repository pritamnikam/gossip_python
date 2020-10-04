import socket

import config
import member_address
import util

class MessageService:
    def __init__(self):
        pass

    def socket_fd(self):
        pass
    
    def bind(self, address):
        pass

    def recv_from(self):
        pass

    def send_to(self, message, address):
        pass

    def close(self):
        pass

    def get_sock_name(self):
        pass

class UDPMessageService(MessageService):
    def __init__(self, logger):
        MessageService.__init__(self)
        self.logger = logger
        self.logger.info('[UDPMessageService] Ctor.')
        self.fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.fd.setblocking(0)

    def bind(self, address):
        self.logger.info('[UDPMessageService] Bind to: %s', address.to_multiaddr())
        self.fd.bind((address.ip, address.port))

    def recv_from(self):
        try:
            data, address = self.fd.recvfrom(1024)
            sender = member_address.Address()
            sender.ip = address[0]
            sender.port = int(address[1])
            return data, sender
        except Exception as e:
            self.logger.warning('[UDPMessageService] Socket read faild. %s', str(e))
            raise e

    def send_to(self, message, address):
        if not util.is_valid_ip_address(address.ip):
            self.logger.warning('[UDPMessageService] Send failed - IP address is invalid.')
            return False
        try:
            bytes_sent = self.fd.sendto(message, (address.ip, address.port))
            self.logger.info('[UDPMessageService] Socket sent: %s', bytes_sent)
            return True
        except Exception as e:
            self.logger.warning('[UDPMessageService] Socket send faild. %s', str(e))
            return False

    def close(self):
        self.fd.close()

    def get_sock_name(self):
        return self.fd.getsockname()

    def socket_fd(self):
        return self.fd