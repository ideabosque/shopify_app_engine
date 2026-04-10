#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "jeffreyw"

import functools
import logging
import traceback
import secrets

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

class AppSubscriptionStatusIndex(LocalSecondaryIndex):
 
    class Meta:
        billing_mode = "PAY_PER_REQUEST"
        # All attributes are projected
        projection = AllProjection()
        index_name = "app_subscription_status-index"

    shop = UnicodeAttribute(hash_key=True)
    status = UnicodeAttribute(range_key=True)

class AppSubscriptionModel(BaseModel):
    class Meta(BaseModel.Meta):
        table_name = "sae-app_subscriptions"

    shop = UnicodeAttribute(hash_key=True)
    app_subscription_id = UnicodeAttribute(range_key=True)
    
    plan_name = UnicodeAttribute()
    plan_code = UnicodeAttribute()
    status = UnicodeAttribute()

    interval = UnicodeAttribute(null=True)
    subscription_created_at = UTCDateTimeAttribute()
    current_period_start = UTCDateTimeAttribute()
    current_period_end = UTCDateTimeAttribute(null=True)
    trial_days = NumberAttribute()
    line_items = ListAttribute(of=MapAttribute)

    quotas = MapAttribute()

    created_at = UTCDateTimeAttribute()
    updated_at = UTCDateTimeAttribute()

    app_subscription_status_index = AppSubscriptionStatusIndex()

def create_app_subscription_table(logger: logging.Logger) -> bool:
    """Create the Subscription table if it doesn't exist."""
    if not AppSubscriptionModel.exists():
        # Create with on-demand billing (PAY_PER_REQUEST)
        AppSubscriptionModel.create_table(billing_mode="PAY_PER_REQUEST", wait=True)
        logger.info("The App Subscription table has been created.")
    return True


@retry(
    reraise=True,
    wait=wait_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
)
def get_app_subscription(shop: str, app_subscription_id: str) -> AppSubscriptionModel:
    try:
        return AppSubscriptionModel.get(shop, app_subscription_id)
    except Exception as e:
        return None

@retry(
    reraise=True,
    wait=wait_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
)
def get_active_app_subscription(shop: str) -> AppSubscriptionModel:
    try:
        results = AppSubscriptionModel.app_subscription_status_index.query(
            shop,
            AppSubscriptionModel.status == "ACTIVE",
            scan_index_forward=False,
            limit=1,
        )
        app_subscription = results.next()

        return app_subscription
    except StopIteration:
        return None

def get_app_subscription_count(shop: str, app_subscription_id: str) -> int:
    return AppSubscriptionModel.count(shop, AppSubscriptionModel.app_subscription_id == app_subscription_id)

def insert_update_app_subscription(**kwargs: Dict[str, Any]) -> None:

    shop = kwargs.get("shop")
    app_subscription_id = kwargs.get("app_subscription_id")
    entity = get_app_subscription(shop, app_subscription_id)
    if entity is None:
        cols = {
            "plan_name": kwargs.get("plan_name"),
            "plan_code": kwargs.get("plan_code"),
            "status": kwargs.get("status"),
            "interval": kwargs.get("interval"),
            "subscription_created_at": kwargs.get("subscription_created_at"),
            "current_period_start": kwargs.get("current_period_start"),
            "current_period_end": kwargs.get("current_period_end"),
            "trial_days": int(kwargs.get("trial_days", 0)),
            "quotas": kwargs.get("quotas", {}),
            "line_items": kwargs.get("line_items", []),
            "created_at": pendulum.now("UTC"),
            "updated_at": pendulum.now("UTC"),
        }

        AppSubscriptionModel(
            shop,
            app_subscription_id,
            **cols,
        ).save()
        return

    actions = [
        AppSubscriptionModel.updated_at.set(pendulum.now("UTC")),
    ]

    field_map = {
        "status": AppSubscriptionModel.status,
    }

    for key, field in field_map.items():
        if key in kwargs:
            actions.append(field.set(kwargs[key]))

    entity.update(actions=actions)
    return

