# 许可证管理系统

## 简介
本系统用于生成、验证和管理软件许可证，支持多种权限控制和使用限制。

## 项目结构
```
license_manager/
├── src/
│   ├── license_models.py      # 许可证模型定义
│   ├── license_generator.py   # 许可证生成器
│   ├── license_validator.py   # 许可证验证器
│   ├── example.py             # 基础示例：生成、校验、基本权限验证
│   └── feature_control_example.py  # 高级示例：细粒度功能权限控制
├── keys/
│   ├── private_key.pem        # 私钥（用于签名）
│   └── public_key.pem         # 公钥（用于验证）
├── licenses/                  # 许可证存储目录
│   ├── customer_001_xxx.json  # 客户许可证文件
│   └── customer_002_xxx.json  # 客户许可证文件
└── README.md                  # 项目说明文档
```

## 功能特性
- 许可证生成和签名
- 许可证验证（签名、时间、环境）
- 多种权限控制（API、服务、UI、按钮）
- 使用限制管理
- 安全时间戳存储
- 硬件绑定（可选）

## 系统要求
- Python 3.9+
- 依赖包：见 requirements.txt

## 安装
1. 克隆仓库
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法
### 生成许可证
使用 `LicenseGenerator` 生成许可证，需要提供私钥文件路径。
```python
from license_generator import LicenseGenerator
generator = LicenseGenerator("private_key.pem")
license_obj = generator.generate_license(...)
```

### 验证许可证
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

### 权限控制
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

## 示例
见 `example.py` 和 `feature_control_example.py`


## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 生成密钥对
```bash
openssl genrsa -out keys/private_key.pem 2048
openssl rsa -in keys/private_key.pem -pubout -out keys/public_key.pem
```

### 3. 运行示例

#### 基础示例 (example.py)
```bash
python src/example.py
```
该示例展示：
- 生成许可证
- 验证许可证有效性
- 检查基本权限（API、节点、用户等）

#### 高级示例 (feature_control_example.py)
```bash
python src/feature_control_example.py
```
该示例展示：
- 创建多种类型的功能权限（API、微服务、UI组件、按钮）
- 生成包含多种权限的许可证
- 验证每种粒度的权限
- 使用装饰器进行权限控制

## 使用说明

### 生成许可证
```python
from license_generator import LicenseGenerator

generator = LicenseGenerator("keys/private_key.pem")
license = generator.generate_license(
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
        {"metric_type": "nodes", "max_value": 10, "current_value": 0},
        {"metric_type": "users", "max_value": 100, "current_value": 0}
    ]
)
```

生成的许可证会自动保存到 `licenses` 目录下，文件名格式为：`customer_id_license_id.json`

### 加载许可证
```python
from license_validator import LicenseValidator

validator = LicenseValidator("keys/public_key.pem")
license = validator.load_license_from_file("licenses/customer_001_xxx.json")
```

### 验证许可证
```python
is_valid = validator.is_valid(license)
```

### 权限控制
```python
# API权限验证
api_allowed = validator.check_api_permission(
    license,
    method="POST",
    path="/api/v1/users"
)

# 微服务权限验证
service_allowed = validator.check_service_permission(
    license,
    service_name="order-service",
    endpoint="/orders"
)

# UI组件权限验证
ui_allowed = validator.check_ui_permission(
    license,
    component_id="stats-dashboard"
)

# 按钮权限验证
button_allowed = validator.check_button_permission(
    license,
    button_id="export-data-btn"
)
```

### 使用装饰器
```python
@require_api_permission("POST", "/api/v1/users")
def create_user(user_data):
    # 创建用户的业务逻辑
    pass

@require_service_permission("order-service", "/orders")
def create_order(order_data):
    # 创建订单的业务逻辑
    pass
```

## 许可证存储

系统会自动将生成的许可证保存为 JSON 文件，存储在 `licenses` 目录下。每个许可证文件包含：

- 许可证ID
- 客户ID
- 生效时间
- 过期时间
- 功能权限配置
- 使用限制
- 元数据
- 签名

许可证文件命名格式：`customer_id_license_id.json`

## 注意事项
1. 确保密钥对安全存储
2. 定期更新许可证
3. 合理设置功能权限和使用限制
4. 在生产环境中使用前进行充分测试
5. 妥善保管许可证文件，防止被篡改
 