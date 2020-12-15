# import everything and define a test runner function
from importlib import reload
from helper import run
import ecc
import helper
import op
import script
import tx

reload(op)
run(op.OpTest("test_op_checkmultisig"))
