import logging
import os, re, time
import threading
import shopify

def request_token(logger, settings, params):
    shop = params.get('shop')
    code = params.get('code')
    hmac = params.get('hmac')

    if not shop or not code:
        raise Exception("Missing shop or code")
    app_id = params.get("state")
    config = settings.get("app_settings", {}).get(app_id)
    shopify.Session.setup(api_key=config.get("client_id"), secret=config.get("client_secret"))
    session = shopify.Session(shop, config.get("version", "2025-01"))  # use current API version
    try:
        access_token = session.request_token(params)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise Exception(str(e))
    return access_token


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
    