# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import logging
from typing import Any, Dict, Optional

import boto3

from silvaengine_utility import Utility


class Config:
    """
    Centralized Configuration Class
    Manages shared configuration variables across the application.
    """

    aws_lambda = None
    aws_sqs = None
    aws_ddb = None
    schemas = {}
    apps = {}

    @classmethod
    def initialize(cls, logger: logging.Logger, **setting: Dict[str, Any]) -> None:
        """
        Initialize configuration setting.
        Args:
            logger (logging.Logger): Logger instance for logging.
            **setting (Dict[str, Any]): Configuration dictionary.
        """
        try:
            cls._set_parameters(setting)
            cls._initialize_aws_services(setting)
            logger.info("Configuration initialized successfully.")
        except Exception as e:
            logger.exception("Failed to initialize configuration.")
            raise e

    @classmethod
    def _set_parameters(cls, setting: Dict[str, Any]) -> None:
        """
        Set application-level parameters.
        Args:
            setting (Dict[str, Any]): Configuration dictionary.
        """
        pass

    @classmethod
    def _initialize_aws_services(cls, setting: Dict[str, Any]) -> None:
        """
        Initialize AWS services, such as the S3 client.
        Args:
            setting (Dict[str, Any]): Configuration dictionary.
        """
        if all(
            setting.get(k)
            for k in ["region_name", "aws_access_key_id", "aws_secret_access_key"]
        ):
            aws_credentials = {
                "region_name": setting["region_name"],
                "aws_access_key_id": setting["aws_access_key_id"],
                "aws_secret_access_key": setting["aws_secret_access_key"],
            }
        else:
            aws_credentials = {}

        cls.aws_lambda = boto3.client("lambda", **aws_credentials)
        cls.aws_sqs = boto3.resource("sqs", **aws_credentials)
        cls.aws_ddb = boto3.resource("dynamodb", **aws_credentials)


    # Fetches and caches GraphQL schema for a given function
    @classmethod
    def fetch_graphql_schema(
        cls,
        logger: logging.Logger,
        endpoint_id: str,
        function_name: str,
        setting: Dict[str, Any] = {},
    ) -> Dict[str, Any]:
        """
        Fetches and caches a GraphQL schema for a given function.

        Args:
            logger: Logger instance for error reporting
            endpoint_id: ID of the endpoint to fetch schema from
            function_name: Name of function to get schema for
            setting: Optional settings dictionary

        Returns:
            Dict containing the GraphQL schema
        """
        # Check if schema exists in cache, if not fetch and store it
        if Config.schemas.get(function_name) is None:
            Config.schemas[function_name] = Utility.fetch_graphql_schema(
                logger,
                endpoint_id,
                function_name,
                setting=setting,
                aws_lambda=Config.aws_lambda,
                execute_mode=setting.get("execute_mode"),
            )
        return Config.schemas[function_name]
    
    
    @classmethod
    def get_app(
        cls,
        target_id: str,
        app_id: Optional[str],
    ) -> Dict[str, Any]:
        target_apps = Config.apps.get(target_id, {})
        
        if app_id is not None:
            # 先尝试精确匹配
            if app_id in target_apps:
                return target_apps[app_id]
        return next(iter(target_apps.values()), None)
    
    @classmethod
    def save_app(
        cls,
        target_id: str,
        app_id: Optional[str],
        app_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        if target_id not in Config.apps:
            Config.apps[target_id] = {}
        
        if app_id not in Config.apps[target_id]:
            Config.apps[target_id][app_id] = app_data
        
        return app_data