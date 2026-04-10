#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "jeffreyw"

import json
import urllib.parse
from typing import Any, Dict, List
from graphene import Schema
from silvaengine_utility import Graphql, Serializer, HttpResponse
from silvaengine_constants import HttpStatus
from silvaengine_dynamodb_base import BaseModel

from .handlers.config import Config
from .handlers.app import App
from .handlers.shopify import request_token, get_active_subscriptions
from .handlers.app_subscription import get_active_subscription
from .handlers.webhook import register_webhook, handle_webhook
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
                "shopify_webhook": {
                    "is_static": False,
                    "label": "Shopify Webhook",
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

        if (
            setting.get("region_name")
            and setting.get("aws_access_key_id")
            and setting.get("aws_secret_access_key")
        ):
            BaseModel.Meta.region = setting.get("region_name")
            BaseModel.Meta.aws_access_key_id = setting.get("aws_access_key_id")
            BaseModel.Meta.aws_secret_access_key = setting.get("aws_secret_access_key")

        Config.initialize(logger, **setting)

        self.logger = logger
        self.setting = setting
    
    def _apply_partition_defaults(self, params: Dict[str, Any]) -> None:
        """
        Apply default partition values if not provided in params.

        Args:
            params (Dict[str, Any]): A dictionary of parameters required to build the GraphQL query.
        """
        endpoint_id = params.get("endpoint_id", self.setting.get("endpoint_id"))
        part_id = params.get("metadata", {}).get(
            "part_id",
            params.get("part_id", self.setting.get("part_id")),
        )

        if params.get("context") is None:
            params["context"] = {}

        if "endpoint_id" not in params["context"]:
            params["context"]["endpoint_id"] = endpoint_id
        if "part_id" not in params["context"]:
            params["context"]["part_id"] = part_id
        if "connection_id" not in params:
            params["connection_id"] = self.setting.get("connection_id")

        if "partition_key" not in params["context"]:
            # Validate endpoint_id and part_id before creating partition_key
            if not endpoint_id or not part_id:
                self.logger.error(
                    f"Missing endpoint_id or part_id: endpoint_id={endpoint_id}, part_id={part_id}"
                )
                raise ValueError(
                    "Both 'endpoint_id' and 'part_id' are required to generate 'partition_key'."
                )
            else:
                params["context"]["partition_key"] = f"{endpoint_id}#{part_id}"
                
    def shopify_app_engine_graphql(self, **params: Dict[str, Any]) -> Any:
        self._apply_partition_defaults(params)
        return self.execute(self.__class__.build_graphql_schema(), **params)


    @staticmethod
    def build_graphql_schema() -> Schema:
        return Schema(
            query=Query,
            mutation=Mutations,
            types=type_class()
        )

    def app_check(self, **params):
        try:
            shopify_params = {
                key: value
                for key, value in params.items()
                if key not in ["endpoint_id", "area", "context", "api_key", "metadata"]
            }
            # self.logger.info(shopify_params)
            shop = shopify_params.get("shop")
            app_id = shopify_params.get("app_id")
            if app_id is None:
                app_id = shopify_params.get("appId")
            config = self.setting.get("app_settings", {}).get(app_id)
            if not shop or not config:
                raise Exception("Missing shop or invalid app_id")
            context = {
                "logger": self.logger,
                "setting": self.setting,
                "endpoint_id": params.get("endpoint_id"),
                "part_id": App.get_target_id(shop),
                "partition_key": f"{params.get('endpoint_id')}#{App.get_target_id(shop)}"
            }
            app_handler = App(context=context, logger=self.logger, **self.setting)
            app = app_handler.get_app(app_id, shop)
            if app is None:
                return Serializer.json_dumps(
                    {
                        "authed": False
                    }
                )
            else:
                
                result = {
                    "authed": True,
                    "subscription_required": config.get("subscription_required", True),
                    "app_subscription": {},
                    "quotas": {},
                }
                if config.get("subscription_required", True):
                    active_subscription = get_active_subscription(context, shop, app)
                    if active_subscription is None:
                        result["app_subscription"]["active"] = False
                    else:
                        # plan_code = self.setting.get("shopify_plan_mapping", {}).get(active_subscription.get("name"))
                        result["app_subscription"] = {
                            "active": True if active_subscription.get("status") == "ACTIVE" else False,
                            "plan_name": active_subscription.get("plan_name"),
                            "plan_code": active_subscription.get("plan_code"),
                            "status": active_subscription.get("status"),
                            "current_period_end": active_subscription.get("current_period_end"),
                            # "quotas": active_subscription.get("quotas"),
                        }
                        result["quotas"] = active_subscription.get("quotas")

                return Serializer.json_dumps(result)
        except Exception as e:
            self.logger.error(str(e))
            return Serializer.json_dumps(
                {
                    "errors": str(e)
                }
            )
        
    def app_callback(self, **params):
        try:
            shopify_params = {
                key: value
                for key, value in params.items()
                if key not in ["endpoint_id", "area", "context", "api_key", "metadata"]
            }
            # self.logger.info(shopify_params)
            shop = shopify_params.get("shop")
            app_id = shopify_params.get("app_id")
            if app_id is None:
                app_id = shopify_params.get("appId")
            config = self.setting.get("app_settings", {}).get(app_id)
            if not shop or not config:
                raise Exception("Missing shop or invalid app_id")
            
            context = {
                "logger": self.logger,
                "setting": self.setting,
                "endpoint_id": params.get("endpoint_id"),
                "part_id": App.get_target_id(shop),
                "partition_key": f"{params.get('endpoint_id')}#{App.get_target_id(shop)}"
            }
            app_handler = App(context=context, logger=self.logger, **self.setting)
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
                query = urllib.parse.urlencode({"shop": shop})
                redirect_url = f"{app_base_url}?{query}"
            return HttpResponse.format_response(
                data={},
                status_code=HttpStatus.FOUND.value,
                headers={
                    "Location": redirect_url
                }
            )
        except Exception as e:
            self.logger.error(str(e))
            return Serializer.json_dumps(
                {
                    "errors": str(e)
                }
            )

    def oauth_callback(self, **params):
        try:
            shopify_params = {
                key: value
                for key, value in params.items()
                if key not in ["endpoint_id", "area", "context", "api_key", "metadata"]
            }
            # self.logger.info(shopify_params)
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
            # self.logger.info(query_params)
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
            
            context = {
                "logger": self.logger,
                "setting": self.setting,
                "endpoint_id": params.get("endpoint_id"),
                "part_id": App.get_target_id(shop),
                "partition_key": f"{params.get('endpoint_id')}#{App.get_target_id(shop)}"
            }
            app_handler = App(context=context, logger=self.logger, **self.setting)
            app_handler.install_app(**query_params)
            try:
                register_webhook(self.logger, self.setting, app_id, shop, access_token)
            except Exception as e:
                self.logger.error(e)
                pass
            config = self.setting.get("app_settings", {}).get(app_id, {})
            app_base_url = self.setting.get("app_base_url")
            redirect_params = {
                "shop": shop,
                "app_id": app_id,
                "embedded": config.get("embedded", 1)
            }
            query = urllib.parse.urlencode(redirect_params)
            redirect_url = f"{app_base_url}?{query}"
            return HttpResponse.format_response(
                data={},
                status_code=HttpStatus.FOUND.value,
                headers={
                    "Location": redirect_url
                }
            )
        except Exception as e:
            self.logger.error(str(e))
            return Serializer.json_dumps(
                {
                    "errors": str(e)
                }
            )
        
    def shopify_webhook(self, **params):
        from .handlers.webhook import ValueExistException, RetryException

        self.logger.info(params)

        if params.get("event") is None:
            self.logger.error("Missing event")
            return HttpResponse.format_response(
                data={},
                status_code=HttpStatus.BAD_REQUEST.value
            )
        self.logger.info("start processing handle_webhook")
        context = {
            "logger": self.logger,
            "setting": self.setting,
            "endpoint_id": params.get("endpoint_id"),
            # "part_id": App.get_target_id(shop),
            # "partition_key": f"{params.get('endpoint_id')}#{App.get_target_id(shop)}"
        }
        
        try:
            handle_webhook(context, params)
        except ValueExistException as e:
            return HttpResponse.format_response(
                data={},
                status_code=HttpStatus.OK.value
            )
        except RetryException as e:
            self.logger.error(str(e))
            return HttpResponse.format_response(
                data={"error": str(e)},
                status_code=HttpStatus.INTERNAL_SERVER_ERROR.value
            )
        except Exception as e:
            self.logger.error(str(e))
            return HttpResponse.format_response(
                data={"error": str(e)},
                status_code=HttpStatus.BAD_REQUEST.value
            )

        return HttpResponse.format_response(
            data={},
            status_code=HttpStatus.OK.value
        )
    


    

        


