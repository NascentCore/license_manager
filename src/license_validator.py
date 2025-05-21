import json
from typing import Optional
from datetime import datetime
import time

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from license_models import License, FeatureType
from hardware_validator import BootTimeValidator, TimeSyncValidator
from secure_time_storage import SecureTimeStorage

class LicenseValidator:
    def __init__(self, public_key_path: str, secret_key: bytes):
        """初始化许可证验证器
        
        Args:
            public_key_path: 公钥文件路径
            secret_key: 密钥
        """
        self.public_key = load_pem_public_key(open(public_key_path, 'rb').read())
        # self.env_validator = KubernetesHardwareValidator()  # 暂时注释掉
        self.boot_validator = BootTimeValidator()
        self.time_sync = TimeSyncValidator()
        self.time_storage = SecureTimeStorage(secret_key)
        
        # 初始化验证状态
        self._initialize_validation()

    def _initialize_validation(self):
        """初始化验证状态"""
        current_time = time.time()
        
        # 验证时间合理性
        if not self.boot_validator.validate_time(current_time):
            raise ValueError("系统时间异常：当前时间早于系统启动时间")
            
        if not self.time_sync.validate_time(current_time):
            raise ValueError("系统时间异常：与时间同步源差异过大")
            
        # 验证时间戳存储
        if not self.time_storage.validate_storage():
            raise ValueError("时间戳存储验证失败")
            
        # 记录初始状态
        self.initial_state = {
            # 'env_info': self.env_validator.get_environment_info(),
            'boot_time': self.boot_validator.boot_time,
            'current_time': current_time,
            'sync_sources': self.time_sync.sync_sources
        }

    def validate_license(self, license_obj: License) -> bool:
        """验证许可证的有效性
        
        Args:
            license_obj: 许可证对象
            
        Returns:
            bool: 许可证是否有效
        """
        # 获取当前时间
        current_time = time.time()
        
        # 验证时间合理性
        if not self.boot_validator.validate_time(current_time):
            return False
            
        if not self.time_sync.validate_time(current_time):
            return False
            
        # 验证时间戳存储
        if not self.time_storage.validate_storage():
            return False
            
        # # 验证环境信息
        # current_env = self.env_validator.get_environment_info()
        # if not self._validate_environment(current_env):
        #     return False
            
        # 验证许可证时间
        now = datetime.fromtimestamp(current_time)
        if not (license_obj.not_before <= now <= license_obj.not_after):
            return False
            
        # 验证签名
        if not self._verify_signature(license_obj):
            return False
            
        # 更新时间戳
        self.time_storage.update_timestamps()
        
        return True
        
    def check_feature(self, license_obj: License, feature_id: str, feature_type: FeatureType) -> bool:
        """检查特定功能是否可用
        
        Args:
            license_obj: 许可证对象
            feature_id: 功能ID
            feature_type: 功能类型
            
        Returns:
            bool: 功能是否可用
        """
        if not self.validate_license(license_obj):
            return False
            
        return license_obj.check_feature(feature_id, feature_type)
        
    def check_api_permission(self, license_obj: License, method: str, path: str) -> bool:
        """检查API权限
        
        Args:
            license_obj: 许可证对象
            method: HTTP方法
            path: API路径
            
        Returns:
            bool: 是否有权限访问API
        """
        if not self.validate_license(license_obj):
            return False
            
        return license_obj.check_api_permission(method, path)
        
    def check_service_permission(self, license_obj: License, service_name: str, endpoint: str) -> bool:
        """检查微服务权限
        
        Args:
            license_obj: 许可证对象
            service_name: 服务名称
            endpoint: 端点路径
            
        Returns:
            bool: 是否有权限访问服务
        """
        if not self.validate_license(license_obj):
            return False
            
        return license_obj.check_service_permission(service_name, endpoint)
        
    def check_ui_permission(self, license_obj: License, component_id: str) -> bool:
        """检查UI组件权限
        
        Args:
            license_obj: 许可证对象
            component_id: 组件ID
            
        Returns:
            bool: 组件是否可见
        """
        if not self.validate_license(license_obj):
            return False
            
        return license_obj.check_ui_permission(component_id)
        
    def check_button_permission(self, license_obj: License, button_id: str) -> bool:
        """检查按钮权限
        
        Args:
            license_obj: 许可证对象
            button_id: 按钮ID
            
        Returns:
            bool: 按钮是否可用
        """
        if not self.validate_license(license_obj):
            return False
            
        return license_obj.check_button_permission(button_id)
        
    def check_usage_limit(self, license_obj: License, metric_type: str, value: int = 1) -> bool:
        """检查使用限制
        
        Args:
            license_obj: 许可证对象
            metric_type: 指标类型
            value: 使用值
            
        Returns:
            bool: 是否在限制范围内
        """
        if not self.validate_license(license_obj):
            return False
            
        return license_obj.check_usage_limit(metric_type, value)
        
    def _verify_signature(self, license_obj: License) -> bool:
        """验证许可证签名
        
        Args:
            license_obj: 许可证对象
            
        Returns:
            bool: 签名是否有效
        """
        if not license_obj.signature:
            return False
            
        try:
            # 将许可证对象转换为字节
            license_bytes = license_obj.dump_for_sign()

            # 使用公钥验证签名
            self.public_key.verify(
                bytes.fromhex(license_obj.signature),
                license_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            return True
        except Exception as e:
            print('签名校验异常:', e)
            return False

    def _validate_environment(self, current_env: dict) -> bool:
        """验证环境信息
        
        Args:
            current_env: 当前环境信息
            
        Returns:
            bool: 环境信息是否有效
        """
        # 暂时跳过环境验证
        return True 