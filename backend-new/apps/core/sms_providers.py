import json
import os
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)


class SmsSendError(Exception):
    """短信发送异常，可携带错误码供前端区分"""
    def __init__(self, message: str, code: str = "SMS_SEND_FAILED"):
        super().__init__(message)
        self.code = code  # 错误码：CONFIG_MISSING / SDK_NOT_INSTALLED / UPSTREAM_FAILED / RATE_LIMITED


@dataclass
class SmsSendResult:
    provider: str
    biz_id: str = ""
    raw_response: dict | None = None


class BaseSmsProvider(ABC):
    @abstractmethod
    def send_code(self, phone: str, code: str, message_type: str = "sms") -> SmsSendResult:
        raise NotImplementedError

    @property
    @abstractmethod
    def is_development(self) -> bool:
        """是否为开发/占位通道（前端可据此提示用户）"""
        return False


class MockSmsProvider(BaseSmsProvider):
    def send_code(self, phone: str, code: str, message_type: str = "sms") -> SmsSendResult:
        return SmsSendResult(provider="mock", biz_id=f"mock-{message_type}-{phone}-{code}", raw_response={"Message": "OK"})

    @property
    def is_development(self) -> bool:
        return True


class AliyunSmsProvider(BaseSmsProvider):
    """阿里云短信服务（真实发送）"""

    def __init__(self):
        self.access_key_id = getattr(settings, "ALIYUN_ACCESS_KEY_ID", "")
        self.access_key_secret = getattr(settings, "ALIYUN_ACCESS_KEY_SECRET", "")
        self.sign_name = getattr(settings, "ALIYUN_SMS_SIGN_NAME", "")
        self.template_code = getattr(settings, "ALIYUN_SMS_TEMPLATE_CODE", "")
        self.endpoint = getattr(settings, "ALIYUN_SMS_ENDPOINT", "dysmsapi.aliyuncs.com")
        self.region = getattr(settings, "ALIYUN_SMS_REGION", "cn-hangzhou")

    @property
    def is_development(self) -> bool:
        return False

    def _validate_config(self):
        """检查阿里云配置完整性，返回 (ok, error_message, error_code)"""
        required = {
            "ALIYUN_ACCESS_KEY_ID": self.access_key_id,
            "ALIYUN_ACCESS_KEY_SECRET": self.access_key_secret,
            "ALIYUN_SMS_SIGN_NAME": self.sign_name,
            "ALIYUN_SMS_TEMPLATE_CODE": self.template_code,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise SmsSendError(
                f"阿里云短信配置缺失: {', '.join(missing)}，请联系管理员完善配置",
                code="CONFIG_MISSING",
            )
        # 检测明显的配置错误：AccessKey ID 应以 LTAI 开头
        if not self.access_key_id.startswith("LTAI"):
            raise SmsSendError(
                "阿里云 AccessKey ID 格式异常（应以 LTAI 开头），请检查 .env 中的 ALIYUN_ACCESS_KEY_ID",
                code="CONFIG_INVALID",
            )

    def send_code(self, phone: str, code: str, message_type: str = "sms") -> SmsSendResult:
        self._validate_config()

        # SDK 可选依赖检测
        try:
            from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
            from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
            from alibabacloud_tea_openapi import models as open_api_models
            from alibabacloud_tea_util import models as util_models
        except ImportError:
            raise SmsSendError(
                "阿里云短信 SDK 未安装，请运行: pip install alibabacloud_dysmsapi20170525 alibabacloud_tea_openapi alibabacloud_tea_util",
                code="SDK_NOT_INSTALLED",
            )

        try:
            config_obj = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
                endpoint=self.endpoint,
                region_id=self.region,
            )
            client = Dysmsapi20170525Client(config_obj)
            request_obj = dysmsapi_20170525_models.SendSmsRequest(
                phone_numbers=phone,
                sign_name=self.sign_name,
                template_code=self.template_code,
                template_param=json.dumps({"code": code}, ensure_ascii=False),
            )
            runtime = util_models.RuntimeOptions()
            response = client.send_sms_with_options(request_obj, runtime)
            body = response.body.to_map() if response and response.body else {}

            aliyun_code = body.get("Code", "")
            if aliyun_code != "OK":
                aliyun_msg = body.get("Message", "unknown error")
                # 常见错误码翻译
                if aliyun_code == "isv.BUSINESS_LIMIT_CONTROL":
                    raise SmsSendError(f"短信发送频率超限: {aliyun_msg}", code="RATE_LIMITED")
                elif aliyun_code == "isv.MOBILE_NUMBER_ILLEGAL":
                    raise SmsSendError(f"手机号格式不合法: {aliyun_msg}", code="INVALID_PHONE")
                elif aliyun_code == "isv.AMOUNT_NOT_ENOUGH":
                    raise SmsSendError(f"阿里云短信余额不足: {aliyun_msg}", code="BALANCE_INSUFFICIENT")
                elif aliyun_code == "isv.TEMPLATE_MISSING_PARAMETERS":
                    raise SmsSendError(f"短信模板变量缺失: {aliyun_msg}", code="TEMPLATE_ERROR")
                elif aliyun_code.startswith("Signature"):
                    raise SmsSendError(f"签名/鉴权错误: {aliyun_msg}", code="AUTH_FAILED")
                else:
                    raise SmsSendError(f"阿里云短信发送失败 [{aliyun_code}]: {aliyun_msg}", code="UPSTREAM_FAILED")

            return SmsSendResult(provider="aliyun", biz_id=body.get("BizId", ""), raw_response=body)

        except SmsSendError:
            raise
        except Exception as exc:
            raise SmsSendError(f"短信服务异常: {exc}", code="NETWORK_ERROR") from exc


class TencentSmsProvider(BaseSmsProvider):
    """腾讯云短信服务（当前为开发占位，需接入真实 SDK）"""

    @property
    def is_development(self) -> bool:
        return True

    def send_code(self, phone: str, code: str, message_type: str = "sms") -> SmsSendResult:
        # 生产环境需接入腾讯云 SDK
        logger.warning("TencentSmsProvider is running in DEVELOPMENT mode - SMS will NOT be actually sent")
        return SmsSendResult(
            provider="tencent-dev",
            biz_id=f"tencent-{message_type}-{phone}-{code}",
            raw_response={"Code": "OK", "mode": "development"},
        )


def get_sms_provider(provider: str | None = None) -> BaseSmsProvider:
    provider_name = (provider or getattr(settings, "SMS_PROVIDER", "") or os.getenv("SMS_PROVIDER", "aliyun")).strip().lower()
    if provider_name == "mock":
        return MockSmsProvider()
    if provider_name == "aliyun":
        return AliyunSmsProvider()
    if provider_name == "tencent":
        return TencentSmsProvider()
    raise SmsSendError(f"unsupported sms provider: {provider_name}", code="CONFIG_INVALID")
