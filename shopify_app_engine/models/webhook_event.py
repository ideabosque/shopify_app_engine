#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "jeffreyw"

import functools
import logging
import traceback
import secrets
import time
from typing import Any, Dict

import pendulum
from graphene import ResolveInfo
from pynamodb.attributes import (
    MapAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
    ListAttribute,
    NumberAttribute
)
from pynamodb.indexes import AllProjection, LocalSecondaryIndex
from tenacity import retry, stop_after_attempt, wait_exponential

from silvaengine_dynamodb_base import (
    BaseModel,
    delete_decorator,
    insert_update_decorator,
    monitor_decorator,
    resolve_list_decorator,
)
from silvaengine_utility import method_cache
from silvaengine_utility.serializer import Serializer

from ..handlers.config import Config


class WebhookEventModel(BaseModel):
    class Meta(BaseModel.Meta):
        table_name = "sae-webhook_events"

    shop = UnicodeAttribute(hash_key=True)
    event_id = UnicodeAttribute(range_key=True)
    
    webhook_data = MapAttribute()
    ttl = NumberAttribute()

    created_at = UTCDateTimeAttribute()
    updated_at = UTCDateTimeAttribute()

def create_webhook_event_table(logger: logging.Logger) -> bool:
    """Create the Webhook table if it doesn't exist."""
    if not WebhookEventModel.exists():
        # Create with on-demand billing (PAY_PER_REQUEST)
        WebhookEventModel.create_table(billing_mode="PAY_PER_REQUEST", wait=True)
        logger.info("The Webhook table has been created.")
    return True


@retry(
    reraise=True,
    wait=wait_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
)
def get_webhook_event(shop: str, event_id: str) -> WebhookEventModel:
    try:
        return WebhookEventModel.get(shop, event_id)
    except Exception as e:
        return None


def get_webhook_event_count(shop: str, event_id: str) -> int:
    return WebhookEventModel.count(shop, WebhookEventModel.event_id == event_id)


def insert_webhook_event(**kwargs: Dict[str, Any]) -> None:

    shop = kwargs.get("shop")
    event_id = kwargs.get("event_id")
    cols = {
        "webhook_data": kwargs.get("webhook_data"),
        "ttl": int(time.time()) + 48 * 3600,
        "created_at": pendulum.now("UTC"),
        "updated_at": pendulum.now("UTC"),
    }

    WebhookEventModel(
        shop,
        event_id,
        **cols,
    ).save()
    return