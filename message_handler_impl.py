import message_handler

import config
import message
import state
import vector_clock
import member
import member_address
import envolope
import util

class MessageHandlerImpl(message_handler.MessageHandler):
    def __init__(self):
        message_handler.MessageHandler.__init__(self)

    def handle_hello(self, envelope_in):
        # Proceed only if connected
        if self.gossip_service.current_state() != state.STATE_CONNECTED:
            return False

        self.logger.info('[MessageHandler] Handle Hello message.')

        # 1. Decode the message
        hello = message.Hello(message.MESSAGE_HELLO_TYPE, 0)
        decode_bytes = hello.decode(envelope_in.buffer)
        if not decode_bytes:
            return False
        
        # 2. Send back a Welcome message.
        self.gossip_service.enqueue_welcome(hello.sequence_num, envelope_in.sender)

        # 3. Send the list of known members to a newcomer node.
        if self.gossip_service.members.get_size():
            self.gossip_service.enqueue_member_list(envelope_in.sender)

        # 4. Notify other nodes about a newcomer.
        member_list_msg = message.MemberList(message.MESSAGE_MEMBER_LIST_TYPE, 0)
        member_list_msg.members.append(hello.this_member)
        self.gossip_service.enqueue_message(member_list_msg,
                                            None,
                                            config.GOSSIP_BROADCAST)

        # 5. Update our local storage with a new member.
        self.gossip_service.members.put([hello.this_member])
        return True


    def handle_welcome(self, envelope_in):
        # Proceed only if not connected
        if self.gossip_service.current_state() == state.STATE_CONNECTED:
            return False

        self.logger.info('[MessageHandler] Handle Welcome message.')

        # 1. Decode the welcome message
        welcome = message.Welcome(message.MESSAGE_WELCOME_TYPE, 0)
        decode_bytes = welcome.decode(envelope_in.buffer)
        if not decode_bytes:
            self.logger.warning("[MessageHandler] Decode for welcome message failed.")
            return False

        # 2. Mark the state as connected and add to the member list
        self.gossip_service.state = state.STATE_CONNECTED

        self.logger.info('[MessageHandler] Node is connected to the cluster.')

        # Now when the seed node responded we can
        # safely add it to the list of known members.
        self.gossip_service.members.put([welcome.this_member])

        # 3. Remove the hello message from the outbound queue.
        env = self.gossip_service.find_envolope_by_sequence_num(welcome.sequence_num)
        if not env:
            self.logger.warning("[MessageHandler] Sequence number didn't match. Received %s", welcome.sequence_num)
        else:
            self.gossip_service.dequeue_envolope(env)

        return True


    def handle_ack(self, envelope_in):
        # Proceed only if connected
        if self.gossip_service.current_state() != state.STATE_CONNECTED:
            return False

        self.logger.info('[MessageHandler] Handle Ack message.')

        # 1. Decode the membership list message
        ack = message.Ack(message.MESSAGE_ACK_TYPE, 0)
        decoded_bytes = ack.decode(envelope_in.buffer)
        if not decoded_bytes:
            return False

        # 2. Removing the processed message from the outbound queue.
        ack_envelope = self.gossip_service.find_envolope_by_sequence_num(ack.ack_sequence_num)
        if ack_envelope:
            self.gossip_service.dequeue_envolope(ack_envelope)

        return True


    def handle_data(self, envelope_in):
        # Proceed only if connected
        if self.gossip_service.current_state() != state.STATE_CONNECTED:
            return False

        self.logger.info('[MessageHandler] Handle Data message.')

        # 1. Decode the data list message
        data = message.Data(message.MESSAGE_DATA_TYPE, 0)
        decoded_bytes = data.decode(envelope_in.buffer)
        if not decoded_bytes:
            return False

        # 2. Send ACK message back to sender.
        self.gossip_service.enqueue_ack(data.sequence_num, envelope_in.sender)

        # 3. Verify whether we saw the arrived message before.
        res = self.gossip_service.data_version.compare_with_record(data.data_version, True)

        if (res == vector_clock.VC_BEFORE):
            # 3a. Add the data to our internal log.
            self.gossip_service.data_log.add_data_log(data)

            if (self.gossip_service.data_receiver):
                # 3b. Invoke the data receiver callback specified by the user.
                self.gossip_service.data_receiver(data.data)
            
            # 3c. Enqueue the same message to send it to N random members later.
            self.gossip_service.enqueue_message(data,
                                                None,
                                                config.GOSSIP_RANDOM)
        
        return True


    def handle_status(self, envelope_in):
        # Proceed only if connected
        if self.gossip_service.current_state() != state.STATE_CONNECTED:
            return False

        self.logger.info('[MessageHandler] Handle Status message.')

        # 1. Decode the status message
        status = message.Status(message.MESSAGE_STATUS_TYPE, 0)
        decoded_bytes = status.decode(envelope_in.buffer)
        if not decoded_bytes:
            return False

        # 2. Acknowledge the arrived Status message.
        self.gossip_service.enqueue_ack(status.sequence_num, envelope_in.sender)

        result = self.gossip_service.data_version.compare(status.data_version, False)
        if result == vector_clock.VC_AFTER:
            # The remote node is missing some of the data messages.
            self.gossip_service.enqueue_data_log(status.data_version,
                                                    envelope_in.sender)

        else:
            if result == vector_clock.VC_BEFORE:
                # This node is behind. Send back the Status message to request the data update.
                self.gossip_service.enqueue_status(envelope_in.sender)

            else: # if result == vector_clock.VC_CONFLICT:
                # The conflict occurred. Both nodes should exchange the data with each other.
                # Send the data messages from the log.
                self.gossip_service.enqueue_data_log(status.data_version,
                                                    envelope_in.sender)

                # Request the data update.
                self.gossip_service.enqueue_status(envelope_in.sender)

        
        return True


    # Handles the new incoming message
    def handle_member_list(self, envelope_in):
        # Proceed only if connected
        if self.gossip_service.current_state() != state.STATE_CONNECTED:
            return False

        self.logger.info('[MessageHandler] Handle MemberList message.')

        # 1. Decode the membership list message
        membership_list = message.MemberList(message.MESSAGE_MEMBER_LIST_TYPE, 0)
        decoded_bytes = membership_list.decode(envelope_in.buffer)
        if not decoded_bytes:
            return False

        # 2. Update our local collection of members with arrived records.
        self.gossip_service.members.put(membership_list.members)

        # 3. Send ACK message back to sender.
        self.gossip_service.enqueue_ack(membership_list.sequence_num, envelope_in.sender)
        return True


    def handle_new_message(self, envelope_in):
        # Read the message type form the incoming envolope.
        message_type = message.decode_type(envelope_in.buffer)

        if message_type == message.MESSAGE_HELLO_TYPE:
            return self.handle_hello(envelope_in)

        if message_type == message.MESSAGE_WELCOME_TYPE:
            return self.handle_welcome(envelope_in)

        if message_type == message.MESSAGE_MEMBER_LIST_TYPE:
            return self.handle_member_list(envelope_in)

        if message_type == message.MESSAGE_DATA_TYPE:
            return self.handle_data(envelope_in)

        if message_type == message.MESSAGE_ACK_TYPE:
            return self.handle_ack(envelope_in)

        if message_type == message.MESSAGE_STATUS_TYPE:
            return self.handle_status(envelope_in)

        return False
