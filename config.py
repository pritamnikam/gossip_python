# the protocol version
PROTOCOL_VERSION = 0x01

# The interval in milliseconds between retry attempts.
MESSAGE_RETRY_INTERVAL = 10000

# The maximum number of attempts to deliver a message.
MESSAGE_RETRY_ATTEMPTS = 3

# The number of members that are used for further gossip propagation.
MESSAGE_RUMOR_FACTOR  = 3

# The maximum supported size of the message including a protocol overhead.
MESSAGE_MAX_SIZE     = 512

# The maximum number of unique messages that can be stored in the outbound message queue.
MAX_OUTPUT_MESSAGES   = 100

# The time interval in milliseconds that determines how often the Gossip tick event should be triggered.
GOSSIP_TICK_INTERVAL  = 1000

DATA_LOG_SIZE  = 25

# Gossip spread
GOSSIP_DIRECT = 0
GOSSIP_RANDOM = 1
GOSSIP_BROADCAST = 2


FORMAT = 'utf-8'