#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "jeffreyw"

import json
import urllib.parse
from typing import Any, Dict, List
from graphene import Schema
from silvaengine_utility import Utility
from silvaengine_utility import Graphql

from .handlers.config import Config
from .handlers.app import App
from .handlers.shopify import request_token
from .schema import Mutations, Query, type_class
def deploy() -> list:
    return [
        {
            "service": "shopify_app_engine",
            "class": "ShopifyAppEngine",
            "functions": {
                "app_check": {
                    "is_static": False,
                    "label": "Check App",
                    "mutation": [],
                    "query": [],
                    "type": "RequestResponse",
                    "support_methods": ["POST", "GET"],
                    "is_auth_required": False,
                    "is_graphql": False,
                    "settings": "shopify_app_engine",
                },
                "app_callback": {
                    "is_static": False,
                    "label": "Check and Install App",
                    "mutation": [],
                    "query": [],
                    "type": "RequestResponse",
                    "support_methods": ["POST", "GET"],
                    "is_auth_required": False,
                    "is_graphql": False,
                    "settings": "shopify_app_engine",
                },
                "oauth_callback": {
                    "is_static": False,
                    "label": "Oauth Callback",
                    "mutation": [],
                    "query": [],
                    "type": "RequestResponse",
                    "support_methods": ["POST", "GET"],
                    "is_auth_required": False,
                    "is_graphql": False,
                    "settings": "shopify_app_engine",
                },
                "shopify_app_engine_graphql": {
                    "is_static": False,
                    "label": "Shopify App Engine GraphQL",
                    "query": [
                        {"action": "ping", "label": "Ping"},
                        {"action": "configSettingList", "label": "Config Setting List"},
                        {"action": "customer", "label": "Get Shopify Customer"}
                    ],
                    "mutation": [
                        {
                            "action": "insertUpdateConfigSetting",
                            "label": "Insert Update Config Setting",
                        },
                    ],
                    "type": "RequestResponse",
                    "support_methods": ["POST"],
                    "is_auth_required": False,
                    "is_graphql": True,
                    "settings": "shopify_app_engine",
                    "disabled_in_resources": True,  # Ignore adding to resource list.
                }
            }
        }
    ]

class ShopifyAppEngine(Graphql):
    def __init__(self, logger, **setting):
        Graphql.__init__(self, logger, **setting)

        Config.initialize(logger, **setting)

        self.logger = logger
        self.setting = setting
    
    def shopify_app_engine_graphql(self, **params: Dict[str, Any]) -> Any:
        schema = Schema(
            query=Query,
            mutation=Mutations,
            types=type_class(),
        )
        return self.execute(schema, **params)

    def app_check(self, **params):
        try:
            shopify_params = {
                key: value
                for key, value in params.items()
                if key not in ["endpoint_id", "area", "context"]
            }
            self.logger.info(shopify_params)
            shop = shopify_params.get("shop")
            app_id = shopify_params.get("app_id")
            if app_id is None:
                app_id = shopify_params.get("appId")
            config = self.setting.get("app_settings", {}).get(app_id)
            if not shop or not config:
                raise Exception("Missing shop or invalid app_id")
            
            app_handler = App(logger=self.logger, **self.setting)
            app = app_handler.get_app(app_id, shop)
            if app is None:
                return Utility.json_dumps(
                    {
                        "authed": False
                    }
                )
            else:
                return Utility.json_dumps(
                    {
                        "authed": True
                    }
                )
        except Exception as e:
            self.logger.error(str(e))
            return Utility.json_dumps(
                {
                    "errors": str(e)
                }
            )
        
    def app_callback(self, **params):
        try:
            shopify_params = {
                key: value
                for key, value in params.items()
                if key not in ["endpoint_id", "area", "context"]
            }
            self.logger.info(shopify_params)
            shop = shopify_params.get("shop")
            app_id = shopify_params.get("app_id")
            if app_id is None:
                app_id = shopify_params.get("appId")
            config = self.setting.get("app_settings", {}).get(app_id)
            if not shop or not config:
                raise Exception("Missing shop or invalid app_id")
            
            app_handler = App(logger=self.logger, **self.setting)
            app = app_handler.get_app(app_id, shop)
            if app is None:
                redirect_url = (
                    f"https://{shop}/admin/oauth/authorize?"
                    f"client_id={config['client_id']}&"
                    f"scope={config['scopes']}&"
                    f"redirect_uri={config['redirect_uri']}&"
                    f"state={app_id}"
                )
            else:
                app_base_url = self.setting.get("app_base_url")
                query = urllib.parse.urlencode(shopify_params)
                redirect_url = f"{app_base_url}?{query}"
            return Utility.json_dumps(
                {
                    "statusCode": 302,
                    "headers": {
                        "Location": redirect_url
                    }
                }
            )
        except Exception as e:
            self.logger.error(str(e))
            return Utility.json_dumps(
                {
                    "errors": str(e)
                }
            )

    def oauth_callback(self, **params):
        try:
            shopify_params = {
                key: value
                for key, value in params.items()
                if key not in ["endpoint_id", "area", "context"]
            }
            self.logger.info(shopify_params)
            query_params = {
                "code": shopify_params.get("code"),
                "hmac": shopify_params.get("hmac"),
                "shop": shopify_params.get("shop"),
                "timestamp": shopify_params.get("timestamp"),
                "host": shopify_params.get("host"),
                "state": shopify_params.get("state")
            }
            shop = shopify_params.get("shop")
            app_id = shopify_params.get("state")
            self.logger.info(query_params)
            access_token = None
            try:
                access_token = request_token(self.logger, self.setting, query_params)
            except Exception as e:
                self.logger.error(e)
            if access_token is None:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Failed to get access token."})
                }
            query_params["access_token"] = access_token
            query_params["app_id"] = params.get("state")
            app_handler = App(logger=self.logger, **self.setting)
            app_handler.install_app(**query_params)

            config = self.setting.get("app_settings", {}).get(app_id, {})
            app_base_url = self.setting.get("app_base_url")
            redirect_params = {
                "shop": shop,
                "app_id": app_id,
                "embedded": config.get("embedded", 1)
            }
            query = urllib.parse.urlencode(redirect_params)
            redirect_url = f"{app_base_url}?{query}"
            return Utility.json_dumps(
                {
                    "statusCode": 302,
                    "headers": {
                        "Location": redirect_url
                    }
                }
            )
        except Exception as e:
            self.logger.error(str(e))
            return Utility.json_dumps(
                {
                    "errors": str(e)
                }
            )
    

        


