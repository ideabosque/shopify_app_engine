#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

from typing import Any, Dict

from graphene import ResolveInfo

from silvaengine_utility import Utility

from ..handlers.app import App
from ..types.shopify import ProductType, VariantProductType, ProductListType, CustomerType
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
    return ProductListType(**Utility.json_normalize({"product_list": formated_products}))


def resolve_customer(info: ResolveInfo, **kwargs: Dict[str, Any]) -> CustomerType:
    shop = kwargs.get("shop")
    app_id = kwargs.get("app_id")
    email = kwargs.get("email")
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
    result = shopify_connector.find_customer_by_email(email)
    if result is not None:
        customer = result[0].to_dict()
        return CustomerType(**Utility.json_normalize(format_customer_data(customer)))
    
    customer_data = {
        "email": email,
        "first_name": kwargs.get("first_name"),
        "last_name": kwargs.get("last_name"),
        "phone": kwargs.get("phone"),
        "address": kwargs.get("address")
    }

    customer = shopify_connector.create_customer(**customer_data)
    return CustomerType(**Utility.json_normalize(format_customer_data(customer.to_dict())))


def format_customer_data(customer_data):
    valid_fields = {f for f in CustomerType._meta.fields.keys()}
    clean_data = {k: v for k, v in customer_data.items() if k in valid_fields}
    return clean_data