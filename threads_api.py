import requests
import json
from typing import Optional, Dict, Any
import base64
import os
import tempfile
import shutil
from pathlib import Path
import datetime
import time

class ThreadsTokenManagerNode:
    """
    Threads 權杖管理節點 - 處理短期權杖轉換為長期權杖和重新整理
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "action": (["exchange_token", "refresh_token", "validate_token"], {
                    "default": "exchange_token"
                }),
                "access_token": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            },
            "optional": {
                "client_secret": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "auto_refresh_threshold_days": ("INT", {
                    "default": 7,
                    "min": 1,
                    "max": 30
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "BOOLEAN", "STRING", "INT", "STRING")
    RETURN_NAMES = ("new_access_token", "success", "status_message", "expires_in_days", "token_type")
    CATEGORY = "Social Media/Threads/Token"
    FUNCTION = "manage_token"
    
    def __init__(self):
        self.base_url = "https://graph.threads.net"
    
    def exchange_to_long_lived_token(self, short_lived_token: str, client_secret: str) -> tuple:
        """
        將短期權杖換成長期權杖
        """
        try:
            if not short_lived_token or not client_secret:
                return ("", False, "❌ 需要提供短期權杖和應用程式密鑰", 0, "")
            
            print("=== 將短期權杖換成長期權杖 ===")
            
            url = f"{self.base_url}/access_token"
            params = {
                'grant_type': 'th_exchange_token',
                'client_secret': client_secret,
                'access_token': short_lived_token
            }
            
            print(f"請求 URL: {url}")
            print(f"參數: {dict(params, client_secret='[HIDDEN]')}")  # 隱藏密鑰
            
            response = requests.get(url, params=params, timeout=30)
            
            print(f"響應狀態: {response.status_code}")
            print(f"響應內容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                
                new_token = result.get('access_token', '')
                token_type = result.get('token_type', 'bearer')
                expires_in_seconds = result.get('expires_in', 0)
                expires_in_days = expires_in_seconds // (24 * 3600)
                
                success_message = f"✅ 成功獲得長期權杖!\n" \
                                f"權杖類型: {token_type}\n" \
                                f"有效期: {expires_in_days} 天 ({expires_in_seconds} 秒)\n" \
                                f"到期日期: {(datetime.datetime.now() + datetime.timedelta(seconds=expires_in_seconds)).strftime('%Y-%m-%d %H:%M:%S')}"
                
                print(success_message)
                return (new_token, True, success_message, expires_in_days, token_type)
                
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('error', {})
                    error_message = error_detail.get('message', response.text)
                    error_code = error_detail.get('code', response.status_code)
                    
                    if error_code == 190:
                        error_msg = f"❌ 權杖轉換失敗: 短期權杖無效或已過期\n詳細信息: {error_message}"
                    elif error_code == 100:
                        error_msg = f"❌ 權杖轉換失敗: 參數錯誤或應用程式密鑰無效\n詳細信息: {error_message}"
                    else:
                        error_msg = f"❌ 權杖轉換失敗: {error_message}"
                        
                except:
                    error_msg = f"❌ 權杖轉換失敗: {response.status_code} - {response.text}"
                
                print(error_msg)
                return ("", False, error_msg, 0, "")
                
        except Exception as e:
            error_message = f"❌ 權杖轉換異常: {str(e)}"
            print(error_message)
            import traceback
            traceback.print_exc()
            return ("", False, error_message, 0, "")
    
    def refresh_long_lived_token(self, long_lived_token: str) -> tuple:
        """
        重新整理長期權杖
        """
        try:
            if not long_lived_token:
                return ("", False, "❌ 需要提供長期權杖", 0, "")
            
            print("=== 重新整理長期權杖 ===")
            
            url = f"{self.base_url}/refresh_access_token"
            params = {
                'grant_type': 'th_refresh_token',
                'access_token': long_lived_token
            }
            
            print(f"請求 URL: {url}")
            print(f"參數: {params}")
            
            response = requests.get(url, params=params, timeout=30)
            
            print(f"響應狀態: {response.status_code}")
            print(f"響應內容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                
                new_token = result.get('access_token', '')
                token_type = result.get('token_type', 'bearer')
                expires_in_seconds = result.get('expires_in', 0)
                expires_in_days = expires_in_seconds // (24 * 3600)
                
                success_message = f"✅ 長期權杖重新整理成功!\n" \
                                f"權杖類型: {token_type}\n" \
                                f"新的有效期: {expires_in_days} 天 ({expires_in_seconds} 秒)\n" \
                                f"新的到期日期: {(datetime.datetime.now() + datetime.timedelta(seconds=expires_in_seconds)).strftime('%Y-%m-%d %H:%M:%S')}"
                
                print(success_message)
                return (new_token, True, success_message, expires_in_days, token_type)
                
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('error', {})
                    error_message = error_detail.get('message', response.text)
                    error_code = error_detail.get('code', response.status_code)
                    
                    if error_code == 190:
                        error_msg = f"❌ 權杖重新整理失敗: 長期權杖無效或已過期\n詳細信息: {error_message}\n💡 建議: 需要重新獲取短期權杖並轉換為長期權杖"
                    else:
                        error_msg = f"❌ 權杖重新整理失敗: {error_message}"
                        
                except:
                    error_msg = f"❌ 權杖重新整理失敗: {response.status_code} - {response.text}"
                
                print(error_msg)
                return ("", False, error_msg, 0, "")
                
        except Exception as e:
            error_message = f"❌ 權杖重新整理異常: {str(e)}"
            print(error_message)
            import traceback
            traceback.print_exc()
            return ("", False, error_message, 0, "")
    
    def validate_token_expiry(self, access_token: str, threshold_days: int = 7) -> tuple:
        """
        驗證權杖並檢查是否需要重新整理
        """
        try:
            if not access_token:
                return ("", False, "❌ 需要提供存取權杖", 0, "")
            
            print("=== 驗證權杖到期狀態 ===")
            
            # 嘗試使用權杖獲取用戶資訊來驗證有效性
            api_version = "v1.0"
            test_url = f"https://graph.threads.net/{api_version}/me"
            test_params = {
                'fields': 'id,username',
                'access_token': access_token
            }
            
            response = requests.get(test_url, params=test_params, timeout=30)
            
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data.get('id', '')
                username = user_data.get('username', '')
                
                # 無法直接獲取權杖到期時間，只能確認權杖當前有效
                validation_message = f"✅ 權杖當前有效\n" \
                                   f"用戶ID: {user_id}\n" \
                                   f"用戶名: @{username}\n" \
                                   f"💡 建議: 如果此權杖使用超過 {threshold_days} 天，請考慮重新整理"
                
                print(validation_message)
                return (access_token, True, validation_message, -1, "valid")  # -1 表示無法確定剩餘天數
                
            elif response.status_code == 190:
                error_msg = "❌ 權杖已過期或無效\n💡 建議: 需要重新獲取短期權杖並轉換為長期權杖"
                print(error_msg)
                return ("", False, error_msg, 0, "expired")
                
            else:
                error_msg = f"❌ 權杖驗證失敗: {response.status_code} - {response.text}"
                print(error_msg)
                return ("", False, error_msg, 0, "unknown")
                
        except Exception as e:
            error_message = f"❌ 權杖驗證異常: {str(e)}"
            print(error_message)
            return ("", False, error_message, 0, "error")
    
    def manage_token(self, action: str, access_token: str, client_secret: str = "",
                    auto_refresh_threshold_days: int = 7):
        """
        主要的權杖管理函數
        """
        try:
            print(f"=== Threads 權杖管理: {action} ===")
            
            if action == "exchange_token":
                return self.exchange_to_long_lived_token(access_token, client_secret)
                
            elif action == "refresh_token":
                return self.refresh_long_lived_token(access_token)
                
            elif action == "validate_token":
                return self.validate_token_expiry(access_token, auto_refresh_threshold_days)
                
            else:
                return ("", False, f"❌ 不支援的操作: {action}", 0, "")
                
        except Exception as e:
            error_message = f"❌ 權杖管理異常: {str(e)}"
            print(error_message)
            return ("", False, error_message, 0, "")


class ThreadsTokenValidatorNode:
    """
    增強的 Threads Token 驗證節點 - 支援長期權杖檢查
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "access_token": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            },
            "optional": {
                "check_expiry_warning": ("BOOLEAN", {
                    "default": True
                }),
                "warning_days_threshold": ("INT", {
                    "default": 7,
                    "min": 1,
                    "max": 30
                }),
            }
        }
    
    RETURN_TYPES = ("BOOLEAN", "STRING", "STRING", "BOOLEAN")
    RETURN_NAMES = ("is_valid", "permissions", "validation_report", "needs_refresh")
    CATEGORY = "Social Media/Threads"
    FUNCTION = "validate_token"
    
    def __init__(self):
        self.api_version = "v1.0"
        self.base_url = f"https://graph.threads.net/{self.api_version}"
    
    def validate_token(self, access_token: str, check_expiry_warning: bool = True,
                      warning_days_threshold: int = 7):
        """
        驗證 Token 有效性和權限，並檢查是否需要重新整理
        """
        try:
            if not access_token or access_token.strip() == "":
                return (False, "", "❌ Access Token 為空", False)
            
            print("驗證 Threads Access Token...")
            
            validation_report = ["=== Threads Token 驗證報告 ==="]
            needs_refresh = False
            
            # 1. 基本格式檢查
            validation_report.append("\n1. Token 格式檢查:")
            if len(access_token) < 20:
                validation_report.append("   ⚠️ Token 長度過短")
            else:
                validation_report.append("   ✅ Token 長度正常")
            
            if ' ' in access_token:
                validation_report.append("   ❌ Token 包含空格")
                return (False, "", "\n".join(validation_report), False)
            else:
                validation_report.append("   ✅ Token 格式正常")
            
            # 2. API 連接測試
            validation_report.append("\n2. API 連接測試:")
            
            # 獲取用戶信息
            user_url = f"{self.base_url}/me"
            user_params = {
                'fields': 'id,username,name',
                'access_token': access_token
            }
            
            user_response = requests.get(user_url, params=user_params, timeout=30)
            
            validation_report.append(f"   狀態碼: {user_response.status_code}")
            
            if user_response.status_code == 200:
                validation_report.append("   ✅ Token 有效，可以訪問用戶信息")
                user_data = user_response.json()
                user_id = user_data.get('id', '')
                username = user_data.get('username', '')
                name = user_data.get('name', '')
                validation_report.append(f"   用戶ID: {user_id}")
                validation_report.append(f"   用戶名: @{username}")
                if name:
                    validation_report.append(f"   顯示名稱: {name}")
                    
            elif user_response.status_code == 190:
                validation_report.append("   ❌ Token 無效或已過期")
                validation_report.append("   💡 建議: 重新獲取短期權杖並轉換為長期權杖")
                return (False, "", "\n".join(validation_report), True)
            elif user_response.status_code == 403:
                validation_report.append("   ❌ Token 權限不足")
                return (False, "", "\n".join(validation_report), False)
            else:
                validation_report.append(f"   ❌ 連接失敗: {user_response.text}")
                return (False, "", "\n".join(validation_report), False)
            
            # 3. 權限檢查
            validation_report.append("\n3. 權限檢查:")
            
            permissions = "基礎權限確認"
            
            # 嘗試檢查權杖詳細資訊（可能不適用於所有情況）
            try:
                # 測試創建權限（不實際創建）
                test_create_url = f"{self.base_url}/{user_id}/threads"
                test_headers = {'Authorization': f'Bearer {access_token}'}
                
                # 使用 HEAD 請求測試權限
                test_response = requests.head(test_create_url, headers=test_headers, timeout=10)
                
                if test_response.status_code in [200, 405]:  # 405 表示方法不允許但端點存在
                    validation_report.append("   ✅ 具有基本發布權限")
                    permissions = "threads_basic,threads_content_publish"
                elif test_response.status_code == 403:
                    validation_report.append("   ⚠️ 可能缺少發布權限")
                    permissions = "threads_basic"
                else:
                    validation_report.append("   ⚠️ 權限檢查不確定")
                    permissions = "未知"
                    
            except:
                validation_report.append("   ⚠️ 權限檢查跳過")
                permissions = "基礎權限確認"
            
            # 4. 長期權杖到期檢查
            if check_expiry_warning:
                validation_report.append("\n4. 長期權杖到期檢查:")
                validation_report.append("   ℹ️ 無法直接檢查權杖到期時間")
                validation_report.append(f"   💡 建議: 如果此權杖使用超過 {60 - warning_days_threshold} 天，請考慮重新整理")
                validation_report.append("   📅 長期權杖有效期為 60 天")
                validation_report.append("   🔄 可在到期前使用重新整理功能延長有效期")
                
                # 根據閾值設定是否需要重新整理的建議
                if warning_days_threshold <= 7:
                    needs_refresh = False  # 保守建議
                    validation_report.append("   ✅ 當前不需要立即重新整理")
                else:
                    needs_refresh = False  # 無法確定確切時間，保持謹慎
                    validation_report.append("   ⚠️ 建議定期檢查和重新整理權杖")
            
            validation_report.append("\n=== 驗證完成 ===")
            validation_report.append("✅ Token 可用於 Threads API")
            validation_report.append("\n💡 長期權杖管理建議:")
            validation_report.append("   1. 定期使用 ThreadsTokenManagerNode 重新整理權杖")
            validation_report.append("   2. 在應用程式中實現自動權杖重新整理機制")
            validation_report.append("   3. 安全存儲應用程式密鑰，僅在伺服器端使用")
            
            return (True, permissions, "\n".join(validation_report), needs_refresh)
            
        except Exception as e:
            error_message = f"❌ 驗證過程發生異常: {str(e)}"
            print(error_message)
            return (False, "", error_message, False)


