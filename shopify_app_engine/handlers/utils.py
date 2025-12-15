#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import logging
import time
import traceback
import re
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Attr, Key
from graphene import ResolveInfo

from silvaengine_utility import Graphql
from .config import Config

class GraphqlSchemaUtility(object):
    functs_on_local = None
    funct_on_local_config = None
    aws_lambda = None
    schemas = {}
    logger = None
    setting = {}
    coordination_uuid = None
    agent_uuid = None
    retry_limit = 10

    ##<--Testing Data-->##
    connection_id = None

    def __init__(self, logger: logging.Logger, **setting: Dict[str, Any]):
        try:
            self._initialize_functs_on_local(setting)
            self._initialize_aws_clients(setting)
            self.logger = logger
            self.setting = setting
        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise e
    def _initialize_functs_on_local(self, setting: Dict[str, Any]) -> None:
        self.functs_on_local = setting.get("functs_on_local", {})

    def _initialize_aws_clients(self, setting: Dict[str, Any]) -> None:
        # if (
        #     setting.get("region_name")
        #     and setting.get("aws_access_key_id")
        #     and setting.get("aws_secret_access_key")
        # ):
        #     self.aws_lambda = boto3.client(
        #         "lambda",
        #         region_name=setting.get("region_name"),
        #         aws_access_key_id=setting.get("aws_access_key_id"),
        #         aws_secret_access_key=setting.get("aws_secret_access_key"),
        #     )
        # else:
        #     self.aws_lambda = boto3.client("lambda")
        self.aws_lambda = Config.aws_lambda

    def fetch_graphql_schema(
        self,
        context: Dict[str, Any],
        function_name: str,
    ) -> Dict[str, Any]:
        if self.schemas.get(function_name) is None:
            self.schemas[function_name] = Graphql.fetch_graphql_schema(
                context=context,
                funct=function_name,
                aws_lambda=self.aws_lambda
            )
        return self.schemas[function_name]


    def execute_graphql_query(
        self,
        context: Dict[str, Any],
        function_name: str,
        operation_name: str,
        operation_type: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        schema = self.fetch_graphql_schema(context, function_name)
        result = Graphql.execute_graphql_query(
            context=context,
            funct=function_name,
            query=Graphql.generate_graphql_operation(operation_name, operation_type, schema),
            variables=variables,
            aws_lambda=self.aws_lambda
        )
        return result

        
    
class BuildContext(object):
    custom_context = None
    function_name = None
    function_version = None
    invoked_function_arn = None
    memory_limit_in_mb = None
    aws_request_id = None
    log_group_name = None
    log_stream_name = None
    client_context = None
    identity = {
        'cognito_identity_id': None,
        'cognito_identity_pool_id': None
    }
    
    def __init__(self, event, context):
        self.custom_context = {
            'function_name': None,
            'function_version': None,
            'invoked_function_arn': None,
            'memory_limit_in_mb': None,
            'aws_request_id': None,
            'log_group_name': None,
            'log_stream_name': None,
            'client_context': None,
            'identity': {
                'cognito_identity_id': None,
                'cognito_identity_pool_id': None
            }
        }
        if len(context) > 0:
            self.custom_context = context
            self.function_name = self.custom_context.get("function_name")
            self.function_version = self.custom_context.get("function_version")
            self.invoked_function_arn = self.custom_context.get("invoked_function_arn")
            self.memory_limit_in_mb = self.custom_context.get("memory_limit_in_mb")
            self.aws_request_id = self.custom_context.get("aws_request_id")
            self.log_group_name = self.custom_context.get("log_group_name")
            self.log_stream_name = self.custom_context.get("log_stream_name")
            self.client_context = self.custom_context.get("client_context")
            self.identity = self.custom_context.get("identity")
        else:
            fn_configurations = event.get("fnConfigurations", {})
            self.custom_context["invoked_function_arn"] = fn_configurations.get("invoked_function_arn")
            self.custom_context["function_name"] = fn_configurations.get("function")
            self.function_name = fn_configurations.get("function")
            self.invoked_function_arn = fn_configurations.get("invoked_function_arn")

    # @staticmethod
    # def function_name(self):
    #     return self.custom_context.get("function_name")
    
    # @staticmethod
    # def invoked_function_arn(self):
    #     return self.custom_context.get("invoked_function_arn")

    # @staticmethod
    # def function_version(self):
    #     return self.custom_context.get("function_version")
    
    # @staticmethod
    # def memory_limit_in_mb(self):
    #     return self.custom_context.get("memory_limit_in_mb")
    
    # @staticmethod
    # def aws_request_id(self):
    #     return self.custom_context.get("aws_request_id")

    # @staticmethod
    # def log_group_name(self):
    #     return self.custom_context.get("log_group_name")
    
    # @staticmethod
    # def log_stream_name(self):
    #     return self.custom_context.get("log_stream_name")
    
    # @staticmethod
    # def client_context(self):
    #     return self.custom_context.get("client_context")
    
    # @staticmethod
    # def identity(self):
    #     return self.custom_context.get("identity")
    