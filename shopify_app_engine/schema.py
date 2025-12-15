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

from .queries.shopify import resolve_product_list, resolve_customer
from .mutations.shopify import CreateDraftOrder
from .types.shopify import DraftOrderType, ProductListType, ProductType, VariantProductType, LineItemType, AddressType, CustomerType
from silvaengine_utility import JSON

def type_class():
    return [
        DraftOrderType,
        ProductListType,
        ProductType,
        VariantProductType,
        LineItemType,
        AddressType,
        CustomerType
    ]


class Query(ObjectType):
    ping = String()
    product_list = Field(
        ProductListType,
        shop=String(required=True),
        app_id=String(required=False),
        attributes=JSON(required=True)
    )

    customer = Field(
        CustomerType,
        shop=String(required=True),
        app_id=String(required=False),
        email=String(required=True),
        first_name=String(required=False),
        last_name=String(required=False),
        phone=String(required=False),
        address=JSON(required=False)
    )

    def resolve_ping(self, info: ResolveInfo) -> str:
        return f"Hello at {time.strftime('%X')}!!"

    def resolve_product_list(self, info: ResolveInfo, **kwargs: Dict[str, Any]) -> ProductListType:
        return resolve_product_list(info, **kwargs)
    
    def resolve_customer(self, info: ResolveInfo, **kwargs: Dict[str, Any]) -> CustomerType:
        return resolve_customer(info, **kwargs)
    
class Mutations(ObjectType):
    create_draft_order = CreateDraftOrder.Field()
