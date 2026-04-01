#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "jeffreyw"

import functools
import logging
import traceback
import secrets

from typing import Any, Dict, List

import pendulum
from graphene import ResolveInfo
from pynamodb.attributes import (
    MapAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
    ListAttribute
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

class WebhookSubscriptionTopicIndex(LocalSecondaryIndex):
 
    class Meta:
        billing_mode = "PAY_PER_REQUEST"
        # All attributes are projected
        projection = AllProjection()
        index_name = "webhook_subscription_topic-index"

    shop = UnicodeAttribute(hash_key=True)
    topic = UnicodeAttribute(range_key=True)

class WebhookSubscriptionModel(BaseModel):
    class Meta(BaseModel.Meta):
        table_name = "sae-webhook_subscriptions"

    shop = UnicodeAttribute(hash_key=True)
    webhook_subscription_id = UnicodeAttribute(range_key=True)
    
    topic = UnicodeAttribute()

    webhook_subscription = MapAttribute()

    created_at = UTCDateTimeAttribute()
    updated_at = UTCDateTimeAttribute()

    webhook_scription_topic_index = WebhookSubscriptionTopicIndex()

def create_webhook_subscription_table(logger: logging.Logger) -> bool:
    """Create the WebhookSubscription table if it doesn't exist."""
    if not WebhookSubscriptionModel.exists():
        # Create with on-demand billing (PAY_PER_REQUEST)
        WebhookSubscriptionModel.create_table(billing_mode="PAY_PER_REQUEST", wait=True)
        logger.info("The WebhookSubscription table has been created.")
    return True


@retry(
    reraise=True,
    wait=wait_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
)
def get_webhook_subscription(shop: str, webhook_subscription_id: str) -> WebhookSubscriptionModel:
    try:
        return WebhookSubscriptionModel.get(shop, webhook_subscription_id)
    except Exception as e:
        return None


def get_webhook_subscription_count(partition_key: str, webhook_subscription_id: str) -> int:
    return WebhookSubscriptionModel.count(partition_key, WebhookSubscriptionModel.webhook_subscription_id == webhook_subscription_id)

@retry(
    reraise=True,
    wait=wait_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
)
def get_webhook_subscription_by_topic(shop: str, topic: str) -> WebhookSubscriptionModel:
    try:
        results = WebhookSubscriptionModel.webhook_scription_topic_index.query(
            shop,
            WebhookSubscriptionModel.topic == topic,
            scan_index_forward=False,
            limit=1,
        )
        webhook_subscription = results.next()

        return webhook_subscription
    except StopIteration:
        return None

def get_webhook_subscriptions_by_shop(shop: str) -> list[WebhookSubscriptionModel]:
    items = []
    results = WebhookSubscriptionModel.query(shop)
    for item in results:
        items.append(item)
    return items
    

def insert_update_webhook_subscription(**kwargs: Dict[str, Any]):

    shop = kwargs.get("shop")
    webhook_subscription_id = kwargs.get("webhook_subscription_id")
    required_fields = ["shop", "webhook_subscription_id", "topic", "webhook_subscription"]
    for required_field in required_fields:
        if required_field not in kwargs or kwargs.get(required_field) is None:
            raise Exception("Missing required field: {}".format(required_field))

    entity = get_webhook_subscription(shop, webhook_subscription_id)
    if entity is None:
        cols = {
            "topic": kwargs["topic"],
            "webhook_subscription": kwargs.get("webhook_subscription", {}),
            "created_at": pendulum.now("UTC"),
            "updated_at": pendulum.now("UTC"),
        }

        WebhookSubscriptionModel(
            shop,
            webhook_subscription_id,
            **cols,
        ).save()
        return

    webhook_subscription = entity
    actions = [
        WebhookSubscriptionModel.updated_at.set(pendulum.now("UTC")),
    ]

    field_map = {
        "webhook_subscription": WebhookSubscriptionModel.webhook_subscription
    }

    for key, field in field_map.items():
        if key in kwargs:
            actions.append(field.set(kwargs[key]))

    webhook_subscription.update(actions=actions)
    return webhook_subscription



def delete_webhook_subscription(shop: str, webhook_subscription_id) -> bool:
    entity = get_webhook_subscription(shop, webhook_subscription_id)
    if entity is not None:
        entity.delete()
    return True
