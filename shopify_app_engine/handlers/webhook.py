import hmac
import hashlib
import base64
from shopify_connector import ShopifyConnector
from ..models.webhook_subscription import insert_update_webhook_subscription, get_webhook_subscriptions_by_shop, delete_webhook_subscription
from ..models.webhook_event import insert_webhook_event, get_webhook_event
from .app_subscription import process_subscription
from .app import App

from silvaengine_utility import Serializer

class ValueExistException(Exception):
    pass

def verify_shopify_webhook(body, hmac_header, shopify_secret):
    digest = hmac.new(
        shopify_secret.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()

    computed_hmac = base64.b64encode(digest).decode()

    return hmac.compare_digest(computed_hmac, hmac_header)

def register_webhook(logger, setting, app_id, shop_domain, access_token):
    config = setting.get("app_settings", {}).get(app_id)
    app_setting = {
        "shop_url": shop_domain,
        "api_version": config.get("version", "2026-01"),
        "private_app_password": access_token
    }
    webhook_url = config.get("webhook_url")
    shopify_connector = ShopifyConnector(logger, **app_setting)
    shopify_webhook_topics = setting.get("shopify_webhook_topics", [])
    default_webhook_topics = [
        "APP_SUBSCRIPTIONS_UPDATE",
        "APP_UNINSTALLED"
    ]
    shopify_webhook_topics.extend(default_webhook_topics)

    shopify_webhook_topics = list(set(shopify_webhook_topics + default_webhook_topics))
    for topic in shopify_webhook_topics:
        try:
            webhook_subscription = shopify_connector.create_webhook_subscription(topic, webhook_url)
            webhook_subscription_data = {
                "shop": App.get_target_id(shop_domain),
                "webhook_subscription_id": webhook_subscription.get("id"),
                "topic": topic,
                "webhook_subscription": webhook_subscription
            }

            insert_update_webhook_subscription(**webhook_subscription_data)
        except Exception as e:
            logger.error(e)
            pass

def delete_webhook(logger, shop):
    # config = setting.get("app_settings", {}).get(app_id)
    # app_setting = {
    #     "shop_url": shop,
    #     "api_version": config.get("version", "2026-01"),
    #     "private_app_password": access_token
    # }
    # shopify_connector = ShopifyConnector(logger, **app_setting)
    try:
        webhook_subscriptions = get_webhook_subscriptions_by_shop(shop)
        if len(webhook_subscriptions) > 0:
            for webhook_subscription in webhook_subscriptions:
                webhook_subscription_id = webhook_subscription.webhook_subscription_id
                # deleted_id = shopify_connector.delete_webhook_subscription(webhook_subscription_id)
                delete_webhook_subscription(shop, webhook_subscription_id) # unstall app can not get access token
    except Exception as e:
        logger.error(e)
        return None
    return None


def handle_webhook(context, params):
    event = params.get("event")
    headers = event.get("headers")

    api_version = headers.get("x-shopify-api-version")
    event_id = headers.get("x-shopify-event-id")
    hmac_sha256 = headers.get("x-shopify-hmac-sha256")
    shop_domain = headers.get("x-shopify-shop-domain")
    topic = headers.get("x-shopify-topic")
    webhook_id = headers.get("x-shopify-webhook-id")
    triggered_at = headers.get("x-shopify-triggered-at")
    shop = App.get_target_id(shop_domain)
    
    if get_webhook_event(shop, event_id) is not None:
        raise ValueExistException("Event is already received.")
    webhook_event_params = {
        "shop": shop,
        "event_id": event_id,
        "webhook_data": Serializer.json_loads(event.get("body"), False, False) if event.get("body") is not None else {},
    }
    # print("insert webhook event")
    context.get("logger").info("insert webhook event")
    insert_webhook_event(**webhook_event_params)

    app_handler = App(context=context, logger=context.get("logger"), **context.get("setting"))
    app_data = app_handler.get_app_by_shop(shop)
    body = event.get("body", None)
    if body is None:
        return
    if event.get("isBase64Encoded", False):
        raw_body = base64.b64decode(body)
    else:
        raw_body = body.encode("utf-8")
    secret =  app_data.get("data", {}).get("clientSecret")
    context.get("logger").info("verify_shopify_webhook")
    if not verify_shopify_webhook(raw_body, hmac_sha256, secret):
        raise Exception("Fail to  verify webhook hmac.")
    
    topic_arr = topic.split("/")
    if len(topic_arr) == 1:
        object_type = topic_arr[0]
        action = None
    else:
        object_type = topic_arr[0]
        action = topic_arr[1]
    
    if object_type == "app_subscriptions":
        context.get("logger").info("process_subscription")
        process_subscription(context, app_data, shop, params.get("app_subscription", {}), True)
        return
    
    if object_type == "app":
        if action == "uninstalled":
            uninstall_params = {
                "shop": shop,
                "app_id": app_data.get("app_id")
            }
            context.get("logger").info("uninstall app")
            app_handler.uninstall_app(**uninstall_params)
            delete_webhook(context.get("logger"), shop)

        return
