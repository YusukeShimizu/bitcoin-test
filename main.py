############## PLEASE RUN THIS CELL FIRST! ###################

# import everything and define a test runner function
from importlib import reload
from helper import run
import block
import ecc
import helper
import network
import script
import tx
import merkleblock
from helper import merkle_parent

reload(merkleblock)
run(merkleblock.MerkleBlockTest("test_is_valid"))
