"""Shared pytest setup.

Layer 1 (unit) tests must not touch the network. Importing api.db normally
starts a background thread that lists/downloads from R2, so we set
FOOTY_SKIP_INIT=1 before anything imports it.
"""
import os

os.environ["FOOTY_SKIP_INIT"] = "1"
