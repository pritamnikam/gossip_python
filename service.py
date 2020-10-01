import queue

import config
import state
import message
import member
import error
import vector_clock
import data_log
import message_service
import envolope
import message_handler


class GossipService:
    def __init__(self, self_address, data_receiver, data_receiver_context):
        self.input_buffer = []
        self.output_buffer = []
        self.output_buffer_offset = 0

        self.outbound_messages = []

        self.sequence_num = 0
        self.data_counter = 0
        self.data_version = vector_clock.VectorClock()

        self.state = state.STATE_INITIALIZED
        self.self_address = member.Member()

        self.members = member.MemberList(config.MAX_OUTPUT_MESSAGES)

        self.data_log = data_log.DataLog()

        self.last_gossip_ts = 0

        self.data_receiver = data_receiver
        self.messaging_service = message_service.UDPMessageService()

        self.data_receiver_context = data_receiver_context
        self.message_handler = message_handler.MessageHandler(self)

    # Send the message to the receipient
    def send(self):
        if (self.state != state.STATE_JOINING and self.state != state.STATE_CONNECTED):
             return False

        pass

    
    # Read the message from peer
    def receive(self):
        if (self.state != state.STATE_JOINING and self.state != state.STATE_CONNECTED):
             return False

        self.input_buffer, addr = self.messaging_service.recv_from()
        env = envolope.MessageEnvolopeIn()
        env.buffer = self.input_buffer
        env.buffer_size = len(self.input_buffer)
        env.sender = addr
        return True


    # Join the cluster
    def join(self, seed_nodes):
        if (self.state != state.STATE_INITIALIZED):
            return False

        if (seed_nodes == None or len(seed_nodes) == 0):
            # No seed nodes were provided.
            self.state = state.STATE_CONNECTED
            return True
        
        for node in seed_nodes:
            self.enqueue_hello(node.addr)
        
        self.state = state.STATE_JOINING
        
        return True

    # Send the data to recipient node
    def send_data(self, payload, recipient):
        if (self.state != state.STATE_JOINING and self.state != state.STATE_CONNECTED):
             return False

        return self.enqueue_data(payload, recipient)

    # Time tickes before sending next data
    def tick(self):
        if (self.state != state.STATE_CONNECTED):
            return False

        next_gossip_ts = self.last_gossip_ts + config.GOSSIP_TICK_INTERVAL
        current_ts = pt_time()
        if (next_gossip_ts > current_ts):
            return next_gossip_ts - current_ts
        
        enqueued_result = self.enqueue_status(None, 0)
        if (enqueued_result < 0):
            return enqueued_result

        self.last_gossip_ts = current_ts
        return True

    # Current state of this node
    def current_state(self):
        return self.state

    # Socket used by node for IO
    def socket_fd(self):
        return self.messaging_service.socket_fd()

    # Clear the outbound message queue
    def clear_envolope(self):
        self.outbound_messages = []

    # Append the message to the outbound queue
    def enqueue_envolope(self, env):
        self.outbound_messages.append(env)

    # Remove the message from the outbound queue
    def dequeue_envolope(self, env):
        del self.outbound_messages[env]

    # Find the message by it's 'sequence_num'
    def find_envolope_by_sequence_num(self, sequence_num):
        for env in self.outbound_messages:
            if env.sequence_num == sequence_num:
                return env

        return False

    # Add the messages to the outbound queue

    # Hello message
    def enqueue_hello(self, recipient):
        hello = message.Hello(message.MESSAGE_HELLO_TYPE, 0)
        hello.this_member = self.self_address
        return self.enqueue_message(hello, recipient, config.GOSSIP_DIRECT)

    # Ack message
    def enqueue_ack(self, sequence_num, recipient):
        ack = message.Ack(message.MESSAGE_ACK_TYPE, 0)
        ack.sequence_num = sequence_num
        return self.enqueue_message(ack, recipient, config.GOSSIP_DIRECT)

    # Welcome message
    def enqueue_welcome(self, hello_sequence_num, recipient):
        welcome = message.Welcome(message.MESSAGE_WELCOME_TYPE, 0)
        welcome.hello_sequence_num = hello_sequence_num
        welcome.this_member = self.self_address
        return self.enqueue_message(welcome, recipient, config.GOSSIP_DIRECT)

    # Staus message
    def enqueue_status(self, recipient):
        status = message.Status(message.MESSAGE_STATUS_TYPE, 0)
        status.data_version.copy(self.data_version)
        spreading_type = config.GOSSIP_DIRECT
        if recipient == None:
           spreading_type = config.GOSSIP_RANDOM

        return self.enqueue_message(status, recipient, spreading_type)

    # Data message
    def enqueue_data(self, payload, recipient):
        # Update the local data version.
        self.data_counter += 1
        clock_counter = self.data_counter
        record = self.data_version.set(self.self_address, clock_counter)

        data = message.Data(message.MESSAGE_DATA_TYPE, 0)
        record.copy(data.data_version)
        data.data = payload
        data.data_size = len(payload)

        # Add the data to our internal log.
        self.data_log.gossip_data_log(data)
        return self.enqueue_message(data, recipient, config.GOSSIP_DIRECT)

    # Data log message
    def enqueue_data_log(self, recipient_version, recipient):
        result = True
        for i in range(self.data_log.size):
            record = self.data_log.messages[i]
            result = recipient_version.compare_with_record(record.version, False)
            if (result == VC_BEFORE):
                # The recipient data version is behind. Enqueue this data payload.
                data = data_log_create_message(record)
                if not data:
                    return False

                result = self.enqueue_message(data, recipient, config.GOSSIP_DIRECT)
                if not result:
                    break

        return result

    # MemberList message
    def enqueue_member_list(self, recipient):
        member_list = message.MemberList(message.MESSAGE_MEMBER_LIST_TYPE, 0)

        members_num = self.members.get_size()
        if (members_num == 0):
            return True
        
        # Send the list of all known members to a recipient.
        # The list can be pretty big, so we split it into multiple messages.
        total = 0
        count = 0
        members_to_send = []
        for member in self.members.set:
            total += 1

            if (count == config.MEMBER_LIST_SYNC_SIZE or total == members_num):
                member_list.members = members_to_send
                member_list.members_n = count

                result = self.enqueue_message(member_list, 
                                             recipient,
                                             config.GOSSIP_DIRECT)
                if not result:
                    return False

                # reset                
                count = 0
                members_to_send = []
                continue
            
            count += 1
            members_to_send.append(member)
            
        return True


    # Helper to enque mesage to the outbound queue
    def enqueue_message(self, msg, recipient, spreading_type):
        offset = self.gossip_update_output_buffer_offset()
        buffer = self.output_buffer[offset:]

        encode_result, max_attempts = self.encode_message(msg)
        if not encode_result:
            return False

        # Distribute the message.
        if spreading_type == config.GOSSIP_DIRECT:
            # Send message to a single recipient.
            return self.enqueue_to_outbound(buffer, max_attempts, recipient)
        
        if spreading_type == config.GOSSIP_RANDOM:
            # Choose some number of random members to distribute the message.
            members = self.members.random_members(config.MESSAGE_RUMOR_FACTOR)

            for member in members:
                # Create a new envolope for each recipient.
                # Note: all created envolopes share the same buffer.
                result = self.enqueue_to_outbound(buffer, max_attempts, member.address)
                if not result:
                    return result

        if spreading_type == config.GOSSIP_BROADCAST:
            # Distribute the message to all known members.
            for member in self.members.get_set():
                # Create a new envolope for each recipient.
                # Note: all created envolopes share the same buffer.
                result = self.enqueue_to_outbound( buffer, max_attempts, member.address)
                if not result:
                    return result
    
        return True


    # Helper function to enque the encoded 'buffer' to the outbound queue
    def enqueue_to_outbound(self, buffer, max_attempts, receiver):
        self.sequence_num += 1
        seq_num = self.sequence_num
        new_envolope = envolope.MessageEnvolopeOut(seq_num,
                                                    buffer,
                                                    max_attempts,
                                                    receiver)
        self.outbound_messages.enqueue(new_envolope)
        return True


    # Helper to encode a message
    def encode_message(msg):
        max_attempts = config.MESSAGE_RETRY_ATTEMPTS
        encode_result = 0
        
        # Serialize the message.
        msg_type = msg.message_type
        encoded_msg = msg.encode()

        if (msg_type == message.MESSAGE_WELCOME_TYPE or msg_type == message.MESSAGE_ACK_TYPE):
            max_attempts = 1

        return encoded_msg, max_attempts

    def data_log_create_message(self, record, msg):
        data = message.Data(message.MESSAGE_DATA_TYPE, 0)
        msg.data_version.record_copy(record.version)
        msg.data = record.data
        msg.data_size = record.data_size
        return data

