from datetime import datetime
from typing import List, Dict, Any, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from license_models import (
    License, APIPermission, ServicePermission,
    UIPermission, ButtonPermission, FeatureType, UsageLimit
)
import uuid
import os
import json

class LicenseGenerator:
    def __init__(self, private_key_path: str):
        """初始化许可证生成器
        
        Args:
            private_key_path: 私钥文件路径
        """
        with open(private_key_path, "rb") as key_file:
            self.private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
    
    def generate_license(
        self,
        customer_id: str,
        not_before: datetime,
        not_after: datetime,
        features: List[Dict[str, Any]],
        usage_limits: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> License:
        """生成许可证
        
        Args:
            customer_id: 客户ID
            not_before: 许可证生效时间
            not_after: 许可证过期时间
            features: 功能特性列表
            usage_limits: 使用限制列表
            metadata: 元数据
            
        Returns:
            License: 生成的许可证对象
        """
        # 创建功能特性对象
        feature_objects = []
        for feature in features:
            feature_type = feature["feature_type"]
            if feature_type == FeatureType.API:
                feature_objects.append(APIPermission(
                    feature_id=feature["feature_id"],
                    feature_name=feature["feature_name"],
                    feature_type=feature["feature_type"],
                    method=feature["method"],
                    path=feature["path"],
                    rate_limit=feature.get("rate_limit")
                ))
            elif feature_type == FeatureType.SERVICE:
                feature_objects.append(ServicePermission(
                    feature_id=feature["feature_id"],
                    feature_name=feature["feature_name"],
                    feature_type=feature["feature_type"],
                    service_name=feature["service_name"],
                    version=feature["version"],
                    endpoints=feature["endpoints"]
                ))
            elif feature_type == FeatureType.UI:
                feature_objects.append(UIPermission(
                    feature_id=feature["feature_id"],
                    feature_name=feature["feature_name"],
                    feature_type=feature["feature_type"],
                    component_id=feature["component_id"],
                    component_type=feature["component_type"],
                    visibility=feature["visibility"]
                ))
            elif feature_type == FeatureType.BUTTON:
                feature_objects.append(ButtonPermission(
                    feature_id=feature["feature_id"],
                    feature_name=feature["feature_name"],
                    feature_type=feature["feature_type"],
                    button_id=feature["button_id"],
                    action_type=feature["action_type"],
                    enabled=feature["enabled"]
                ))
        
        # 创建使用限制对象
        usage_limit_objects = [
            UsageLimit(
                metric_type=limit["metric_type"],
                max_value=limit["max_value"],
                current_value=limit["current_value"]
            )
            for limit in usage_limits
        ]
        
        # 创建许可证对象
        license_obj = License(
            license_id=str(uuid.uuid4()),
            customer_id=customer_id,
            not_before=not_before,
            not_after=not_after,
            features=feature_objects,
            usage_limits=usage_limit_objects,
            metadata=metadata or {}
        )
        
        # 签名许可证
        self._sign_license(license_obj)
        
        # 保存许可证到文件
        self._save_license(license_obj)
        
        return license_obj
    
    def _sign_license(self, license_obj: License) -> None:
        """签名许可证
        
        Args:
            license_obj: 许可证对象
        """
        # 将许可证对象转换为字节
        license_bytes = license_obj.dump_for_sign()

        # 使用私钥签名
        signature = self.private_key.sign(
            license_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        # 设置签名
        license_obj.signature = signature.hex()

    def _save_license(self, license_obj: License) -> None:
        """保存许可证到文件
        
        Args:
            license_obj: 许可证对象
        """
        # 创建 licenses 目录（如果不存在）
        os.makedirs("licenses", exist_ok=True)
        
        # 生成文件名：customer_id_license_id.json
        filename = f"licenses/{license_obj.customer_id}_{license_obj.license_id}.json"
        
        # 将许可证对象转换为字典
        license_dict = license_obj.model_dump()
        
        # 自定义 JSON 编码器
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)
        
        # 保存为 JSON 文件
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(license_dict, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
        
        print(f"许可证已保存到: {filename}")
