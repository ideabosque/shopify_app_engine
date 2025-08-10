# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import traceback
from typing import Any, Dict

from graphene import Boolean, Field, Int, Mutation, String

from silvaengine_utility import JSON, Utility
from ..types.config_setting import ConfigSettingType, VariableType
from ..handlers.app import App

class InsertUpdateConfigSetting(Mutation):
    config_setting = Field(ConfigSettingType)

    class Arguments:
        shop = String(required=True)
        setting_id = String(required=True)
        settings = JSON(required=True)

    @staticmethod
    def mutate(root: Any, info: Any, **kwargs: Dict[str, Any]) -> "InsertUpdateConfigSetting":
        try:
            app = App(info.context.get("logger"), **info.context.get("setting"))
            shop = kwargs.get("shop")
            setting_id = kwargs.get("setting_id")
            settings = [
                item
                for item in kwargs.get("settings", [])
                if item.get("variable") and item.get("value")
            ]
            app.insert_update_config_settings(shop, setting_id, settings)
            
            items = app.get_config_setting_by_setting_id(setting_id)
            
            config_setting = {
                "setting_id": setting_id,
                "settings": []
            }
            for item in items:
                config_setting["settings"].append(
                    VariableType(**Utility.json_loads(Utility.json_dumps({
                        "variable": item.get("variable"),
                        "value": item.get("value")
                    }))
                    )
                )
            
            return InsertUpdateConfigSetting(config_setting=ConfigSettingType(**Utility.json_loads(Utility.json_dumps(config_setting))))
        except Exception as e:
            log = traceback.format_exc()
            info.context.get("logger").error(log)
            raise e

