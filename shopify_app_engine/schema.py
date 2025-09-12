#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "jeffreyw"

import time
from typing import Any, Dict

from graphene import (
    Boolean,
    DateTime,
    Field,
    Int,
    List,
    ObjectType,
    ResolveInfo,
    String,
)

from .mutations.config_setting import InsertUpdateConfigSetting
from .queries.config_setting import resolve_config_setting_list
from .queries.shopify import resolve_product_list
from .mutations.shopify import CreateDraftOrder
# from .mutations.app import DeleteApp, InsertUpdateApp
# from .mutations.thread import DeleteThread, InsertThread
# from .queries.app import resolve_app, resolve_app_list
# from .queries.app_config import resolve_app_config, resolve_app_config_list
# from .queries.thread import resolve_thread, resolve_thread_list
from .types.config_setting import ConfigSettingType, ConfigSettingListType, VariableType
from .types.shopify import DraftOrderType, ProductListType, ProductType, VariantProductType, LineItemType, AddressType
from silvaengine_utility import JSON, Utility

def type_class():
    return [
        ConfigSettingType,
        ConfigSettingListType,
        VariableType,
        DraftOrderType,
        ProductListType,
        ProductType,
        VariantProductType,
        LineItemType,
        AddressType
    ]


class Query(ObjectType):
    ping = String()
    config_setting_list = Field(
        ConfigSettingListType,
        shop=String(required=True),
        setting_id=String()
    )
    product_list = Field(
        ProductListType,
        shop=String(required=True),
        app_id=String(required=False),
        attributes=JSON(required=True)
    )
    def resolve_ping(self, info: ResolveInfo) -> str:
        return f"Hello at {time.strftime('%X')}!!"

    def resolve_config_setting_list(self, info: ResolveInfo, **kwargs: Dict[str, Any]) -> ConfigSettingListType:
        return resolve_config_setting_list(info, **kwargs)

    def resolve_product_list(self, info: ResolveInfo, **kwargs: Dict[str, Any]) -> ProductListType:
        return resolve_product_list(info, **kwargs)
    
class Mutations(ObjectType):
    insert_update_config_setting = InsertUpdateConfigSetting.Field()
    create_draft_order = CreateDraftOrder.Field()
