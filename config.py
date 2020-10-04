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

# String for mat multi-addr
MULTI_ADDR_FORMAT = f'/ip/xxx.xxx.xxx.xxx/port/xxxxx'

# Size of a multi-addr address
MAX_MEMBER_ADDRESS_SIZE = len(MULTI_ADDR_FORMAT)

# Size of a single member
CLUSTER_MEMBER_SIZE = (4 + 4 + MAX_MEMBER_ADDRESS_SIZE)

# Membership list can grop really big.
MEMBER_LIST_SYNC_SIZE = (MESSAGE_MAX_SIZE / CLUSTER_MEMBER_SIZE)

DATA_LOG_SIZE  = 25

# Gossip spread
GOSSIP_DIRECT = 0
GOSSIP_RANDOM = 1
GOSSIP_BROADCAST = 2


FORMAT = 'utf-8'

LOG_FORMATTING = '%(asctime)-15s [%(levelname)s] %(message)s'