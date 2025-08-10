#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

from graphene import DateTime, Int, List, ObjectType, String, Union

from silvaengine_dynamodb_base import ListObjectType
from silvaengine_utility import JSON

class VariableType(ObjectType):
    variable = String()
    value = String()

class ConfigSettingType(ObjectType):
    setting_id = String()
    settings = List(JSON)

class ConfigSettingListType(ListObjectType):
    config_setting_list = List(ConfigSettingType)

