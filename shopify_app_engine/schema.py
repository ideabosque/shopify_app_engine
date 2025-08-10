#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "jeffreyw"

import time
from typing import Any, Dict

from graphene import (
    Boolean,
    DateTime,
    Field,
    Int,
    List,
    ObjectType,
    ResolveInfo,
    String,
)

from .mutations.config_setting import InsertUpdateConfigSetting
from .queries.config_setting import resolve_config_setting_list
# from .mutations.app import DeleteApp, InsertUpdateApp
# from .mutations.thread import DeleteThread, InsertThread
# from .queries.app import resolve_app, resolve_app_list
# from .queries.app_config import resolve_app_config, resolve_app_config_list
# from .queries.thread import resolve_thread, resolve_thread_list
from .types.config_setting import ConfigSettingType, ConfigSettingListType, VariableType


def type_class():
    return [
        ConfigSettingType,
        ConfigSettingListType,
        VariableType
    ]


class Query(ObjectType):
    ping = String()
    config_setting_list = Field(
        ConfigSettingListType,
        shop=String(required=True),
        setting_id=String()
    )

    def resolve_ping(self, info: ResolveInfo) -> str:
        return f"Hello at {time.strftime('%X')}!!"

    def resolve_config_setting_list(self, info: ResolveInfo, **kwargs: Dict[str, Any]) -> ConfigSettingListType:
        return resolve_config_setting_list(info, **kwargs)


class Mutations(ObjectType):
    insert_update_config_setting = InsertUpdateConfigSetting.Field()
