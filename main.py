############## PLEASE RUN THIS CELL FIRST! ###################

# import everything and define a test runner function
from tx import Tx, TxIn, TxOut
from script import p2pkh_script, Script
from network import (
    GetDataMessage,
    GetHeadersMessage,
    HeadersMessage,
    NetworkEnvelope,
    SimpleNode,
    TX_DATA_TYPE,
    FILTERED_BLOCK_DATA_TYPE,
)
from merkleblock import MerkleBlock
from helper import hash256, little_endian_to_int, encode_varint, read_varint, decode_base58, SIGHASH_ALL
from ecc import PrivateKey
from bloomfilter import BloomFilter
from block import Block
import time
from importlib import reload
from helper import run
import bloomfilter
import block
import ecc
import helper
import merkleblock
import network
import script
import tx


last_block_hex = '00000000000000085e9b87f63928d398f1a92c4abbd9773607f5bf99321a3109'  # FILL THIS IN

secret = little_endian_to_int(
    hash256(b'stm1051212@yahoo.co.jp'))  # FILL THIS IN
private_key = PrivateKey(secret=secret)
addr = private_key.point.address(testnet=True)
print("change_address:", addr)
h160 = decode_base58(addr)

target_address = 'mwJn1YPMq7y5F8J3LkC5Hxg9PHyZ5K4cFv'
target_h160 = decode_base58(target_address)
target_script = p2pkh_script(target_h160)
fee = 5000  # fee in satoshis


# connect to testnet.programmingbitcoin.com in testnet mode
node = SimpleNode('testnet.programmingbitcoin.com', testnet=True, logging=True)
# create a bloom filter of size 30 and 5 functions. Add a tweak.
bf = BloomFilter(size=30, function_count=5, tweak=90210)
# add the h160 to the bloom filter
bf.add(h160)
# complete the handshake
node.handshake()
# load the bloom filter with the filterload command
node.send(bf.filterload())
# set start block to last_block from above
start_block = bytes.fromhex(last_block_hex)
# send a getheaders message with the starting block
getheaders = GetHeadersMessage(start_block=start_block)
node.send(getheaders)
# wait for the headers message
headers = node.wait_for(HeadersMessage)
# store the last block as None
last_block = None
# initialize the GetDataMessage
getdata = GetDataMessage()
# loop through the blocks in the headers
for b in headers.blocks:
    # check that the proof of work on the block is valid
    if not b.check_pow():
        raise RuntimeError('proof of work is invalid')
    # check that this block's prev_block is the last block
    if last_block is not None and last_block != b.prev_block:
        raise RuntimeError('block is not chained')
    # add a new item to the get_data_message
    # should be FILTERED_BLOCK_DATA_TYPE and block hash
    getdata.add_data(FILTERED_BLOCK_DATA_TYPE, b.hash())
    # set the last block to the current hash
    last_block = b.hash()

# send the getdata message
node.send(getdata)
# initialize prev_tx, prev_index and  to None
prev_tx, prev_index, prev_amount = None, None, None
# loop while prev_tx is None
while prev_tx is None:
    # wait for the merkleblock or tx commands
    message = node.wait_for(MerkleBlock, Tx)
    # if we have the merkleblock command
    if message.command == b'merkleblock':
        # check that the MerkleBlock is valid
        if not message.is_valid():
            raise RuntimeError('invalid merkle proof')
    # else we have the tx command
    elif message.command == b'tx':
        # set the tx's testnet to be True
        message.testnet = True
        # loop through the tx outs
        for i, tx_out in enumerate(message.tx_outs):
            # if our output has the same address as our address we found it
            if tx_out.script_pubkey.address(testnet=True) == addr:
                # we found our utxo. set prev_tx, prev_index, and tx
                prev_tx = message.hash()
                prev_index = i
                prev_amount = tx_out.amount
                print('found: {}:{}'.format(prev_tx.hex(), prev_index))
                # create the TxIn
                tx_in = TxIn(prev_tx, prev_index)
                # calculate the output amount (previous amount minus the fee)
                output_amount = prev_amount - fee
                # create a new TxOut to the target script with the output amount
                tx_out = TxOut(output_amount, target_script)
                # create a new transaction with the one input and one output
                tx_obj = Tx(1, [tx_in], [tx_out], 0, testnet=True)
                # sign the only input of the transaction
                print(tx_obj.sign_input(0, private_key))
                # serialize and hex to see what it looks like
                print(tx_obj.serialize().hex())
                # send this signed transaction on the network
                node.send(tx_obj)
                # wait a sec so this message goes through with time.sleep(1)
                time.sleep(1)
                # now ask for this transaction from the other node
                # create a GetDataMessage
                getdata = GetDataMessage()
                # ask for our transaction by adding it to the message
                getdata.add_data(TX_DATA_TYPE, tx_obj.hash())
                # send the message
                node.send(getdata)
                # now wait for a Tx response
                received_tx = node.wait_for(Tx)
                # if the received tx has the same id as our tx, we are done!
                if received_tx.id() == tx_obj.id():
                    print('success!')
