# 使用指南

## 许可证生成
使用 `LicenseGenerator` 生成许可证，需要提供私钥文件路径。
```python
from license_generator import LicenseGenerator
generator = LicenseGenerator("private_key.pem")
license_obj = generator.generate_license(...)
```

## 许可证验证
使用 `LicenseValidator` 验证许可证，需要提供公钥文件路径和用于时间戳加密的密钥。
```python
from license_validator import LicenseValidator
from cryptography.fernet import Fernet

# 生成或加载密钥
secret_key = Fernet.generate_key()  # 实际应用中应安全存储

# 创建验证器
validator = LicenseValidator("public_key.pem", secret_key)

# 验证许可证
is_valid = validator.validate_license(license_obj)
```

## 权限控制
系统支持多种权限控制：
- API权限
- 服务权限
- UI组件权限
- 按钮权限
- 使用限制

## 安全说明
- 私钥和公钥应妥善保管
- 时间戳加密密钥应安全存储
- 在Kubernetes环境中，可启用环境验证 