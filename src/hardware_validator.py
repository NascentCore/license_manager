import sys
import time
import uuid
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import os

class BootTimeValidator:
    def __init__(self):
        self.boot_time = self._get_boot_time()
        
    def _get_boot_time(self) -> float:
        """获取系统启动时间"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime = float(f.read().split()[0])
            return time.time() - uptime
        except:
            return time.time()
            
    def validate_time(self, current_time: float) -> bool:
        """验证时间是否合理"""
        # 当前时间不能早于系统启动时间
        return current_time >= self.boot_time

class TimeSyncValidator:
    def __init__(self, ntp_servers: List[str] = None):
        """初始化时间同步验证器
        
        Args:
            ntp_servers: NTP服务器列表，如果为None则使用默认服务器
        """
        self.ntp_servers = ntp_servers or [
            'pool.ntp.org',
            'time.windows.com',
            'time.apple.com',
            'time.google.com'
        ]
        self.sync_sources = self._get_sync_sources()
        self.last_ntp_time = None
        self.last_sync_time = time.time()
        
    def _get_sync_sources(self) -> List[Tuple[str, float]]:
        """获取可用的时间同步源"""
        sources = []
        
        # 检查NTP服务器
        for server in self.ntp_servers:
            try:
                import ntplib
                ntp_client = ntplib.NTPClient()
                response = ntp_client.request(server, timeout=1)
                sources.append(('ntp', response.tx_time))
                self.last_ntp_time = response.tx_time
                self.last_sync_time = time.time()
                break  # 只要有一个NTP服务器响应就退出
            except:
                continue
            
        # 检查系统时间同步服务
        try:
            result = subprocess.check_output(['timedatectl', 'status'])
            if b'NTP synchronized: yes' in result:
                sources.append(('systemd-timesyncd', time.time()))
        except:
            pass
            
        return sources
        
    def get_ntp_time(self) -> Optional[float]:
        """获取NTP时间
        
        Returns:
            float: NTP时间戳，如果获取失败则返回None
        """
        # 如果上次同步时间超过5分钟，重新同步
        if time.time() - self.last_sync_time > 300:
            self.sync_sources = self._get_sync_sources()
            
        return self.last_ntp_time
        
    def validate_time(self, current_time: float) -> bool:
        """验证时间是否合理"""
        if not self.sync_sources:
            return True
            
        # 获取NTP时间
        ntp_time = self.get_ntp_time()
        if ntp_time is not None:
            # 检查与NTP时间的差异
            time_diff = abs(current_time - ntp_time)
            if time_diff > 300:  # 允许5分钟误差
                return False
                
        # 检查其他时间同步源
        for source, source_time in self.sync_sources:
            if source != 'ntp':  # 已经检查过NTP时间
                time_diff = abs(current_time - source_time)
                if time_diff > 300:  # 允许5分钟误差
                    return False
                    
        return True
        
    def force_sync(self) -> bool:
        """强制同步时间
        
        Returns:
            bool: 同步是否成功
        """
        self.sync_sources = self._get_sync_sources()
        return len(self.sync_sources) > 0 

class KubernetesHardwareValidator:
    def __init__(self):
        self.node_info = self._get_node_info()
        self.pod_info = self._get_pod_info()
        
    def _get_node_info(self) -> dict:
        """获取节点信息"""
        try:
            # 获取节点名称
            node_name = os.environ.get('NODE_NAME', '')
            
            # 获取节点IP
            node_ip = os.environ.get('NODE_IP', '')
            
            # 获取集群信息
            cluster_name = os.environ.get('CLUSTER_NAME', '')
            
            return {
                'node_name': node_name,
                'node_ip': node_ip,
                'cluster_name': cluster_name
            }
        except:
            return {}
            
    def _get_pod_info(self) -> dict:
        """获取Pod信息"""
        try:
            # 获取Pod名称
            pod_name = os.environ.get('POD_NAME', '')
            
            # 获取命名空间
            namespace = os.environ.get('POD_NAMESPACE', '')
            
            # 获取Pod IP
            pod_ip = os.environ.get('POD_IP', '')
            
            return {
                'pod_name': pod_name,
                'namespace': namespace,
                'pod_ip': pod_ip
            }
        except:
            return {}
            
    def get_environment_info(self) -> dict:
        """获取环境信息"""
        return {
            'node_info': self.node_info,
            'pod_info': self.pod_info,
            'timestamp': time.time()
        } 