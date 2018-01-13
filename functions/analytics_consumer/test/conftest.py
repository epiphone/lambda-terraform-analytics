import os
import sys

here = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(here, '..', '..', '..', 'test_utils'))

from fixtures import event, lambda_context