# 修改原有的節點以支援長期權杖
class ThreadsOfficialFormatNode:
    """
    严格按照官方 curl 示例格式的 Threads 節點 - 增強長期權杖支援
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "access_token": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "text": ("STRING", {
                    "multiline": True,
                    "default": "Hello from ComfyUI! 🚀"
                }),
                "threads_user_id": ("STRING", {
                    "default": "me",
                    "multiline": False
                }),
            },
            "optional": {
                "media_type": (["TEXT", "IMAGE", "VIDEO"], {
                    "default": "TEXT"
                }),
                "image_url": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "video_url": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "auto_refresh_token": ("BOOLEAN", {
                    "default": False
                }),
                "client_secret": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "BOOLEAN", "STRING", "STRING")
    RETURN_NAMES = ("post_id", "permalink", "success", "status_message", "refreshed_token")
    CATEGORY = "Social Media/Threads"
    FUNCTION = "publish_official_format"
    
    def __init__(self):
        self.api_version = "v1.0"
        self.base_url = f"https://graph.threads.net/{self.api_version}"
        self.token_manager = ThreadsTokenManagerNode()
    
    def handle_token_expiry(self, access_token: str, client_secret: str, auto_refresh: bool) -> tuple:
        """
        處理權杖過期情況
        """
        try:
            if not auto_refresh or not client_secret:
                return (access_token, False, "權杖可能已過期，請手動重新整理或提供 client_secret 以自動重新整理")
            
            print("嘗試自動重新整理權杖...")
            
            # 嘗試重新整理權杖
            new_token, refresh_success, refresh_message, expires_days, token_type = self.token_manager.refresh_long_lived_token(access_token)
            
            if refresh_success:
                print(f"✅ 權杖重新整理成功: {expires_days} 天有效期")
                return (new_token, True, f"權杖已自動重新整理，新的有效期: {expires_days} 天")
            else:
                print(f"❌ 權杖重新整理失敗: {refresh_message}")
                return (access_token, False, f"權杖重新整理失敗: {refresh_message}")
                
        except Exception as e:
            return (access_token, False, f"權杖處理異常: {str(e)}")
    
    def create_text_post_container(self, threads_user_id: str, access_token: str, text: str,
                                  auto_refresh: bool = False, client_secret: str = "") -> tuple:
        """
        創建純文本帖子容器 - 增強權杖處理
        """
        try:
            url = f"{self.base_url}/{threads_user_id}/threads"
            
            if not text.strip():
                return (None, access_token, "❌ 純文本帖子需要 text 參數")
            
            params = {
                'media_type': 'TEXT',
                'text': text,
                'access_token': access_token
            }
            
            print(f"創建純文本帖子容器...")
            print(f"URL: {url}")
            print(f"參數: {params}")
            
            response = requests.post(url, params=params, timeout=30)
            
            print(f"文本帖子響應狀態: {response.status_code}")
            print(f"文本帖子響應內容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                creation_id = result.get('id')
                print(f"✅ 文本帖子容器創建成功，ID: {creation_id}")
                return (creation_id, access_token, "容器創建成功")
                
            elif response.status_code == 190:  # 權杖過期
                print("⚠️ 權杖可能已過期，嘗試處理...")
                new_token, refresh_success, refresh_message = self.handle_token_expiry(
                    access_token, client_secret, auto_refresh
                )
                
                if refresh_success:
                    # 使用新權杖重試
                    params['access_token'] = new_token
                    retry_response = requests.post(url, params=params, timeout=30)
                    
                    if retry_response.status_code == 200:
                        result = retry_response.json()
                        creation_id = result.get('id')
                        print(f"✅ 使用新權杖創建成功，ID: {creation_id}")
                        return (creation_id, new_token, f"權杖已重新整理並創建成功: {refresh_message}")
                    else:
                        return (None, new_token, f"使用新權杖創建失敗: {retry_response.text}")
                else:
                    return (None, access_token, refresh_message)
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('error', {})
                    error_msg = f"容器創建失敗: {error_detail.get('message', response.text)}"
                except:
                    error_msg = f"容器創建失敗: {response.text}"
                
                return (None, access_token, error_msg)
                
        except Exception as e:
            error_msg = f"創建文本帖子容器異常: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return (None, access_token, error_msg)
    
    def publish_threads_container(self, creation_id: str, access_token: str,
                                 auto_refresh: bool = False, client_secret: str = "") -> tuple:
        """
        發布 Threads 容器 - 增強權杖處理
        """
        try:
            url = f"{self.base_url}/me/threads_publish"
            
            data = {
                'creation_id': creation_id,
                'access_token': access_token
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            print(f"發布 Threads 容器...")
            print(f"URL: {url}")
            print(f"POST 數據: {data}")
            
            response = requests.post(url, data=data, headers=headers, timeout=30)
            
            print(f"發布響應狀態: {response.status_code}")
            print(f"發布響應內容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 發布成功: {result}")
                return (result, access_token, "發布成功")
                
            elif response.status_code == 190:  # 權杖過期
                print("⚠️ 權杖可能已過期，嘗試處理...")
                new_token, refresh_success, refresh_message = self.handle_token_expiry(
                    access_token, client_secret, auto_refresh
                )
                
                if refresh_success:
                    # 使用新權杖重試
                    data['access_token'] = new_token
                    retry_response = requests.post(url, data=data, headers=headers, timeout=30)
                    
                    if retry_response.status_code == 200:
                        result = retry_response.json()
                        print(f"✅ 使用新權杖發布成功: {result}")
                        return (result, new_token, f"權杖已重新整理並發布成功: {refresh_message}")
                    else:
                        return (None, new_token, f"使用新權杖發布失敗: {retry_response.text}")
                else:
                    return (None, access_token, refresh_message)
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('error', {})
                    error_msg = f"發布失敗: {error_detail.get('message', response.text)}"
                except:
                    error_msg = f"發布失敗: {response.text}"
                
                return (None, access_token, error_msg)
                
        except Exception as e:
            error_msg = f"發布時發生異常: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return (None, access_token, error_msg)
    
    def publish_official_format(self, access_token: str, text: str, threads_user_id: str,
                               media_type: str = "TEXT", image_url: str = "", video_url: str = "",
                               auto_refresh_token: bool = False, client_secret: str = ""):
        """
        主發布函數 - 增強長期權杖支援
        """
        try:
            print("=== Threads 官方格式發布開始（支援長期權杖）===")
            print(f"用戶ID: {threads_user_id}")
            print(f"媒體類型: {media_type}")
            print(f"文本內容: {text[:50]}...")
            print(f"自動重新整理權杖: {auto_refresh_token}")
            
            current_token = access_token
            
            # 目前僅支援文本帖子的增強權杖處理，其他類型可以類似擴展
            if media_type == 'TEXT':
                if not text.strip():
                    return ("", "", False, "❌ 純文本帖子必須提供 text 參數", current_token)
                
                # 創建容器
                creation_id, updated_token, create_message = self.create_text_post_container(
                    threads_user_id, current_token, text, auto_refresh_token, client_secret)
               
                current_token = updated_token
               
                if not creation_id:
                   return ("", "", False, create_message, current_token)
               
               # 發布容器
                publish_result, final_token, publish_message = self.publish_threads_container(
                   creation_id, current_token, auto_refresh_token, client_secret
                )
               
                if not publish_result:
                   return ("", "", False, publish_message, final_token)
               
               # 獲取結果
                post_id = publish_result.get('id', '')
                permalink = f"https://threads.net/post/{post_id}"
               
                success_message = f"✅ 成功發布到 Threads!\n帖子 ID: {post_id}\n媒體類型: {media_type}"
                if final_token != access_token:
                   success_message += "\n🔄 權杖已自動重新整理"
               
                print("=== 發布完成 ===")
                return (post_id, permalink, True, success_message, final_token)
           
            else:
               # 對於圖片和視頻，暫時使用原有邏輯，但可以擴展
               return ("", "", False, "❌ 圖片和視頻發布的權杖自動重新整理功能尚未實現", current_token)
           
        except Exception as e:
            error_message = f"❌ 發布過程發生異常: {str(e)}"
            print(error_message)
            import traceback
            traceback.print_exc()
            return ("", "", False, error_message, access_token)


class ThreadsMediaUploaderNode:
   """
   媒體上傳器節點 - 提供多種方式處理本地媒體文件
   """
   
   @classmethod
   def INPUT_TYPES(cls):
       return {
           "required": {
               "upload_service": (["imgur", "temp_host", "base64_embed", "local_server"], {
                   "default": "imgur"
               }),
               "media_file_path": ("STRING", {
                   "default": "",
                   "multiline": False
               }),
               "media_type": (["IMAGE", "VIDEO"], {
                   "default": "IMAGE"
               }),
           },
           "optional": {
               "imgur_client_id": ("STRING", {
                   "default": "",
                   "multiline": False
               }),
               "custom_server_url": ("STRING", {
                   "default": "http://localhost:8000",
                   "multiline": False
               }),
               "temp_host_service": (["imgbb", "postimages", "imgur_anonymous"], {
                   "default": "imgur_anonymous"
               }),
           }
       }
   
   RETURN_TYPES = ("STRING", "BOOLEAN", "STRING", "STRING")
   RETURN_NAMES = ("media_url", "success", "upload_method", "status_message")
   CATEGORY = "Social Media/Threads/Media"
   FUNCTION = "upload_media"
   
   def upload_to_imgur(self, file_path: str, client_id: str = None) -> tuple:
       """
       上傳到 Imgur
       """
       try:
           if not os.path.exists(file_path):
               return ("", False, "File not found")
           
           with open(file_path, 'rb') as f:
               image_data = f.read()
           
           # 使用匿名上傳或授權上傳
           if client_id:
               headers = {'Authorization': f'Client-ID {client_id}'}
               upload_method = "Imgur (Authorized)"
           else:
               # 匿名上傳 - 使用公共客戶端ID
               headers = {'Authorization': 'Client-ID 546c25a59c58ad7'}
               upload_method = "Imgur (Anonymous)"
           
           data = {
               'image': base64.b64encode(image_data),
               'type': 'base64'
           }
           
           response = requests.post(
               'https://api.imgur.com/3/image',
               headers=headers,
               data=data,
               timeout=30
           )
           
           if response.status_code == 200:
               result = response.json()
               if result['success']:
                   image_url = result['data']['link']
                   return (image_url, True, upload_method)
               else:
                   return ("", False, f"Imgur API error: {result}")
           else:
               return ("", False, f"Upload failed: {response.status_code}")
               
       except Exception as e:
           return ("", False, f"Upload error: {str(e)}")
   
   def upload_to_imgbb(self, file_path: str, api_key: str = None) -> tuple:
       """
       上傳到 ImgBB (需要API密鑰)
       """
       try:
           if not api_key:
               return ("", False, "ImgBB requires API key")
           
           if not os.path.exists(file_path):
               return ("", False, "File not found")
           
           with open(file_path, 'rb') as f:
               image_data = f.read()
           
           data = {
               'key': api_key,
               'image': base64.b64encode(image_data)
           }
           
           response = requests.post(
               'https://api.imgbb.com/1/upload',
               data=data,
               timeout=30
           )
           
           if response.status_code == 200:
               result = response.json()
               if result['success']:
                   image_url = result['data']['url']
                   return (image_url, True, "ImgBB")
               else:
                   return ("", False, f"ImgBB error: {result}")
           else:
               return ("", False, f"Upload failed: {response.status_code}")
               
       except Exception as e:
           return ("", False, f"Upload error: {str(e)}")
   
   def create_temp_server(self, file_path: str, port: int = 8000) -> tuple:
       """
       創建臨時本地服務器
       """
       try:
           import http.server
           import socketserver
           import threading
           import time
           
           if not os.path.exists(file_path):
               return ("", False, "File not found")
           
           # 創建臨時目錄
           temp_dir = tempfile.mkdtemp()
           file_name = os.path.basename(file_path)
           temp_file_path = os.path.join(temp_dir, file_name)
           
           # 複製文件到臨時目錄
           shutil.copy2(file_path, temp_file_path)
           
           # 啟動簡單HTTP服務器
           handler = http.server.SimpleHTTPRequestHandler
           
           def start_server():
               os.chdir(temp_dir)
               with socketserver.TCPServer(("", port), handler) as httpd:
                   httpd.timeout = 300  # 5分鐘超時
                   httpd.serve_forever()
           
           # 在後台線程啟動服務器
           server_thread = threading.Thread(target=start_server, daemon=True)
           server_thread.start()
           
           # 等待服務器啟動
           time.sleep(2)
           
           # 獲取本地IP
           import socket
           hostname = socket.gethostname()
           local_ip = socket.gethostbyname(hostname)
           
           media_url = f"http://{local_ip}:{port}/{file_name}"
           
           return (media_url, True, f"Local Server (Port {port})")
           
       except Exception as e:
           return ("", False, f"Server error: {str(e)}")
   
   def create_data_url(self, file_path: str) -> tuple:
       """
       創建 Data URL (Base64 編碼) - 僅用於小文件
       """
       try:
           if not os.path.exists(file_path):
               return ("", False, "File not found")
           
           # 檢查文件大小 (限制為2MB)
           file_size = os.path.getsize(file_path)
           if file_size > 2 * 1024 * 1024:
               return ("", False, "File too large for Base64 encoding (>2MB)")
           
           with open(file_path, 'rb') as f:
               file_data = f.read()
           
           # 確定MIME類型
           file_ext = Path(file_path).suffix.lower()
           mime_types = {
               '.jpg': 'image/jpeg',
               '.jpeg': 'image/jpeg',
               '.png': 'image/png',
               '.gif': 'image/gif',
               '.webp': 'image/webp',
               '.mp4': 'video/mp4',
               '.mov': 'video/quicktime',
               '.avi': 'video/x-msvideo'
           }
           
           mime_type = mime_types.get(file_ext, 'application/octet-stream')
           
           # 創建 Data URL
           base64_data = base64.b64encode(file_data).decode('utf-8')
           data_url = f"data:{mime_type};base64,{base64_data}"
           
           return (data_url, True, "Base64 Data URL")
           
       except Exception as e:
           return ("", False, f"Base64 error: {str(e)}")
   
   def upload_media(self, upload_service: str, media_file_path: str, media_type: str,
                   imgur_client_id: str = "", custom_server_url: str = "",
                   temp_host_service: str = "imgur_anonymous"):
       """
       主要的媒體上傳函數
       """
       try:
           print(f"=== 媒體上傳開始 ===")
           print(f"服務: {upload_service}")
           print(f"文件: {media_file_path}")
           print(f"類型: {media_type}")
           
           if not media_file_path or not os.path.exists(media_file_path):
               return ("", False, upload_service, "❌ 文件路徑無效或文件不存在")
           
           # 根據選擇的服務進行上傳
           if upload_service == "imgur":
               media_url, success, method = self.upload_to_imgur(
                   media_file_path, imgur_client_id
               )
               
           elif upload_service == "temp_host":
               if temp_host_service == "imgur_anonymous":
                   media_url, success, method = self.upload_to_imgur(media_file_path)
               elif temp_host_service == "imgbb":
                   media_url, success, method = self.upload_to_imgbb(
                       media_file_path, imgur_client_id  # 重用字段作為API密鑰
                   )
               else:
                   media_url, success, method = self.upload_to_imgur(media_file_path)
                   
           elif upload_service == "base64_embed":
               media_url, success, method = self.create_data_url(media_file_path)
               
           elif upload_service == "local_server":
               # 解析端口號
               try:
                   if ":" in custom_server_url:
                       port = int(custom_server_url.split(":")[-1])
                   else:
                       port = 8000
               except:
                   port = 8000
                   
               media_url, success, method = self.create_temp_server(
                   media_file_path, port
               )
           
           else:
               return ("", False, upload_service, "❌ 不支援的上傳服務")
           
           if success:
               status_message = f"✅ 媒體上傳成功!\n方法: {method}\nURL: {media_url[:100]}..."
               print(status_message)
               return (media_url, True, method, status_message)
           else:
               status_message = f"❌ 媒體上傳失敗: {method}"
               print(status_message)
               return ("", False, method, status_message)
               
       except Exception as e:
           error_message = f"❌ 上傳過程異常: {str(e)}"
           print(error_message)
           return ("", False, upload_service, error_message)


class ThreadsAllInOneNode:
    """
    Threads 一體化發布節點 - 集成所有功能並支援長期權杖，增強視頻發布支援
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "access_token": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "text": ("STRING", {
                    "multiline": True,
                    "default": "Hello from ComfyUI! 🚀"
                }),
                "threads_user_id": ("STRING", {
                    "default": "me",
                    "multiline": False
                }),
                "post_type": (["TEXT_ONLY", "IMAGE_POST", "VIDEO_POST"], {
                    "default": "TEXT_ONLY"
                }),
            },
            "optional": {
                # 媒體文件選項
                "media_file_path": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "media_url": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                
                # 自動上傳選項
                "auto_upload": ("BOOLEAN", {
                    "default": True
                }),
                "upload_service": (["imgur", "cloudinary", "s3", "temp_server"], {
                    "default": "imgur"
                }),
                
                # 長期權杖管理
                "auto_refresh_token": ("BOOLEAN", {
                    "default": True
                }),
                "client_secret": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                
                # Imgur 配置
                "imgur_client_id": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                
                # 媒體處理選項
                "auto_optimize": ("BOOLEAN", {
                    "default": True
                }),
                "max_file_size_mb": ("FLOAT", {
                    "default": 10.0,
                    "min": 0.1,
                    "max": 100.0
                }),
                
                # 視頻發布特定選項
                "video_check_timeout": ("INT", {
                    "default": 60,
                    "min": 10,
                    "max": 300
                }),
                "video_check_interval": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 30
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "BOOLEAN", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("post_id", "permalink", "success", "status_message", "media_url_used", "processing_log", "final_token")
    CATEGORY = "Social Media/Threads"
    FUNCTION = "publish_all_in_one"
    
    def __init__(self):
        self.api_version = "v1.0"
        self.base_url = f"https://graph.threads.net/{self.api_version}"
        self.media_uploader = ThreadsMediaUploaderNode()
        self.token_manager = ThreadsTokenManagerNode()
    
    def handle_api_error_with_token_refresh(self, response, current_token: str, client_secret: str, 
                                          auto_refresh: bool) -> tuple:
        """
        處理API錯誤並嘗試權杖重新整理
        """
        if response.status_code == 190 and auto_refresh and client_secret:
            print("🔄 檢測到權杖過期，嘗試自動重新整理...")
            
            new_token, refresh_success, refresh_message, expires_days, token_type = self.token_manager.refresh_long_lived_token(current_token)
            
            if refresh_success:
                print(f"✅ 權杖重新整理成功，新的有效期: {expires_days} 天")
                return (new_token, True, f"權杖已自動重新整理: {expires_days} 天有效期")
            else:
                print(f"❌ 權杖重新整理失敗: {refresh_message}")
                return (current_token, False, f"權杖重新整理失敗: {refresh_message}")
        else:
            return (current_token, False, f"API 錯誤: {response.status_code} - {response.text}")
    
    def check_container_status(self, container_id: str, access_token: str) -> tuple:
        """
        檢查媒體容器狀態
        """
        try:
            url = f"{self.base_url}/{container_id}"
            params = {
                'fields': 'status,error_message',
                'access_token': access_token
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'UNKNOWN')
                error_message = result.get('error_message', '')
                
                return (True, status, error_message)
            else:
                return (False, 'ERROR', f"狀態檢查失敗: {response.status_code} - {response.text}")
                
        except Exception as e:
            return (False, 'ERROR', f"狀態檢查異常: {str(e)}")
    
    def wait_for_container_ready(self, container_id: str, access_token: str, 
                                timeout: int = 60, check_interval: int = 5) -> tuple:
        """
        等待容器準備完成（主要用於視頻）
        """
        import time
        
        start_time = time.time()
        processing_log = []
        
        processing_log.append(f"⏳ 等待容器準備完成（最多 {timeout} 秒）...")
        
        while time.time() - start_time < timeout:
            success, status, error_message = self.check_container_status(container_id, access_token)
            
            if not success:
                processing_log.append(f"❌ 狀態檢查失敗: {error_message}")
                return (False, processing_log, error_message)
            
            processing_log.append(f"📊 容器狀態: {status}")
            
            if status == 'FINISHED':
                processing_log.append("✅ 容器準備完成！")
                return (True, processing_log, "容器準備完成")
            elif status == 'ERROR':
                error_msg = f"❌ 容器處理錯誤: {error_message}"
                processing_log.append(error_msg)
                return (False, processing_log, error_msg)
            elif status in ['IN_PROGRESS', 'PROCESSING']:
                processing_log.append(f"⏳ 容器正在處理中，{check_interval} 秒後重新檢查...")
                time.sleep(check_interval)
            else:
                processing_log.append(f"⚠️ 未知狀態: {status}，繼續等待...")
                time.sleep(check_interval)
        
        timeout_msg = f"⏰ 等待超時（{timeout} 秒），容器可能仍在處理中"
        processing_log.append(timeout_msg)
        return (False, processing_log, timeout_msg)
    
    def create_video_container_with_retry(self, threads_user_id: str, access_token: str,
                                        text: str, video_url: str,
                                        auto_refresh: bool = True, client_secret: str = "",
                                        video_check_timeout: int = 60, video_check_interval: int = 5) -> tuple:
        """
        創建視頻容器並等待準備完成 - 支援重試
        """
        try:
            processing_log = []
            processing_log.append("🎬 開始創建視頻容器...")
            
            url = f"{self.base_url}/{threads_user_id}/threads"
            current_token = access_token
            
            params = {
                'media_type': 'VIDEO',
                'video_url': video_url,
                'access_token': current_token
            }
            
            # 添加文本（如果提供）
            if text.strip():
                params['text'] = text
            
            processing_log.append(f"📝 請求參數: {dict(params, access_token='[HIDDEN]')}")
            
            # Step 1: 創建視頻容器
            response = requests.post(url, params=params, timeout=60)
            processing_log.append(f"📊 創建響應狀態: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                container_id = result.get('id')
                processing_log.append(f"✅ 視頻容器創建成功: {container_id}")
                
                # Step 1.5: 等待視頻處理完成
                processing_log.append("⏳ 等待視頻處理完成...")
                ready_success, wait_log, wait_message = self.wait_for_container_ready(
                    container_id, current_token, video_check_timeout, video_check_interval
                )
                
                processing_log.extend(wait_log)
                
                if ready_success:
                    processing_log.append("✅ 視頻容器準備完成，可以發布")
                    return (container_id, current_token, "視頻容器創建並準備完成", processing_log)
                else:
                    # 即使等待超時，也嘗試發布（有些視頻可能不需要處理時間）
                    processing_log.append("⚠️ 等待超時，但仍嘗試發布...")
                    return (container_id, current_token, f"視頻容器創建完成但等待超時: {wait_message}", processing_log)
                
            elif response.status_code == 190:  # 權杖過期
                processing_log.append("🔄 權杖可能已過期，嘗試處理...")
                new_token, refresh_success, refresh_message = self.handle_api_error_with_token_refresh(
                    response, current_token, client_secret, auto_refresh
                )
                
                if refresh_success:
                    processing_log.append("✅ 權杖重新整理成功，重試創建容器...")
                    # 使用新權杖重試
                    params['access_token'] = new_token
                    retry_response = requests.post(url, params=params, timeout=60)
                    
                    if retry_response.status_code == 200:
                        result = retry_response.json()
                        container_id = result.get('id')
                        processing_log.append(f"✅ 使用新權杖創建視頻容器成功: {container_id}")
                        
                        # 等待視頻處理完成
                        ready_success, wait_log, wait_message = self.wait_for_container_ready(
                            container_id, new_token, video_check_timeout, video_check_interval
                        )
                        
                        processing_log.extend(wait_log)
                        
                        return (container_id, new_token, f"權杖已重新整理，視頻容器創建完成", processing_log)
                    else:
                        processing_log.append(f"❌ 使用新權杖重試失敗: {retry_response.text}")
                        return (None, new_token, f"使用新權杖重試失敗: {retry_response.text}", processing_log)
                else:
                    processing_log.append(f"❌ 權杖重新整理失敗: {refresh_message}")
                    return (None, current_token, refresh_message, processing_log)
            else:
                error_msg = f"視頻容器創建失敗: {response.status_code} - {response.text}"
                processing_log.append(f"❌ {error_msg}")
                return (None, current_token, error_msg, processing_log)
                
        except Exception as e:
            error_msg = f"創建視頻容器異常: {str(e)}"
            processing_log.append(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return (None, current_token, error_msg, processing_log)
    
    def create_threads_container_with_retry(self, threads_user_id: str, access_token: str,
                                          media_type: str, text: str, media_url: str = "",
                                          auto_refresh: bool = True, client_secret: str = "",
                                          video_check_timeout: int = 60, video_check_interval: int = 5) -> tuple:
        """
        創建 Threads 容器並支援重試 - 增強視頻支援
        """
        try:
            processing_log = []
            current_token = access_token
            
            # 特殊處理視頻類型
            if media_type == 'VIDEO':
                processing_log.append("🎬 檢測到視頻發布，使用增強的視頻處理流程...")
                container_id, updated_token, create_message, video_log = self.create_video_container_with_retry(
                    threads_user_id, current_token, text, media_url, auto_refresh, client_secret,
                    video_check_timeout, video_check_interval
                )
                processing_log.extend(video_log)
                
                if container_id:
                    return (container_id, updated_token, create_message, processing_log)
                else:
                    return (None, updated_token, create_message, processing_log)
            
            # 原有的文本和圖片處理邏輯
            url = f"{self.base_url}/{threads_user_id}/threads"
            
            params = {
                'media_type': media_type,
                'access_token': current_token
            }
            
            if media_type == 'TEXT':
                if not text.strip():
                    processing_log.append("❌ 純文本帖子需要 text 參數")
                    return (None, current_token, "❌ 純文本帖子需要 text 參數", processing_log)
                params['text'] = text
                
            elif media_type == 'IMAGE':
                if not media_url:
                    processing_log.append("❌ 圖片帖子需要 image_url 參數")
                    return (None, current_token, "❌ 圖片帖子需要 image_url 參數", processing_log)
                params['image_url'] = media_url
                params['is_carousel_item'] = False
                if text.strip():
                    params['text'] = text
            
            processing_log.append(f"創建容器 URL: {url}")
            processing_log.append(f"創建容器參數: {dict(params, access_token='[HIDDEN]')}")
            
            response = requests.post(url, params=params, timeout=60)
            processing_log.append(f"容器創建響應: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                creation_id = result.get('id')
                processing_log.append(f"✅ 容器創建成功: {creation_id}")
                return (creation_id, current_token, "容器創建成功", processing_log)
                
            elif response.status_code == 190:  # 權杖過期
                new_token, refresh_success, refresh_message = self.handle_api_error_with_token_refresh(
                    response, current_token, client_secret, auto_refresh
                )
                
                if refresh_success:
                    processing_log.append("✅ 權杖重新整理成功，重試創建容器...")
                    # 使用新權杖重試
                    params['access_token'] = new_token
                    retry_response = requests.post(url, params=params, timeout=60)
                    
                    if retry_response.status_code == 200:
                        result = retry_response.json()
                        creation_id = result.get('id')
                        processing_log.append(f"✅ 使用新權杖創建成功: {creation_id}")
                        return (creation_id, new_token, f"權杖已重新整理，容器創建成功", processing_log)
                    else:
                        processing_log.append(f"❌ 使用新權杖重試失敗: {retry_response.text}")
                        return (None, new_token, f"使用新權杖重試失敗: {retry_response.text}", processing_log)
                else:
                    processing_log.append(f"❌ 權杖重新整理失敗: {refresh_message}")
                    return (None, current_token, refresh_message, processing_log)
            else:
                error_msg = f"容器創建失敗: {response.status_code} - {response.text}"
                processing_log.append(f"❌ {error_msg}")
                return (None, current_token, error_msg, processing_log)
                
        except Exception as e:
            error_msg = f"創建容器異常: {str(e)}"
            processing_log.append(f"❌ {error_msg}")
            return (None, current_token, error_msg, processing_log)
    
    def publish_threads_container_with_retry(self, creation_id: str, access_token: str,
                                           auto_refresh: bool = True, client_secret: str = "") -> tuple:
        """
        發布 Threads 容器並支援重試 - Step 2: 發布容器
        """
        try:
            processing_log = []
            processing_log.append("🚀 開始發布容器...")
            
            url = f"{self.base_url}/me/threads_publish"
            current_token = access_token
            
            data = {
                'creation_id': creation_id,
                'access_token': current_token
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            processing_log.append(f"發布容器 URL: {url}")
            processing_log.append(f"發布容器數據: {dict(data, access_token='[HIDDEN]')}")
            
            response = requests.post(url, data=data, headers=headers, timeout=30)
            processing_log.append(f"發布響應: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                processing_log.append(f"✅ 發布成功: {result}")
                return (result, current_token, "發布成功", processing_log)
                
            elif response.status_code == 190:  # 權杖過期
                new_token, refresh_success, refresh_message = self.handle_api_error_with_token_refresh(
                    response, current_token, client_secret, auto_refresh
                )
                
                if refresh_success:
                    processing_log.append("✅ 權杖重新整理成功，重試發布...")
                    # 使用新權杖重試
                    data['access_token'] = new_token
                    retry_response = requests.post(url, data=data, headers=headers, timeout=30)
                    
                    if retry_response.status_code == 200:
                        result = retry_response.json()
                        processing_log.append(f"✅ 使用新權杖發布成功: {result}")
                        return (result, new_token, f"權杖已重新整理，發布成功", processing_log)
                    else:
                        processing_log.append(f"❌ 使用新權杖重試失敗: {retry_response.text}")
                        return (None, new_token, f"使用新權杖重試失敗: {retry_response.text}", processing_log)
                else:
                    processing_log.append(f"❌ 權杖重新整理失敗: {refresh_message}")
                    return (None, current_token, refresh_message, processing_log)
            else:
                error_msg = f"發布失敗: {response.status_code} - {response.text}"
                processing_log.append(f"❌ {error_msg}")
                return (None, current_token, error_msg, processing_log)
                
        except Exception as e:
            error_msg = f"發布異常: {str(e)}"
            processing_log.append(f"❌ {error_msg}")
            return (None, current_token, error_msg, processing_log)
    
    def publish_all_in_one(self, access_token: str, text: str, threads_user_id: str, post_type: str,
                          media_file_path: str = "", media_url: str = "", auto_upload: bool = True,
                          upload_service: str = "imgur", auto_refresh_token: bool = True,
                          client_secret: str = "", imgur_client_id: str = "",
                          auto_optimize: bool = True, max_file_size_mb: float = 10.0,
                          video_check_timeout: int = 60, video_check_interval: int = 5):
        """
        一體化發布函數 - 支援長期權杖自動管理和增強的視頻發布
        """
        try:
            processing_log = ["=== Threads 一體化發布開始（增強視頻支援）==="]
            processing_log.append(f"發布類型: {post_type}")
            processing_log.append(f"文本長度: {len(text)} 字符")
            processing_log.append(f"自動權杖重新整理: {auto_refresh_token}")
            
            if post_type == "VIDEO_POST":
                processing_log.append(f"視頻檢查超時: {video_check_timeout} 秒")
                processing_log.append(f"視頻檢查間隔: {video_check_interval} 秒")
            
            current_token = access_token
            media_url_used = ""
            
            # 先驗證權杖
            if auto_refresh_token:
                processing_log.append("\n🔐 權杖驗證階段")
                token_validator = ThreadsTokenValidatorNode()
                is_valid, permissions, validation_report, needs_refresh = token_validator.validate_token(
                    current_token, True, 7
                )
                
                if not is_valid:
                    error_msg = f"❌ 權杖驗證失敗: {validation_report}"
                    processing_log.append(error_msg)
                    return ("", "", False, error_msg, "", "\n".join(processing_log), current_token)
                
                processing_log.append("✅ 權杖驗證通過")
            
            # 處理媒體文件（如果需要）
            if post_type in ['IMAGE_POST', 'VIDEO_POST']:
                media_type = post_type.replace('_POST', '')
                processing_log.append(f"\n📁 媒體處理階段")
                
                if media_url:
                    media_url_used = media_url
                    processing_log.append(f"使用提供的媒體URL: {media_url[:50]}...")
                    
                elif media_file_path and auto_upload:
                    processing_log.append(f"處理本地文件: {media_file_path}")
                    
                    # 上傳文件
                    processing_log.append(f"📤 使用 {upload_service} 上傳...")
                    
                    upload_result = self.media_uploader.upload_media(
                        upload_service, media_file_path, media_type, imgur_client_id
                    )
                    
                    media_url_result, upload_success, upload_method, upload_message = upload_result
                    
                    if upload_success:
                        media_url_used = media_url_result
                        processing_log.append(f"✅ 上傳成功: {upload_method}")
                    else:
                        error_msg = f"❌ 上傳失敗: {upload_message}"
                        processing_log.append(error_msg)
                        return ("", "", False, error_msg, "", "\n".join(processing_log), current_token)
                        
                else:
                    error_msg = f"❌ {post_type} 需要提供媒體文件或URL"
                    processing_log.append(error_msg)
                    return ("", "", False, error_msg, "", "\n".join(processing_log), current_token)
            
            # 發布到 Threads
            processing_log.append(f"\n🚀 Threads 發布階段")
            
            # 確定媒體類型
            if post_type == "TEXT_ONLY":
                media_type = "TEXT"
            elif post_type == "IMAGE_POST":
                media_type = "IMAGE"
            elif post_type == "VIDEO_POST":
                media_type = "VIDEO"
            
            # 創建容器
            processing_log.append("📝 創建發布容器...")
            creation_id, updated_token, create_message, container_log = self.create_threads_container_with_retry(
                threads_user_id, current_token, media_type, text, media_url_used,
                auto_refresh_token, client_secret, video_check_timeout, video_check_interval
            )
            
            processing_log.extend(container_log)
            current_token = updated_token
            
            if not creation_id:
                processing_log.append(f"❌ {create_message}")
                return ("", "", False, create_message, media_url_used, "\n".join(processing_log), current_token)
            
            processing_log.append(f"✅ 容器創建成功: {creation_id}")
            if updated_token != access_token:
                processing_log.append("🔄 權杖已在創建階段自動重新整理")
            
            # 發布容器
            processing_log.append("🎯 發布容器...")
            publish_result, final_token, publish_message, publish_log = self.publish_threads_container_with_retry(
                creation_id, current_token, auto_refresh_token, client_secret
            )
            
            processing_log.extend(publish_log)
            
            if not publish_result:
                processing_log.append(f"❌ {publish_message}")
                return ("", "", False, publish_message, media_url_used, "\n".join(processing_log), final_token)
            
            # 獲取結果
            post_id = publish_result.get('id', '')
            permalink = f"https://threads.net/post/{post_id}"
            
            processing_log.append(f"✅ 發布成功!")
            processing_log.append(f"帖子 ID: {post_id}")
            processing_log.append(f"鏈接: {permalink}")
            
            if final_token != access_token:
                processing_log.append("🔄 權杖已在發布過程中自動重新整理")
            
            success_message = f"✅ 成功發布到 Threads!\n帖子類型: {post_type}\n帖子 ID: {post_id}"
            if media_url_used:
                success_message += f"\n媒體URL: {media_url_used[:50]}..."
            if final_token != access_token:
                success_message += "\n🔄 權杖已自動重新整理"
            
            processing_log.append("\n=== 發布完成 ===")
            
            return (post_id, permalink, True, success_message, media_url_used, "\n".join(processing_log), final_token)
            
        except Exception as e:
            error_message = f"❌ 發布過程異常: {str(e)}"
            processing_log.append(error_message)
            print(error_message)
            import traceback
            traceback.print_exc()
            return ("", "", False, error_message, media_url_used, "\n".join(processing_log), current_token)


class ThreadsUserInfoNode:
   """
   獲取 Threads 用戶信息的節點 - 支援長期權杖
   """
   
   @classmethod
   def INPUT_TYPES(cls):
       return {
           "required": {
               "access_token": ("STRING", {
                   "default": "",
                   "multiline": False
               }),
           },
           "optional": {
               "auto_refresh_token": ("BOOLEAN", {
                   "default": True
               }),
               "client_secret": ("STRING", {
                   "default": "",
                   "multiline": False
               }),
           }
       }
   
   RETURN_TYPES = ("STRING", "STRING", "STRING", "BOOLEAN", "STRING", "STRING")
   RETURN_NAMES = ("user_id", "username", "user_info", "success", "message", "refreshed_token")
   CATEGORY = "Social Media/Threads"
   FUNCTION = "get_user_info"
   
   def __init__(self):
       self.api_version = "v1.0"
       self.base_url = f"https://graph.threads.net/{self.api_version}"
       self.token_manager = ThreadsTokenManagerNode()
   
   def get_user_info(self, access_token: str, auto_refresh_token: bool = True, client_secret: str = ""):
       """
       獲取用戶信息 - 支援權杖自動重新整理
       """
       try:
           if not access_token or access_token.strip() == "":
               return ("", "", "", False, "請提供有效的 Access Token", access_token)
           
           print("獲取 Threads 用戶信息...")
           current_token = access_token
           
           # 獲取用戶基本信息
           url = f"{self.base_url}/me"
           params = {
               'fields': 'id,username,name,threads_profile_picture_url,threads_biography',
               'access_token': current_token
           }
           
           print(f"請求 URL: {url}")
           print(f"請求參數: {dict(params, access_token='[HIDDEN]')}")
           
           response = requests.get(url, params=params, timeout=30)
           
           print(f"響應狀態: {response.status_code}")
           print(f"響應內容: {response.text}")
           
           if response.status_code == 200:
               user_data = response.json()
               
               user_id = user_data.get('id', '')
               username = user_data.get('username', '')
               name = user_data.get('name', '')
               
               # 格式化用戶信息
               user_info_lines = [
                   f"用戶 ID: {user_id}",
                   f"用戶名: @{username}",
                   f"顯示名稱: {name}",
               ]
               
               if 'threads_profile_picture_url' in user_data:
                   user_info_lines.append(f"頭像 URL: {user_data['threads_profile_picture_url']}")
               
               if 'threads_biography' in user_data:
                   bio = user_data['threads_biography']
                   if bio:
                       user_info_lines.append(f"簡介: {bio}")
               
               user_info = "\n".join(user_info_lines)
               
               success_message = f"✅ 成功獲取用戶信息\n用戶ID: {user_id}\n用戶名: @{username}"
               
               print(success_message)
               return (user_id, username, user_info, True, success_message, current_token)
               
           elif response.status_code == 190:  # 權杖過期
               if auto_refresh_token and client_secret:
                   print("🔄 權杖過期，嘗試自動重新整理...")
                   
                   new_token, refresh_success, refresh_message, expires_days, token_type = self.token_manager.refresh_long_lived_token(current_token)
                   
                   if refresh_success:
                       print(f"✅ 權杖重新整理成功，重試獲取用戶信息...")
                       
                       # 使用新權杖重試
                       params['access_token'] = new_token
                       retry_response = requests.get(url, params=params, timeout=30)
                       
                       if retry_response.status_code == 200:
                           user_data = retry_response.json()
                           
                           user_id = user_data.get('id', '')
                           username = user_data.get('username', '')
                           name = user_data.get('name', '')
                           
                           user_info_lines = [
                               f"用戶 ID: {user_id}",
                               f"用戶名: @{username}",
                               f"顯示名稱: {name}",
                           ]
                           
                           if 'threads_profile_picture_url' in user_data:
                               user_info_lines.append(f"頭像 URL: {user_data['threads_profile_picture_url']}")
                           
                           if 'threads_biography' in user_data:
                               bio = user_data['threads_biography']
                               if bio:
                                   user_info_lines.append(f"簡介: {bio}")
                           
                           user_info = "\n".join(user_info_lines)
                           
                           success_message = f"✅ 權杖已重新整理並成功獲取用戶信息\n用戶ID: {user_id}\n用戶名: @{username}\n🔄 新權杖有效期: {expires_days} 天"
                           
                           print(success_message)
                           return (user_id, username, user_info, True, success_message, new_token)
                       else:
                           error_msg = f"❌ 使用新權杖重試失敗: {retry_response.text}"
                           return ("", "", "", False, error_msg, new_token)
                   else:
                       error_msg = f"❌ 權杖重新整理失敗: {refresh_message}"
                       return ("", "", "", False, error_msg, current_token)
               else:
                   error_msg = "❌ Access Token 無效或已過期\n💡 請提供 client_secret 以啟用自動權杖重新整理"
                   print(error_msg)
                   return ("", "", "", False, error_msg, current_token)
               
           elif response.status_code == 403:
               error_msg = "❌ 權限不足，請檢查 Token 權限設置"
               print(error_msg)
               return ("", "", "", False, error_msg, current_token)
               
           else:
               try:
                   error_data = response.json()
                   error_detail = error_data.get('error', {})
                   error_msg = f"❌ 請求失敗: {response.status_code}\n錯誤: {error_detail.get('message', '未知錯誤')}"
               except:
                   error_msg = f"❌ 請求失敗: {response.status_code}\n響應: {response.text}"
               
               print(error_msg)
               return ("", "", "", False, error_msg, current_token)
               
       except Exception as e:
           error_message = f"❌ 獲取用戶信息時發生異常: {str(e)}"
           print(error_message)
           import traceback
           traceback.print_exc()
           return ("", "", "", False, error_message, access_token)


class ThreadsQuickTestNode:
   """
   快速測試整個發布流程的節點 - 支援長期權杖
   """
   
   @classmethod
   def INPUT_TYPES(cls):
       return {
           "required": {
               "access_token": ("STRING", {
                   "default": "",
                   "multiline": False
               }),
               "test_text": ("STRING", {
                   "multiline": True,
                   "default": "Quick test from ComfyUI"
               }),
               "threads_user_id": ("STRING", {
                   "default": "me",
                   "multiline": False
               }),
           },
           "optional": {
               "auto_refresh_token": ("BOOLEAN", {
                   "default": True
               }),
               "client_secret": ("STRING", {
                   "default": "",
                   "multiline": False
               }),
           }
       }
   
   RETURN_TYPES = ("STRING", "BOOLEAN", "STRING", "STRING")
   RETURN_NAMES = ("test_result", "success", "post_id", "final_token")
   CATEGORY = "Social Media/Debug"
   FUNCTION = "quick_test"
   
   def __init__(self):
       self.api_version = "v1.0"
       self.base_url = f"https://graph.threads.net/{self.api_version}"
       self.token_manager = ThreadsTokenManagerNode()
   
   def quick_test(self, access_token: str, test_text: str, threads_user_id: str,
                 auto_refresh_token: bool = True, client_secret: str = ""):
       """
       快速測試完整流程 - 支援權杖自動重新整理
       """
       try:
           test_log = ["=== Threads 快速測試開始（支援長期權杖）==="]
           current_token = access_token
           
           # 步驟0: 權杖驗證
           if auto_refresh_token:
               test_log.append("\n🔐 步驟0: 權杖驗證")
               validator = ThreadsTokenValidatorNode()
               is_valid, permissions, validation_report, needs_refresh = validator.validate_token(
                   current_token, True, 7
               )
               
               if not is_valid:
                   test_log.append("❌ 權杖驗證失敗")
                   test_log.append(validation_report)
                   return ("\n".join(test_log), False, "", current_token)
               
               test_log.append("✅ 權杖驗證通過")
           
           # 步驟1: 創建容器
           test_log.append("\n📝 步驟1: 創建文本容器")
           
           create_url = f"{self.base_url}/{threads_user_id}/threads"
           create_params = {
               'media_type': 'TEXT',
               'text': test_text,
               'access_token': current_token
           }
           
           test_log.append(f"創建URL: {create_url}")
           test_log.append(f"創建參數: {dict(create_params, access_token='[HIDDEN]')}")
           
           create_response = requests.post(create_url, params=create_params, timeout=30)
           test_log.append(f"創建狀態: {create_response.status_code}")
           test_log.append(f"創建響應: {create_response.text}")
           
           if create_response.status_code == 190 and auto_refresh_token and client_secret:
               test_log.append("🔄 權杖過期，嘗試自動重新整理...")
               
               new_token, refresh_success, refresh_message, expires_days, token_type = self.token_manager.refresh_long_lived_token(current_token)
               
               if refresh_success:
                   test_log.append(f"✅ 權杖重新整理成功，有效期: {expires_days} 天")
                   current_token = new_token
                   
                   # 使用新權杖重試
                   create_params['access_token'] = current_token
                   create_response = requests.post(create_url, params=create_params, timeout=30)
                   test_log.append(f"重試創建狀態: {create_response.status_code}")
                   test_log.append(f"重試創建響應: {create_response.text}")
               else:
                   test_log.append(f"❌ 權杖重新整理失敗: {refresh_message}")
                   return ("\n".join(test_log), False, "", current_token)
           
           if create_response.status_code != 200:
               test_log.append("❌ 容器創建失敗")
               return ("\n".join(test_log), False, "", current_token)
           
           create_data = create_response.json()
           creation_id = create_data.get('id')
           test_log.append(f"✅ 容器創建成功: {creation_id}")
           
           # 步驟2: 嘗試發布
           test_log.append(f"\n🚀 步驟2: 測試發布")
           
           # 方法A: 標準方法
           test_log.append("\n嘗試方法A: POST /{creation-id}/publish")
           publish_url_a = f"{self.base_url}/{creation_id}/publish"
           publish_data_a = {'access_token': current_token}
           
           publish_response_a = requests.post(publish_url_a, data=publish_data_a, timeout=30)
           test_log.append(f"方法A狀態: {publish_response_a.status_code}")
           
           if publish_response_a.status_code == 190 and auto_refresh_token and client_secret:
               test_log.append("🔄 發布時權杖過期，使用已刷新的權杖重試...")
               publish_data_a['access_token'] = current_token
               publish_response_a = requests.post(publish_url_a, data=publish_data_a, timeout=30)
               test_log.append(f"方法A重試狀態: {publish_response_a.status_code}")
           
           if publish_response_a.status_code == 200:
               test_log.append("✅ 方法A發布成功!")
               result_data = publish_response_a.json()
               post_id = result_data.get('id', '')
               test_log.append(f"帖子ID: {post_id}")
               return ("\n".join(test_log), True, post_id, current_token)
           else:
               test_log.append(f"方法A失敗: {publish_response_a.text}")
           
           # 方法B: 替代方法
           test_log.append("\n嘗試方法B: POST /me/threads_publish")
           publish_url_b = f"{self.base_url}/me/threads_publish"
           publish_data_b = {
               'creation_id': creation_id,
               'access_token': current_token
           }
           
           publish_response_b = requests.post(publish_url_b, data=publish_data_b, timeout=30)
           test_log.append(f"方法B狀態: {publish_response_b.status_code}")
           
           if publish_response_b.status_code == 190 and auto_refresh_token and client_secret:
               test_log.append("🔄 發布時權杖過期，使用已刷新的權杖重試...")
               publish_data_b['access_token'] = current_token
               publish_response_b = requests.post(publish_url_b, data=publish_data_b, timeout=30)
               test_log.append(f"方法B重試狀態: {publish_response_b.status_code}")
           
           if publish_response_b.status_code == 200:
               test_log.append("✅ 方法B發布成功!")
               result_data = publish_response_b.json()
               post_id = result_data.get('id', '')
               test_log.append(f"帖子ID: {post_id}")
               return ("\n".join(test_log), True, post_id, current_token)
           else:
               test_log.append(f"方法B失敗: {publish_response_b.text}")
           
           test_log.append("\n❌ 所有發布方法都失敗了")
           test_log.append("\n💡 建議:")
           test_log.append("1. 檢查Token權限設置")
           test_log.append("2. 確認帳戶狀態")
           test_log.append("3. 使用 ThreadsTokenManagerNode 手動重新整理權杖")
           test_log.append("4. 聯繫Meta支持")
           
           return ("\n".join(test_log), False, "", current_token)
           
       except Exception as e:
           error_message = f"❌ 測試過程異常: {str(e)}"
           print(error_message)
           return (error_message, False, "", access_token)


# 節點註冊 - 更新版本
NODE_CLASS_MAPPINGS = {
   # 權杖管理節點
   "ThreadsTokenManagerNode": ThreadsTokenManagerNode,
   
   # 增強的核心節點
   "ThreadsOfficialFormatNode": ThreadsOfficialFormatNode,
   "ThreadsUserInfoNode": ThreadsUserInfoNode,
   "ThreadsTokenValidatorNode": ThreadsTokenValidatorNode,
   "ThreadsQuickTestNode": ThreadsQuickTestNode,
   
   # 媒體處理節點
   "ThreadsMediaUploaderNode": ThreadsMediaUploaderNode,
   
   # 一體化節點
   "ThreadsAllInOneNode": ThreadsAllInOneNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
   # 權杖管理
   "ThreadsTokenManagerNode": "🔑 Threads Token Manager",
   
   # 增強的核心節點
   "ThreadsOfficialFormatNode": "🧵 Threads Official Format (Enhanced)",
   "ThreadsUserInfoNode": "👤 Get Threads User Info (Enhanced)",
   "ThreadsTokenValidatorNode": "🔐 Validate Threads Token (Enhanced)",
   "ThreadsQuickTestNode": "⚡ Threads Quick Test (Enhanced)",
   
   # 媒體處理
   "ThreadsMediaUploaderNode": "📤 Threads Media Uploader",
   
   # 一體化
   "ThreadsAllInOneNode": "🎯 Threads All-in-One (Enhanced)",
}
                