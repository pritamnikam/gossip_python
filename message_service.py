import socket

import config

class MessageService:
    def __init__(self):
        pass

    def socket_fd(self, domain, type):
        pass
    
    def bind(self, ip, port):
        pass

    def recv_from(self):
        pass

    def send_to(self, message, ip, port):
        pass

    def close(self):
        pass

    def get_sock_name(self):
        pass

class UDPMessageService(MessageService):
    def __init__(self):
        super.__init__(self)
        self.socket_fd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def bind(self, ip, port):
        self.socket_fd.bind((ip, port))

    def recv_from(self):
        data, address = self.socket_fd.recvfrom(1024)
        return data, address

    def send_to(self, message, ip, port):
        self.socket_fd.sendto(message, (ip, port))

    def close(self):
        self.socket_fd.close()

    def get_sock_name(self):
        return self.socket_fd.getsockname()
