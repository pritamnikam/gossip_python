# Gossip Protocol Implementation in Python

## Description
Gossip Protocol in Python - is an extremely small gossip protocol implementation in python. Its main goal is a data dissemination rather than membership management.

The crucial features and advantages of 'Gossip Protocol' are the following:
* Allows to build a fully decentralized P2P cluster (without a single server instance).
* Gossip Protocol is a very lightweight with zero external dependencies.
* Utilizes UDP for the transport layer.
* Very tiny and adjustable memory footprint.
* Small protocol overhead.
* The data spreading is pretty fast.

Don't expect from Gossip Protocol the following:
* Cluster membership tracking and management.
As mentioned above it's a dissemination protocol. This means that each node has to be aware only of a small part of the cluster to function properly. While it is pretty good in fast distribution of data across the cluster, it doesn't provide any guarantees about cluster convergence or data consistency (at least for now).

* Transferring of huge amounts of data.
Since UDP is not a reliable protocol, it imposes some restrictions on a maximum size of each packet (the larger size is - the higher risk to lose a packet). The default maximum message size for Gossip Protocol is 512 bytes (the value is configurable). This includes the protocol overhead, which is only few bytes for the data message. So by default the payload size shouldn't exceed 512 bytes per one message. This should be enough for a small command or notification.

So far neither the message delivery order nor the delivery itself have strong guarantees.

## How it's designed

* GossipService. A core service responsible for the peer-to-peer communication and composeses necessary data structures used while liftime of the service. This is only exposed service from this package.

* State. The nodes have lifetime states - INITIALIZED, JOINING, CONNECTED, DISCONNECTED and DISTROYED. Node starts with 'INITIALIZED' state does necessary data structure initializations required for joining the cluster, then temporaily moved to 'JOINING' state. In this state, it attempts to conenct to the cluster by sending a Hello message to the seed nodes. On receiving a Welcome message from the seed node, state transit to 'CONNECTED'. Node stays in this state

* Message. Every 'Message' has a fixed-size header of 8-bytes with 2-bytes 'message_type', 2-bytes 'reserved' bytes and 4-byte 'sequence_number'. Messages are encoded in 'utf-8' format before enclosed into 'MessageEnvolopeOut' and enqued to a outbound message queue before get dispatched. The envolope holds other useful meta information like 'recipient' address, 'attempt_num' and 'max_attempts' allowed for that type of message, for example, the maximum attempts are capped to '3' (configurable) except for Welcome and Ack messsages - they can be maximum 1.

* MessageService.
Gossip protocol uses UDP based messaging service to send and receive messages. GossipService periodically dispatches the messages from outbound message queues to the recipient.

* Spread Type. The Gossip protocol supports 3 types of message spreads – DIRECT, RANDOM and BROADCAST, to achieve the anti-entropy infection style message dissemination.

* MessageHandler. Once an encoded buffer is read over UDP socket, it gets enclosed into MessageEnvolopeIn and dispatch to the respective handler. The message header decoding shall confirm the type of the incoming message and respective message handler comes into action.

In short, the pipeline will be shown below:

[Message]
  -> [Message].encode
     -> Envolope{[Message].encode}
        -> socket.send_to

socket->recv_from
  -> Envolope{buffer}
    -> buffer.decode
       -> [Message]
          -> handle


## How to use
First of all import the Gossip Protocol service:
```python
import config
import member_address
import service
import util
```

Now instantiate a Gossip Protocol service and address of the current node and a data receiver callback:
```python
# Filling in the address of the current node.
my_address = member_address.Address.from_multiaddr('/ip/127.0.0.1/port/7070')

# A log file to collect debug logs
log_file = 'demo_log_file.txt'
logger = util.create_logger(config.LOG_FORMATTING, log_file)

# Create a new gossip service instance.
gossip_daemon = service.GossipService(self_address = my_address,
                                      data_receiver = data_receiver,
                                      logger = logger)
```

The data receiver callback may look like following:
```python
def data_receiver(data):
    # This function is invoked every time when a new data arrives.
    buffer_size = int(data[:4].decode(config.FORMAT).strip()) # 4-bytes
    buffer = buffer[4:4+buffer_size].decode(config.FORMAT)
    print(f"Data is: ${buffer}");
```

Joining a cluster:
There are 2 ways to do this:
1) specify the list of seed nodes that are used as entry points to a cluster or
2) specify nothing if this instance is going to be a seed node in itself.
```python
# Provide a seed node destination address.
seed_node_address = member_address.Address.from_multiaddr('/ip/127.0.0.1/port/8080')

# Join a cluster.
join_result = gossip_daemon.join([seed_node_address])
if not join_result:
    print('Failed to join'.)
    return
```

To force Gossip Protocol to read a message from the network:
```python
recv_result = gossip_daemon.receive(gossip)
if not recv_result:
    self.logger.warning("Receive failed.")
    return
```

To flush the outbound messages to the network:
```python
send_result = gossip_daemon.send()
if not send_result:
    print('Send failed.')
    return
```

In order to enable the anti-entropy in Gossip Protocol periodically call the gossip tick function:
```python
time_till_next_tick = gossip_daemon.tick()
if not time_till_next_tick:
    print('Tick failed.')
    return 
```

This function returns a time period in milliseconds which indicates when the next tick should occur. This time interval can be used to adjust yor `poll` or `select` timeout.

To spread (gossip) some data within a cluster:
```python
message = 'Hello Gossip!'
encoded_message = bytes(message, config.FORMAT)
encoded_message_size = bytes(f'{len(encoded_message):>04}', config.FORMAT)  # 4-bytes length
composit_encoded_messsage = encoded_message_size + encoded_message
gossip_daemon.send_data(composit_encoded_messsage)
```

For a more complete examples check out the `demo_node.py` and `demo_seed_node.py` demo applications. 

To run the demo seed node:
```shell
python demo_seed_node.py
```

To run the demo node:
```shell
python demo_node.py
```
