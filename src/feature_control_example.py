from datetime import datetime, timedelta
from license_models import (
    License, APIPermission, ServicePermission,
    UIPermission, ButtonPermission, FeatureType
)
from license_generator import LicenseGenerator
from license_validator import LicenseValidator

def create_feature_license():
    """创建包含不同粒度功能许可的许可证"""
    generator = LicenseGenerator("private_key.pem")
    
    # 创建API权限
    api_permission = APIPermission(
        feature_id="api_001",
        feature_name="用户管理API",
        feature_type=FeatureType.API,
        method="POST",
        path="/api/v1/users",
        rate_limit=1000
    )
    
    # 创建微服务权限
    service_permission = ServicePermission(
        feature_id="service_001",
        feature_name="订单服务",
        feature_type=FeatureType.SERVICE,
        service_name="order-service",
        version="1.0.0",
        endpoints=["/orders", "/payments"]
    )
    
    # 创建UI组件权限
    ui_permission = UIPermission(
        feature_id="ui_001",
        feature_name="数据统计面板",
        feature_type=FeatureType.UI,
        component_id="stats-dashboard",
        component_type="dashboard",
        visibility=True
    )
    
    # 创建按钮权限
    button_permission = ButtonPermission(
        feature_id="button_001",
        feature_name="导出数据按钮",
        feature_type=FeatureType.BUTTON,
        button_id="export-data-btn",
        action_type="export",
        enabled=True
    )
    
    # 生成许可证
    license_obj = generator.generate_license(
        customer_id="customer_001",
        not_before=datetime.utcnow(),
        not_after=datetime.utcnow() + timedelta(days=365),
        features=[
            {
                "feature_id": "api_001",
                "feature_name": "用户管理API",
                "feature_type": FeatureType.API,
                "method": "POST",
                "path": "/api/v1/users",
                "rate_limit": 1000
            },
            {
                "feature_id": "service_001",
                "feature_name": "订单服务",
                "feature_type": FeatureType.SERVICE,
                "service_name": "order-service",
                "version": "1.0.0",
                "endpoints": ["/orders", "/payments"]
            },
            {
                "feature_id": "ui_001",
                "feature_name": "数据统计面板",
                "feature_type": FeatureType.UI,
                "component_id": "stats-dashboard",
                "component_type": "dashboard",
                "visibility": True
            },
            {
                "feature_id": "button_001",
                "feature_name": "导出数据按钮",
                "feature_type": FeatureType.BUTTON,
                "button_id": "export-data-btn",
                "action_type": "export",
                "enabled": True
            }
        ],
        usage_limits=[
            {"metric_type": "nodes", "max_value": 10, "current_value": 0},
            {"metric_type": "users", "max_value": 100, "current_value": 0}
        ]
    )
    
    return license_obj

def verify_feature_permissions():
    """验证不同粒度的功能许可"""
    validator = LicenseValidator("public_key.pem")
    license_obj = create_feature_license()
    
    # 验证API权限
    api_allowed = validator.check_api_permission(
        license_obj,
        method="POST",
        path="/api/v1/users"
    )
    print(f"API权限验证结果: {api_allowed}")
    
    # 验证微服务权限
    service_allowed = validator.check_service_permission(
        license_obj,
        service_name="order-service",
        endpoint="/orders"
    )
    print(f"微服务权限验证结果: {service_allowed}")
    
    # 验证UI组件权限
    ui_allowed = validator.check_ui_permission(
        license_obj,
        component_id="stats-dashboard"
    )
    print(f"UI组件权限验证结果: {ui_allowed}")
    
    # 验证按钮权限
    button_allowed = validator.check_button_permission(
        license_obj,
        button_id="export-data-btn"
    )
    print(f"按钮权限验证结果: {button_allowed}")

# 在微服务中使用装饰器进行权限控制
from functools import wraps

def require_api_permission(method: str, path: str):
    """API权限控制装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not validator.check_api_permission(license_obj, method, path):
                raise PermissionError(f"没有权限访问API: {method} {path}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_service_permission(service_name: str, endpoint: str):
    """微服务权限控制装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not validator.check_service_permission(license_obj, service_name, endpoint):
                raise PermissionError(f"没有权限访问服务: {service_name} {endpoint}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@require_api_permission("POST", "/api/v1/users")
def create_user(user_data):
    # 创建用户的业务逻辑
    pass

@require_service_permission("order-service", "/orders")
def create_order(order_data):
    # 创建订单的业务逻辑
    pass

if __name__ == "__main__":
    verify_feature_permissions() 