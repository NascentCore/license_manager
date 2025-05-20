from datetime import datetime, timedelta
from license_models import (
    License, APIPermission, ServicePermission,
    UIPermission, ButtonPermission, FeatureType, UsageLimit
)
from license_generator import LicenseGenerator
from license_validator import LicenseValidator
import json

def main():
    # 生成密钥对（实际使用时应该提前生成并安全保存）
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    
    # 生成私钥
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # 保存私钥
    with open("private_key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # 保存公钥
    with open("public_key.pem", "wb") as f:
        f.write(private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    
    # 创建许可证生成器
    generator = LicenseGenerator("private_key.pem")
    
    # 创建许可证
    license_obj = generator.generate_license(
        customer_id="customer_001",
        not_before=datetime.utcnow(),
        not_after=datetime.utcnow() + timedelta(days=365),
        features=[
            # API权限
            {
                "feature_id": "api_001",
                "feature_name": "用户管理API",
                "feature_type": FeatureType.API,
                "method": "POST",
                "path": "/api/v1/users",
                "rate_limit": 1000
            },
            # 微服务权限
            {
                "feature_id": "service_001",
                "feature_name": "订单服务",
                "feature_type": FeatureType.SERVICE,
                "service_name": "order-service",
                "version": "1.0.0",
                "endpoints": ["/orders", "/payments"]
            },
            # UI组件权限
            {
                "feature_id": "ui_001",
                "feature_name": "数据统计面板",
                "feature_type": FeatureType.UI,
                "component_id": "stats-dashboard",
                "component_type": "dashboard",
                "visibility": True
            },
            # 按钮权限
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
            # 节点数限制
            {
                "metric_type": "nodes",
                "max_value": 10,
                "current_value": 0
            },
            # 用户数限制
            {
                "metric_type": "users",
                "max_value": 100,
                "current_value": 0
            }
        ],
        metadata={
            "version": "1.0",
            "environment": "production"
        }
    )
    
    # 创建许可证验证器
    validator = LicenseValidator("public_key.pem")
    
    # 调试：输出签名内容和签名
    print('签名内容:', license_obj.dump_for_sign())
    print('签名:', license_obj.signature)
    
    # 验证许可证
    is_valid = validator.validate_license(license_obj)
    print(f"许可证是否有效: {is_valid}")
    
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
    
    # 验证使用限制
    can_add_node = validator.check_usage_limit(license_obj, "nodes", 10)
    print(f"是否可以添加新节点: {can_add_node}")
    
    can_add_users = validator.check_usage_limit(license_obj, "users", 50)
    print(f"是否可以添加50个新用户: {can_add_users}")

def test_modified_license():
    """测试修改许可证内容后的验证结果"""
    # 生成原始许可证
    generator = LicenseGenerator("keys/private_key.pem")
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
            }
        ],
        usage_limits=[
            {"metric_type": "nodes", "max_value": 10, "current_value": 0}
        ]
    )
    
    # 加载许可证文件
    with open(f"licenses/{license_obj.customer_id}_{license_obj.license_id}.json", "r", encoding="utf-8") as f:
        license_dict = json.load(f)
    
    # 修改许可证内容
    print("\n=== 测试修改许可证内容 ===")
    print("1. 修改前验证结果：")
    validator = LicenseValidator("keys/public_key.pem")
    is_valid = validator.validate_license(license_obj)
    print(f"许可证是否有效: {is_valid}")
    
    # 修改内容
    license_dict["not_after"] = "2099-12-31T23:59:59"  # 修改过期时间
    license_dict["usage_limits"][0]["max_value"] = 1000  # 修改节点数限制
    
    # 保存修改后的许可证
    modified_filename = f"licenses/{license_obj.customer_id}_{license_obj.license_id}_modified.json"
    with open(modified_filename, "w", encoding="utf-8") as f:
        json.dump(license_dict, f, ensure_ascii=False, indent=2)
    
    # 加载修改后的许可证
    modified_license = License.model_validate(license_dict)
    
    # 验证修改后的许可证
    print("\n2. 修改后验证结果：")
    is_valid = validator.validate_license(modified_license)
    print(f"许可证是否有效: {is_valid}")
    
    if not is_valid:
        print("原因：许可证内容被修改，签名验证失败")

if __name__ == "__main__":
    main()
    test_modified_license() 