"""
API Routes Module
"""

from flask import Blueprint, request
from ..auth import verify_auth

graph_bp = Blueprint('graph', __name__)
simulation_bp = Blueprint('simulation', __name__)
report_bp = Blueprint('report', __name__)
tribev2_bp = Blueprint('tribev2', __name__)

# Protect all graph blueprint routes
@graph_bp.before_request
def protect_graph():
    return verify_auth()

# Protect all simulation blueprint routes
@simulation_bp.before_request
def protect_simulation():
    return verify_auth()

# Protect all report blueprint routes
@report_bp.before_request
def protect_report():
    return verify_auth()

# Protect all tribev2 blueprint routes
@tribev2_bp.before_request
def protect_tribev2():
    return verify_auth()

from . import graph  # noqa: E402, F401
from . import simulation  # noqa: E402, F401
from . import report  # noqa: E402, F401
from . import neurosim_adapter  # noqa: E402, F401 - NeuroSim compatibility endpoint
from . import tribev2  # noqa: E402, F401 - TRIBE v2 brain response prediction

