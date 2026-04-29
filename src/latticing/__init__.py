"""
lattice: Code implementation for Behavior Latticing.
"""

import sys
import os

# Source files use bare imports; ensure this directory is on the path.
_here = os.path.dirname(__file__)
if _here not in sys.path:
    sys.path.insert(0, _here)

from Observer import Observer  # noqa: E402
from AsyncLLM import AsyncLLM  # noqa: E402
from SyncLLM import SyncLLM  # noqa: E402
from Lattice import Lattice  # noqa: E402
from models import Separator  # noqa: E402
from Visualize import Visualizer  # noqa: E402
from Layers import LatticeLayer, Sequential, SessionLayer, AllLayer, TimeLayer, NumberLayer  # noqa: E402

__version__ = "0.1.3.2"

# Per Python logging best practices for libraries: attach a NullHandler so
# that log records are silently discarded unless the application configures
# a handler.  Never call basicConfig or setLevel in library code.
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
