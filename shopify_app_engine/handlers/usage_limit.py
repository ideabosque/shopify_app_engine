from silvaengine_definitions.pynamodb.models.usage import insert_update_usage_limit, get_usage_limit


def process_usage_limit(logger, setting, partition_key, app_subscription):
    default_usage_keys = ["conversation"]
    usage_keys = list(set(setting.get("avaliable_usage_keys",[]) + default_usage_keys))
    
    available_status_mapping = {
        "ACTIVE": "ACTIVE",
        "CANCELLED": "CANCELLED"
    }
    if app_subscription.status not in available_status_mapping: 
        return
    
    if app_subscription.quotas is None:
        return
    
    quotas = app_subscription.quotas.__dict__["attribute_values"]
    for usage_key in usage_keys:
        if usage_key not in quotas:
            continue
        usage_quota = quotas.get(usage_key, {})
        limit_item = get_usage_limit(partition_key, usage_key)
        if limit_item is not None:
            if app_subscription.current_period_start < limit_item.period_start:
                continue

        limit_data = {
            "partition_key": partition_key,
            "usage_key": usage_key,
            "usage_limit": int(usage_quota.get("lte", 0)),
            "allow_overage": usage_quota.get("allow_overage", False),
            "period_start": app_subscription.current_period_start,
            "period_end": app_subscription.current_period_end,
            "created_from": "shopify",
            "status": available_status_mapping[app_subscription.status]
        }

        if app_subscription.current_period_end is None:
            limit_data.pop("period_end")

        insert_update_usage_limit(**limit_data)