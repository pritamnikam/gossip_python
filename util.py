#!/usr/bin/python
import time
import math
import re
import socket
import logging

def get_time():
    ticks = time.time()
    return math.floor(ticks * 1000)   # in milliseconds

def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True

def is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    return True

def is_valid_ip_address(address):
    return is_valid_ipv4_address(address) or is_valid_ipv6_address(address)

def create_logger(formatter, path_to_file):
    logger = logging.getLogger()
    file_handler = logging.FileHandler(path_to_file, mode='w')
    file_handler.setFormatter(logging.Formatter(formatter))
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    return logger
