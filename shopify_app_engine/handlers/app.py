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

from silvaengine_utility import Utility
from .utils import GraphqlSchemaUtility
from .config import Config

class App(object):
    platform = "shopify"
    functs_on_local = None
    funct_on_local_config = None
    aws_ddb = None
    schemas = {}
    logger = None
    setting = {}
    endpoint_id = None

    ##<--Testing Data-->##
    connection_id = None
    test_mode = None

    app_id = None
    app_endpoint_id = None
    graphql_schema_utility = None

    def __init__(self, logger: logging.Logger, **setting: Dict[str, Any]):
        try:
            self._initialize_config(setting)
            self._initialize_aws_services(setting)
            self._initialize_graphql_schema_utility(logger, setting)
            self.logger = logger
            self.setting = setting
        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise e
    def _initialize_config(self, setting: Dict[str, Any]) -> None:
        self.endpoint_id = setting.get("endpoint_id")
        self.app_endpoint_id = setting.get("app_endpoint_id")

    def _initialize_aws_services(self, setting: Dict[str, Any]) -> None:
        # if all(
        #     setting.get(k)
        #     for k in ["region_name", "aws_access_key_id", "aws_secret_access_key"]
        # ):
        #     aws_credentials = {
        #         "region_name": setting["region_name"],
        #         "aws_access_key_id": setting["aws_access_key_id"],
        #         "aws_secret_access_key": setting["aws_secret_access_key"],
        #     }
        # else:
        #     aws_credentials = {}

        # self.aws_ddb = boto3.resource("dynamodb", **aws_credentials)
        self.aws_ddb = Config.aws_ddb

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
        response = self.graphql_schema_utility.execute_graphql_query(
            logger=self.logger,
            endpoint_id=self.app_endpoint_id,
            function_name="app_core_engine_graphql",
            operation_name="insertUpdateAppConfig",
            operation_type="Mutation",
            variables=variables,
            setting=self.setting,
            connection_id=self.connection_id,
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
        response = self.graphql_schema_utility.execute_graphql_query(
            logger=self.logger,
            endpoint_id=self.app_endpoint_id,
            function_name="app_core_engine_graphql",
            operation_name="insertUpdateApp",
            operation_type="Mutation",
            variables=variables,
            setting=self.setting,
            connection_id=self.connection_id,
        )
        self.insert_connections(target_id)
        self.insert_endpoint(target_id)
        self.init_config_setting(target_id)

    def get_app(self, app_id, shop):
        target_id = self.get_target_id(shop)
        variables = {
            "appId": app_id,
            "targetId": target_id
        }
        response = self.graphql_schema_utility.execute_graphql_query(
            logger=self.logger,
            endpoint_id=self.app_endpoint_id,
            function_name="app_core_engine_graphql",
            operation_name="app",
            operation_type="Query",
            variables=variables,
            setting=self.setting,
            connection_id=self.connection_id,
        )
        app = None
        if response["app"] is not None:
            app = response["app"]["accessToken"]
        return app
    def get_access_token(self, **params):
        pass

    
    def insert_connections(self, shop):
        default_connections_settings = self.setting.get("default_connections_settings", [])
        if len(default_connections_settings) == 0:
            return

        connections_table = self.aws_ddb.Table("se-connections")
        response = connections_table.query(
            KeyConditionExpression=Key('endpoint_id').eq(shop),
            Select='COUNT'
        )
        if response["Count"] == len(default_connections_settings):
            return
        for connection_setting in default_connections_settings:
            item = {
                "endpoint_id": shop,
                "api_key": connection_setting.get("api_key"),
                "functions": self.process_setting_in_functions(shop, connection_setting.get("functions")),
                "whitelist": None
            }
            connections_table.put_item(Item=item)

    def process_setting_in_functions(self, shop, functions):
        new_functions = []
        replace_module_setting = self.setting.get("replace_function_setting", {"ai_marketing_graphql":"ai_marketing_engine"})
        for function in functions:
            if function.get("function") in replace_module_setting:
                new_functions.append(
                    dict(function, **{"setting": self.get_setting_id(shop, replace_module_setting[function.get("function")])})
                )
            else:
                new_functions.append(function)
        return new_functions

    def insert_endpoint(self, shop):
        endpoints_table = self.aws_ddb.Table("se-endpoints")
        response = endpoints_table.query(
            KeyConditionExpression=Key('endpoint_id').eq(shop),
            Select='COUNT'
        )
        if response["Count"] > 0:
            return
        item = {
            "endpoint_id": shop,
            "code": 0,
            "special_connection": True
        }
        endpoints_table.put_item(Item=item)

    def get_target_id(self, shop):
        return shop.replace(".myshopify.com", "")

    def get_setting_id(self, shop, default_setting_id):
        target_id = self.get_target_id(shop)
        return "{setting_id}_{target_id}".format(setting_id=default_setting_id, target_id=target_id)

    def vaildate_setting_id(self, shop, setting_id):
        replace_module_setting = self.setting.get("replace_function_setting", {"ai_marketing_graphql":"ai_marketing_engine"})
        shop_available_setting_ids = [
            self.get_setting_id(shop, default_setting_id)
            for function, default_setting_id in replace_module_setting.items()
        ]
        if setting_id not in shop_available_setting_ids:
            raise Exception(f"{shop} does not have setting_id {setting_id}")

    def get_config_settings(self, shop):
        replace_module_setting = self.setting.get("replace_function_setting", {"ai_marketing_graphql":"ai_marketing_engine"})
        all_items = []
        for function, default_setting_id in replace_module_setting.items():
            setting_id = self.get_setting_id(shop, default_setting_id)
            items = self.get_config_setting_by_setting_id(setting_id)
            all_items.extend(items)

        return all_items
    
    def get_config_setting_by_setting_id(self, setting_id):
        configdata_table = self.aws_ddb.Table("se-configdata")
        response = configdata_table.query(
            KeyConditionExpression=Key('setting_id').eq(setting_id)
        )
        items = response["Items"]
        while "LastEvaluatedKey" in response:
            response = configdata_table.query(
                KeyConditionExpression=Key('setting_id').eq(setting_id),
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response["Items"])
        return items
    
    def vaildate_config_settings(self, shop, setting_id, settings):
        replace_module_setting = self.setting.get("replace_function_setting", {"ai_marketing_graphql":"ai_marketing_engine"})
        matched_function = None
        for function, default_setting_id in replace_module_setting.items():
            if setting_id == self.get_setting_id(shop, default_setting_id):
                matched_function = function
        if matched_function is None:
            raise Exception("Invalid setting_id")
        
        allow_variables = self.setting.get("allow_edit_variables", {}).get(replace_module_setting.get(matched_function,""), [])
        if len(allow_variables) > 0:
            for setting in settings:
                if setting.get("variable") not in allow_variables:
                    raise Exception("variable:{variable} is not allowed to update.".format(variable=setting.get("variable")))

    
    def insert_update_config_settings(self, shop, setting_id, settings):
        self.vaildate_config_settings(shop, setting_id, settings)
        configdata_table = self.aws_ddb.Table("se-configdata")
        with configdata_table.batch_writer() as batch:
            for item in settings:
                new_item = dict(item, **{"setting_id": setting_id})
                batch.put_item(Item=new_item)

    def init_config_setting(self, shop):
        default_config_settings = self.get_default_config_settings()
        if len(default_config_settings) == 0 or len(self.get_config_settings(shop)) > 0:
            return
        
        configdata_table = self.aws_ddb.Table("se-configdata")
        with configdata_table.batch_writer() as batch:
            for item in default_config_settings:
                new_item = dict(item, **{"setting_id": self.get_setting_id(shop, item.get("setting_id"))})
                batch.put_item(Item=new_item)

    def get_default_config_settings(self):
        replace_module_setting = self.setting.get("replace_function_setting", {"ai_marketing_graphql":"ai_marketing_engine"})
        all_items = []
        for function, default_setting_id in replace_module_setting.items():
            items = self.get_config_setting_by_setting_id(default_setting_id)
            all_items.extend(items)

        return all_items
    
    def formated_config_setting_list(self, shop, config_settings):
        setting_dict = {}
        
        for item in config_settings:
            if item.get("setting_id") not in setting_dict:
                setting_dict[item.get("setting_id")] = {"setting_id": item.get("setting_id"), "settings": []}
            setting_dict[item.get("setting_id")]["settings"].append(
                {
                    "variable": item.get("variable"),
                    "value": item.get("value")
                }
            )
        show_variables = self.setting.get("show_variables", {})
        show_variables_mapping = {}
        if len(show_variables) > 0:
            for default_setting_id, variables in show_variables.items():
                if len(variables) == 0:
                    continue
                show_variables_mapping[self.get_setting_id(shop, default_setting_id)] = variables
        formated_config_settings = []
        for setting_id, config_setting in setting_dict.items():
            if len(show_variables_mapping) == 0:
                formated_config_settings.append(config_setting)
                continue
            if setting_id in show_variables_mapping:
                config_setting["settings"] = [
                    setting for setting in config_setting["settings"]
                    if setting.get("variable") in show_variables_mapping[setting_id]
                ]
                if len(config_setting["settings"]) > 0:
                    formated_config_settings.append(config_setting)
            else:
                formated_config_settings.append(config_setting)
            


        return [config_setting for setting_id, config_setting in setting_dict.items()]