import queue

import config
import state
import member
import vector_clock
import data_log
import message_service
import envolope
import message_handler_factory
import member_address
import util
import message
import message_factory

class GossipService:
    def __init__(self, self_address, data_receiver, logger):
        self.logger = logger
        self.input_buffer = []
        self.output_buffer = []
        self.outbound_messages = []

        self.sequence_num = 0
        self.data_counter = 0
        self.data_version = vector_clock.VectorClock()
        self.state = state.STATE_INITIALIZED
        self.self_address = self_address
        self.this_member = member.Member.create(self_address)

        self.members = member.MemberList()
        self.data_log = data_log.DataLog()

        self.last_gossip_ts = 0
        self.data_receiver = data_receiver

        self.message_handler = message_handler_factory.MessageHandlerFactory.getInstance().getHandler()
        self.message_handler.set_service(self)
        self.message_handler.set_logger(self.logger)
        
        self.messaging_service = message_service.UDPMessageService(self.logger)
        self.messaging_service.bind(self_address)
        self.logger.info("[GossipService] Service started.")

    # Send the message to the receipient
    def send(self):
        if (self.state != state.STATE_JOINING and self.state != state.STATE_CONNECTED):
            self.logger.warning("Failed to send - not connected.")
            return False

        # get the first message from outbound message queue
        msg_sent = 0
        i = 0
        while i < len(self.outbound_messages):
            current_msg = self.outbound_messages[i]
            i += 1

            # The message exceeded the maximum number of attempts.
            if (current_msg.attempt_num >= current_msg.max_attempts):
                if (current_msg.max_attempts > 1):
                    # If the number of maximum attempts is more than 1, then
                    # the message required acknowledgement but we've never received it.
                    # Remove node from the list since it's unreachable.
                    self.members.remove_by_addr(current_msg.recipient)

                    # Quite often the same recipient has several messages in a row.
                    # Check whether the next message should be removed as well.
                    j = 1 + i
                    while j < len(self.outbound_messages):
                        next_msg = self.outbound_messages[j]
                        j += 1
                        if (current_msg.recipient == next_msg.recipient):
                            self.dequeue_envolope(next_msg)
                            continue
                        
                        break

                    # Remove this message from the queue.
                    self.dequeue_envolope(current_msg)
                    continue
            
            current_ts = util.get_time()

            # It's not yet time to retry this message.
            if (current_msg.attempt_num != 0 and
                (current_msg.attempt_ts + config.MESSAGE_RETRY_INTERVAL) > current_ts):
                continue
            
            # Send to recipient
            sent = self.messaging_service.send_to(current_msg.buffer, current_msg.recipient)
            if not sent:
                self.logger.warning("Failed to send %s - error in messaging service.", current_msg.recipient.to_multiaddr())
                return False
            
            self.logger.info("[GossipService] Message sent to %s", current_msg.recipient.to_multiaddr())

            # increament the attempt counts
            current_msg.attempt_ts = current_ts
            current_msg.attempt_num += 1
            msg_sent += 1

            # The message must be sent only once. Remove it immediately.
            if (current_msg.max_attempts <= 1):
                self.dequeue_envolope(current_msg)

        return msg_sent

    # Read the message from peer
    def receive(self):
        # Only receive iff node has requested to join or connected to the cluster.
        if (self.state != state.STATE_JOINING and self.state != state.STATE_CONNECTED):
            self.logger.warning("Failed to receive - not connected.")
            return False

        # Read the payload from messaging service and add to envolope and dispatch
        self.input_buffer, sender_address = self.messaging_service.recv_from()
        self.logger.info("[GossipService] Message received from %s", sender_address.to_multiaddr())

        envolope_in = envolope.MessageEnvolopeIn(self.input_buffer, sender_address)
        return self.message_handler.handle_new_message(envolope_in)


    # Join the cluster
    def join(self, seed_nodes):
        # Node can join only if it's initialized
        if (self.state != state.STATE_INITIALIZED):
            self.logger.warning("Failed to join - not in init state.")
            return False

        # No seed nodes were provided, then it's a supernode
        if len(seed_nodes) == 0:
            self.logger.info("[GossipService] Seed node started.")
            self.state = state.STATE_CONNECTED
            return True
        
        # say hello to all seed nodes to join the cluster
        for node in seed_nodes:
            self.enqueue_hello(node)
        
        self.logger.info("[GossipService] Node requested to join the cluster.")
        self.state = state.STATE_JOINING
        return True


    # Send the data to recipient node
    def send_data(self, payload, recipient=None):
        # Only allowed to send data iff node has requested to join or connected to the cluster.
        if (self.state != state.STATE_JOINING and self.state != state.STATE_CONNECTED):
            self.logger.warning("Failed to send_data - not connected.")
            return False

        return self.enqueue_data(payload, recipient)


    # Time tickes before sending next data
    def tick(self):
        if (self.state != state.STATE_CONNECTED):
            self.logger.warning("Failed to tick - not connected.")
            return False

        next_gossip_ts = self.last_gossip_ts + config.GOSSIP_TICK_INTERVAL
        current_ts = util.get_time()
        if (next_gossip_ts > current_ts):
            return next_gossip_ts - current_ts
        
        enqueued_result = self.enqueue_status(None)
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
        self.outbound_messages.remove(env)

    # Find the message by it's 'sequence_num'
    def find_envolope_by_sequence_num(self, sequence_num):
        for env in self.outbound_messages:
            if env.sequence_num == sequence_num:
                return env

        return False

    # Add the messages to the outbound queue

    # Hello message
    def enqueue_hello(self, recipient):
        self.logger.info("[GossipService] Enque Hello message to %s", recipient.to_multiaddr())
        hello = message_factory.MessageFactory.getInstance().create(message.MESSAGE_HELLO_TYPE)
        hello.this_member = self.this_member
        return self.enqueue_message(hello, recipient, config.GOSSIP_DIRECT)

    # Ack message
    def enqueue_ack(self, sequence_num, recipient):
        self.logger.info("[GossipService] Enque Ack message to %s", recipient.to_multiaddr())
        ack = message_factory.MessageFactory.getInstance().create(message.MESSAGE_ACK_TYPE)
        ack.sequence_num = sequence_num
        return self.enqueue_message(ack, recipient, config.GOSSIP_DIRECT)

    # Welcome message
    def enqueue_welcome(self, hello_sequence_num, recipient):
        self.logger.info("[GossipService] Enque Welcom message to %s", recipient.to_multiaddr())
        welcome = message_factory.MessageFactory.getInstance().create(message.MESSAGE_WELCOME_TYPE)
        welcome.hello_sequence_num = hello_sequence_num
        welcome.this_member = self.this_member
        return self.enqueue_message(welcome, recipient, config.GOSSIP_DIRECT)

    # Staus message
    def enqueue_status(self, recipient):
        if recipient == None:
            self.logger.info("[GossipService] Gossip the Status message.")
        else:
            self.logger.info("[GossipService] Enque Status message to %s", recipient.to_multiaddr())
        status = message_factory.MessageFactory.getInstance().create(message.MESSAGE_STATUS_TYPE)
        status.data_version.copy(self.data_version)
        spreading_type = config.GOSSIP_DIRECT
        if recipient == None:
           spreading_type = config.GOSSIP_RANDOM

        return self.enqueue_message(status, recipient, spreading_type)

    # Data message
    def enqueue_data(self, payload, recipient=None):
        spreading_type = config.GOSSIP_DIRECT
        if recipient is None:
            spreading_type = config.GOSSIP_RANDOM

        self.logger.info("[GossipService] Enque Data message.")
        # Update the local data version.
        self.data_counter += 1
        clock_counter = self.data_counter
        record = self.data_version.set_sequence_number_for_member(self.this_member, clock_counter)
        if not record:
            return False

        data = message_factory.MessageFactory.getInstance().create(message.MESSAGE_DATA_TYPE)
        record.copy(data.data_version)
        data.data = payload
        data.data_size = len(payload)

        # Add the data to our internal log.
        self.data_log.add_data_log(data)

        # Enque the data to outbound message queue to be dispatched
        return self.enqueue_message(data, recipient, spreading_type)

    # Data log message
    def enqueue_data_log(self, recipient_version, recipient):
        self.logger.info("[GossipService] Enque DataLog to %s", recipient.to_multiaddr())
        result = True
        for i in range(len(self.data_log.records)):
            record = self.data_log.records[i]
            result = recipient_version.compare_with_record(record.version, False)
            if (result == vector_clock.VC_BEFORE):
                # The recipient data version is behind. Enqueue this data payload.
                data = record.create_data_message()
                if not data:
                    return False

                result = self.enqueue_message(data, recipient, config.GOSSIP_DIRECT)
                if not result:
                    break

        return result

    # MemberList message
    def enqueue_member_list(self, recipient):
        self.logger.info("[GossipService] Enque MemberList message to %s", recipient.to_multiaddr())
        member_list = message_factory.MessageFactory.getInstance().create(message.MESSAGE_MEMBER_LIST_TYPE)

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

                result = self.enqueue_message(member_list, recipient, config.GOSSIP_DIRECT)
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
        encoded_msg, max_attempts = self.encode_message(msg)
        if not encoded_msg:
            self.logger.warning("Failed to enque message - encode error.")
            return False

        # Distribute the message.
        if spreading_type == config.GOSSIP_DIRECT:
            # Send message to a single recipient.
            return self.enqueue_to_outbound(encoded_msg, max_attempts, recipient)
        
        if spreading_type == config.GOSSIP_RANDOM:
            # Choose some number of random members to distribute the message.
            members = self.members.random_members(config.MESSAGE_RUMOR_FACTOR)

            for member in members:
                # Create a new envolope for each recipient.
                # Note: all created envolopes share the same buffer.
                result = self.enqueue_to_outbound(encoded_msg, max_attempts, member.address)
                if not result:
                    return result

        if spreading_type == config.GOSSIP_BROADCAST:
            # Distribute the message to all known members.
            for member in self.members.get_set():
                # Create a new envolope for each recipient.
                # Note: all created envolopes share the same buffer.
                result = self.enqueue_to_outbound(encoded_msg, max_attempts, member.address)
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
        self.outbound_messages.append(new_envolope)
        return True

    # Helper to encode a message
    def encode_message(self, msg):
        max_attempts = config.MESSAGE_RETRY_ATTEMPTS

        # Serialize the message.
        encoded_msg = msg.encode()

        if (msg.message_type == message.MESSAGE_WELCOME_TYPE or msg.message_type == message.MESSAGE_ACK_TYPE):
            max_attempts = 1

        return encoded_msg, max_attempts

    def data_log_create_message(self, record, msg):
        data = message.Data(message.MESSAGE_DATA_TYPE, 0)
        msg.data_version.record_copy(record.version)
        msg.data = record.data
        msg.data_size = record.data_size
        return data
