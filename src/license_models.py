from datetime import datetime
from typing import Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
import json

class FeatureType(str, Enum):
    """功能类型枚举"""
    API = "api"           # API级别
    SERVICE = "service"   # 微服务级别
    UI = "ui"            # UI组件级别
    BUTTON = "button"    # 按钮级别

class FeaturePermission(BaseModel):
    """功能权限模型"""
    feature_id: str
    feature_name: str
    feature_type: FeatureType
    enabled: bool = True
    metadata: Dict[str, str] = Field(default_factory=dict)

class APIPermission(FeaturePermission):
    """API权限模型"""
    method: str  # HTTP方法
    path: str    # API路径
    rate_limit: Optional[int] = None  # 速率限制

class ServicePermission(FeaturePermission):
    """微服务权限模型"""
    service_name: str
    version: str
    endpoints: List[str] = Field(default_factory=list)

class UIPermission(FeaturePermission):
    """UI组件权限模型"""
    component_id: str
    component_type: str
    visibility: bool = True

class ButtonPermission(FeaturePermission):
    """按钮权限模型"""
    button_id: str
    action_type: str
    enabled: bool = True

class UsageLimit(BaseModel):
    """使用限制模型"""
    metric_type: str  # 如 "nodes", "users", "api_calls"
    max_value: int
    current_value: int = 0

class License(BaseModel):
    """许可证主模型"""
    license_id: str
    customer_id: str
    not_before: datetime
    not_after: datetime
    features: List[Union[APIPermission, ServicePermission, UIPermission, ButtonPermission]] = Field(default_factory=list)
    usage_limits: List[UsageLimit] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)
    signature: Optional[str] = None

    def is_valid(self) -> bool:
        """检查许可证是否在有效期内"""
        now = datetime.utcnow()
        return self.not_before <= now <= self.not_after

    def check_feature(self, feature_id: str, feature_type: FeatureType) -> bool:
        """检查特定功能是否可用"""
        for feature in self.features:
            if feature.feature_id == feature_id and feature.feature_type == feature_type:
                return feature.enabled
        return False

    def check_api_permission(self, method: str, path: str) -> bool:
        """检查API权限"""
        for feature in self.features:
            if (isinstance(feature, APIPermission) and 
                feature.method == method and 
                feature.path == path):
                return feature.enabled
        return False

    def check_service_permission(self, service_name: str, endpoint: str) -> bool:
        """检查微服务权限"""
        for feature in self.features:
            if (isinstance(feature, ServicePermission) and 
                feature.service_name == service_name and 
                endpoint in feature.endpoints):
                return feature.enabled
        return False

    def check_ui_permission(self, component_id: str) -> bool:
        """检查UI组件权限"""
        for feature in self.features:
            if (isinstance(feature, UIPermission) and 
                feature.component_id == component_id):
                return feature.visibility
        return False

    def check_button_permission(self, button_id: str) -> bool:
        """检查按钮权限"""
        for feature in self.features:
            if (isinstance(feature, ButtonPermission) and 
                feature.button_id == button_id):
                return feature.enabled
        return False

    def check_usage_limit(self, metric_type: str, value: int = 1) -> bool:
        """检查使用限制"""
        for limit in self.usage_limits:
            if limit.metric_type == metric_type:
                return limit.current_value + value <= limit.max_value
        return True

    def dump_for_sign(self):
        data = self.model_dump(exclude={"signature"})
        for k in ["not_before", "not_after"]:
            v = data.get(k)
            if isinstance(v, datetime):
                data[k] = v.replace(microsecond=0).isoformat()
        # 递归处理 features
        def feature_to_dict(f):
            if hasattr(f, 'model_dump'):
                return f.model_dump()
            elif isinstance(f, dict):
                return f
            else:
                return dict(f)
        data["features"] = [feature_to_dict(f) for f in self.features]
        data["usage_limits"] = [l.model_dump() if hasattr(l, 'model_dump') else l for l in self.usage_limits]
        return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8") 