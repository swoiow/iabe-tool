import sys

if sys.version_info > (3, 0):
    PY_VERSION = 3
else:
    PY_VERSION = 2

from utils.basic import *
from utils.common import *
from utils.dbModel import *
from utils.dbUnit import *

