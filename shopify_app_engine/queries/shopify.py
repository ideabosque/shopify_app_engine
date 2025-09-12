#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

from typing import Any, Dict

from graphene import ResolveInfo

from silvaengine_utility import Utility

from ..handlers.app import App
from ..types.shopify import ProductType, VariantProductType, ProductListType
from shopify_connector import ShopifyConnector

def resolve_product_list(info: ResolveInfo, **kwargs: Dict[str, Any]) -> ProductListType:
    shop = kwargs.get("shop")
    app_id = kwargs.get("app_id")
    attributes = kwargs.get("attributes")
    app = App(info.context.get("logger"), **info.context.get("setting"))
    app_data = app.get_app_by_shop(shop, app_id)
    if app_data is None:
        raise Exception("App not found")
    if not app_data.get("accessToken"):
        raise Exception("You didn't authorize this app")
    app_setting = {
        "shop_url": shop,
        "api_version": app_data.get("appConfig",{}).get("configruation",{}).get("version", "2025-01"),
        "private_app_password": app_data.get("accessToken")
    }
    shopify_connector = ShopifyConnector(info.context.get("logger"), **app_setting)
    products = shopify_connector.find_products_by_attributes(attributes)
    formated_products = []
    if products is not None:
        formated_products = [product.to_dict() for product in products]
    return ProductListType(**Utility.json_loads(Utility.json_dumps({"product_list": formated_products})))


