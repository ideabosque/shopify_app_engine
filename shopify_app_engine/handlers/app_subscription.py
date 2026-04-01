from shopify_connector import ShopifyConnector
from silvaengine_utility import Serializer
from ..models.app_subscription import insert_update_app_subscription, get_active_app_subscription, get_app_subscription
from ..handlers.usage_limit import process_usage_limit
from ..handlers.app import App
from datetime import datetime
def get_active_subscription(context, shop_domain, app_data):
    shop = App.get_target_id(shop_domain)
    app_subscription = get_active_app_subscription(shop)
    if app_subscription is None:
        app_setting = {
            "shop_url": shop_domain,
            "api_version": app_data.get("appConfig",{}).get("configruation",{}).get("version", "2026-01"),
            "private_app_password": app_data.get("accessToken")
        }
        shopify_connector = ShopifyConnector(context.get("logger"), **app_setting)
        active_subscriptions = shopify_connector.get_active_subscriptions()
        if active_subscriptions is None or len(active_subscriptions) == 0:
            return None
        else:
            active_subscription = active_subscriptions[0]
            app_subscription = active_subscription
            process_subscription(context, app_data, shop, active_subscription, False)
            app_subscription = get_active_app_subscription(shop)
    if app_subscription is not None:
        return app_subscription.__dict__["attribute_values"]
    return app_subscription

def process_subscription(context, app_data, shop, app_subscription, is_webhook):
    logger = context.get("logger")
    setting = context.get("setting")
    plan_name = app_subscription.get("name")
    plan_code = app_subscription.get("plan_handle") if app_subscription.get("plan_handle") else setting.get("shopify_plan_mapping", {}).get(plan_name)
    quotas = setting.get("shopify_plan_quotas", {}).get(plan_code, {})
    status = app_subscription.get("status")
    if is_webhook:
        app_setting = {
            "shop_url": shop,
            "api_version": app_data.get("appConfig",{}).get("configruation",{}).get("version", "2026-01"),
            "private_app_password": app_data.get("accessToken")
        }
        shopify_connector = ShopifyConnector(logger, **app_setting)
        app_subscription_node = shopify_connector.get_subscription(app_subscription.get("admin_graphql_api_id"))
    created_at = app_subscription_node.get("createdAt") if is_webhook else app_subscription.get("createdAt")
    current_period_end = app_subscription_node.get("currentPeriodEnd") if is_webhook else app_subscription.get("currentPeriodEnd")

    subscription_id = app_subscription.get("admin_graphql_api_id") if is_webhook else app_subscription.get("id")
    app_subscription_params = {
        "shop": shop,
        "app_subscription_id": subscription_id,
        "plan_name": plan_name,
        "plan_code": plan_code,
        "status": status,
        "interval": app_subscription.get("interval"),
        "quotas": quotas,
        "subscription_created_at": datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ"),
        "current_period_start": datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ"),
        "current_period_end": datetime.strptime(current_period_end, "%Y-%m-%dT%H:%M:%SZ"),
        "trial_days": app_subscription_node.get("trialDays") if is_webhook else app_subscription.get("trialDays"),
        "line_items": app_subscription_node.get("lineItems") if is_webhook else app_subscription.get("lineItems"),
    }

    processed_app_subscription = {
        key: value
        for key, value in app_subscription_params.items()
        if value is not None
    }

    insert_update_app_subscription(**processed_app_subscription)
    existing_app_subscription = get_app_subscription(shop, subscription_id)

    process_usage_limit(logger, setting, context.get("partition_key"), existing_app_subscription)
    # if status in ["CANCELLED", "DECLINED", "EXPIRED"]:
    #     ## To Do  delete usage limit
    #     return
    
    # if status == "ACTIVE":
    #     ## To Do  insert/update usage limit
    #     return
