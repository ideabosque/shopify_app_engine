# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import traceback
from typing import Any, Dict

from graphene import Boolean, Field, Int, Mutation, String

from silvaengine_utility import JSONCamelCasefrom ..types.shopify import DraftOrderType
from ..handlers.app import App
from ..handlers.config import Config
from shopify_connector import ShopifyConnector

class CreateDraftOrder(Mutation):
    draft_order = Field(DraftOrderType)

    class Arguments:
        shop = String(required=True)
        app_id = String(required=False)
        email = String(required=True)
        line_items = JSONCamelCase(required=True)
        shipping_address = JSONCamelCase(required=True)
        billing_address = JSONCamelCase(required=False)
        # settings = JSONCamelCase(required=True)

    @staticmethod
    def mutate(root: Any, info: Any, **kwargs: Dict[str, Any]) -> "CreateDraftOrder":
        try:
            shop = kwargs.get("shop")
            app_id = kwargs.get("app_id")
            app = App(info.context, info.context.get("logger"), **info.context.get("setting"))
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
            email = kwargs.get("email")
            line_items = kwargs.get("line_items")
            shipping_address = kwargs.get("shipping_address")
            billing_address = kwargs.get("billing_address")
            if billing_address is None:
                billing_address = dict({}, **shipping_address)
            
            draft_order = shopify_connector.create_draft_order(email, line_items, shipping_address, billing_address)
            draft_order_data = draft_order.to_dict()
            return CreateDraftOrder(draft_order=draft_order_data)
        except Exception as e:
            log = traceback.format_exc()
            info.context.get("logger").error(log)
            raise e

