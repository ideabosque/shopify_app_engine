# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import logging
from typing import Any, Dict, List


def _initialize_tables(logger: logging.Logger) -> None:
    from .app_subscription import create_app_subscription_table
    from .webhook_event import create_webhook_event_table
    from .webhook_subscription import create_webhook_subscription_table

    create_app_subscription_table(logger)
    create_webhook_event_table(logger)
    create_webhook_subscription_table(logger)