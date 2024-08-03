"""Custom logger for Miraie."""

import logging

from .constants import PACKAGE_NAME

LOGGER: logging.Logger = logging.getLogger(PACKAGE_NAME)