#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

from typing import Any, Dict

from graphene import ResolveInfo

from silvaengine_utility import Utility

from ..handlers.app import App
from ..types.config_setting import ConfigSettingType, VariableType, ConfigSettingListType


def resolve_config_setting_list(info: ResolveInfo, **kwargs: Dict[str, Any]) -> ConfigSettingListType:
    shop = kwargs.get("shop")
    setting_id = kwargs.get("setting_id")
    app = App(info.context.get("logger"), **info.context.get("setting"))
    config_settings = []
    if setting_id is not None:
        app.vaildate_setting_id(shop, setting_id)
        config_setting = app.get_config_setting_by_setting_id(setting_id)
        config_settings.extend(config_setting)
    else:
        config_settings = app.get_config_settings(shop)
    

    config_setting_list = {"config_setting_list": app.formated_config_setting_list(shop, config_settings)}
    
    return ConfigSettingListType(**Utility.json_loads(Utility.json_dumps(config_setting_list)))


