#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import logging
import time
import traceback
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Attr, Key
from graphene import ResolveInfo

from .utils import GraphqlSchemaUtility
from .config import Config

class App(object):
    platform = "shopify"
    schemas = {}
    logger = None
    setting = {}
    context = None

    app_id = None
    graphql_schema_utility = None

    def __init__(self, context: Dict[str, Any], logger: logging.Logger, **setting: Dict[str, Any]):
        try:
            self._initialize_config(setting)
            self._initialize_aws_services(setting)
            self._initialize_graphql_schema_utility(logger, setting)
            self.logger = logger
            self.setting = setting
            self.context = context
        except Exception as e:
            log = traceback.format_exc()
            logger.error(log)
            raise e
    def _initialize_config(self, setting: Dict[str, Any]) -> None:
        pass

    def _initialize_aws_services(self, setting: Dict[str, Any]) -> None:
        pass

    def _initialize_graphql_schema_utility(self, logger: logging.Logger, setting: Dict[str, Any]) -> None:
        self.graphql_schema_utility = GraphqlSchemaUtility(logger, **setting)
        self.app_id = None

    def install_app_config(self, app_id):
        config = self.setting.get("app_settings",{}).get(app_id)
        variables = {
            "appId": app_id,
            "platform": self.platform,
            "configuration": config
        }
        response = self.graphql_schema_utility.request_graphql(
            context=self.context,
            module_name="app_core_engine",
            function_name="app_core_engine_graphql",
            graphql_operation_name="insertUpdateAppConfig",
            graphql_operation_type="Mutation",
            class_name="AppCoreEngine",
            variables=variables
        )

    def install_app(self, **params):
        app_id = params.get("app_id")
        self.install_app_config(app_id)
        config = self.setting.get("app_settings",{}).get(app_id)
        target_id = self.get_target_id(params.get("shop"))
        variables = {
            "appId": params.get("app_id"),
            "targetId": target_id,
            "platform": self.platform,
            "accessToken": params.get("access_token", ""),
            "userId": params.get("user_id", "####"),
            "scope": config.get("scopes", ""),
            "data": dict(params, **config),
            "status": "installed",
        }
        response = self.graphql_schema_utility.request_graphql(
            context=self.context,
            module_name="app_core_engine",
            function_name="app_core_engine_graphql",
            graphql_operation_name="insertUpdateApp",
            graphql_operation_type="Mutation",
            class_name="AppCoreEngine",
            variables=variables
        )

    def get_app(self, app_id, shop):
        target_id = self.get_target_id(shop)
        variables = {
            "appId": app_id,
            "targetId": target_id,
        }

        response = self.graphql_schema_utility.request_graphql(
            context=self.context,
            module_name="app_core_engine",
            function_name="app_core_engine_graphql",
            graphql_operation_name="app",
            graphql_operation_type="Query",
            class_name="AppCoreEngine",
            variables=variables
        )
        
        app = None
        if response is not None:
            app = response
        return app
    
    def get_shop_apps(self, shop):
        target_id = self.get_target_id(shop)
        variables = {
            "targetId": target_id,
            "platform": self.platform
        }

        response = self.graphql_schema_utility.request_graphql(
            context=self.context,
            module_name="app_core_engine",
            function_name="app_core_engine_graphql",
            graphql_operation_name="appList",
            graphql_operation_type="Query",
            class_name="AppCoreEngine",
            variables=variables
        )

        app_list = None
        if response is not None and response["appList"] is not None:
            app_list = response["appList"]
        return app_list
    def get_access_token(self, **params):
        pass

    def get_target_id(self, shop):
        return shop.replace(".myshopify.com", "")


    def get_app_by_shop(self, shop, app_id=None):
        target_id = self.get_target_id(shop)
        app = Config.get_app(target_id, app_id)
        if app is not None:
            return app
        shop_apps = self.get_shop_apps(shop)
        for shop_app in shop_apps:
            Config.save_app(target_id, shop_app["appId"],shop_app)

        return Config.get_app(target_id, app_id)