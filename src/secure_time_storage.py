import os
import time
import tempfile
from typing import Optional
from cryptography.fernet import Fernet
from pathlib import Path

class SecureTimeStorage:
    def __init__(self, secret_key: bytes):
        """初始化安全时间戳存储
        
        Args:
            secret_key: 用于加密的密钥
        """
        self.secret_key = secret_key
        self.fernet = Fernet(secret_key)
        self.storage_dir = Path("secure_storage")
        self._initialize_storage()
        
    def _initialize_storage(self):
        """初始化存储"""
        # 创建存储目录
        os.makedirs(self.storage_dir, exist_ok=True)
        # 创建多个时间戳文件
        self._create_encrypted_files()
        
    def _create_encrypted_files(self):
        """创建加密的时间戳文件"""
        timestamp = time.time()
        # 在多个位置创建加密的时间戳
        locations = [
            self.storage_dir / "timestamp_1.dat",
            self.storage_dir / "timestamp_2.dat",
            self.storage_dir / "timestamp_3.dat"
        ]
        
        for location in locations:
            # 加密时间戳
            encrypted_time = self.fernet.encrypt(str(timestamp).encode())
            # 写入文件
            with open(location, "wb") as f:
                f.write(encrypted_time)
            # 设置文件权限
            os.chmod(location, 0o600)
                
    def validate_storage(self) -> bool:
        """验证存储的时间戳
        
        Returns:
            bool: 时间戳是否有效
        """
        try:
            timestamps = []
            # 读取所有时间戳文件
            for file in self.storage_dir.glob("timestamp_*.dat"):
                with open(file, "rb") as f:
                    encrypted_data = f.read()
                # 解密时间戳
                decrypted_data = self.fernet.decrypt(encrypted_data)
                timestamp = float(decrypted_data.decode())
                timestamps.append(timestamp)
            
            # 检查是否至少有两个有效的时间戳
            if len(timestamps) < 2:
                return False
                
            # 检查时间戳是否一致
            first_timestamp = timestamps[0]
            for timestamp in timestamps[1:]:
                if abs(timestamp - first_timestamp) > 1.0:  # 允许1秒的误差
                    return False
                    
            return True
            
        except Exception as e:
            print(f"时间戳验证失败: {e}")
            return False
        
    def update_timestamps(self):
        """更新所有时间戳"""
        self._create_encrypted_files() 