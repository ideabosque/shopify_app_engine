#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

from graphene import DateTime, Int, List, ObjectType, String, Union, Float, Field, Boolean

from silvaengine_dynamodb_base import ListObjectType
from silvaengine_utility import JSONCamelCase
class AddressType(ObjectType):
    first_name = String()
    last_name = String()
    name = String()
    company = String()
    address1 = String()
    address2 = String()
    city = String()
    province = String()
    country = String()
    zip = String()
    phone = String()
    province_code = String()
    country_code = String()
    default = Boolean()

class LineItemType(ObjectType):
    title = String()
    variant_title = String()
    sku = String()
    vendor = String()
    quantity = Int()
    sku = String()
    name = String()
    price = String()

class DraftOrderType(ObjectType):
    email = String()
    name = String()
    note = String()
    status = String()
    total_price = String()
    subtotal_price = String()
    total_tax = String()
    line_items = List(LineItemType)
    shipping_address = Field(AddressType)
    billing_address = Field(AddressType)

class VariantProductType(ObjectType):
    id = String()
    title = String()
    price = String()
    position = Int()
    option1 = String()
    option2 = String()
    option3 = String()
    barcode = String()
    sku = String()
    weight = Float()
    weight_unit = String()
    image_id = String()

class OptionType(ObjectType):
    id = String()
    product_id = String()
    name = String()
    position = Int()
    values = List(String)

class ImageType(ObjectType):
    id = String()
    alt = String()
    position = Int()
    src = String()
    width = String()
    height = String()
    variant_ids = List(String)

class ProductType(ObjectType):
    id = String()
    handle = String()
    title = String()
    body_html = String()
    vendor = String()
    product_type = String()
    status = String()
    variants = List(VariantProductType)
    images = List(ImageType)
    options = List(OptionType)

class ProductListType(ListObjectType):
    product_list = List(ProductType)

class CustomerType(ObjectType):
    id = String()
    email = String()
    first_name = String()
    last_name = String()
    note = String()
    phone = String()
    tags = String()
    addresses = List(AddressType)
    default_address = Field(AddressType)

# class VariableType(ObjectType):
#     variable = String()
#     value = String()

# class ConfigSettingType(ObjectType):
#     setting_id = String()
#     settings = List(JSONCamelCase)

# class ConfigSettingListType(ListObjectType):
#     config_setting_list = List(ConfigSettingType)

