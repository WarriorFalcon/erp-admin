import uuid
import hashlib
import json
import csv
import time
import os
import socket
from pathlib import Path
from typing import Any, Dict
from datetime import timedelta
import json
from django.conf import settings
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import connections
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import requests

from apps.common.rbac_permissions import HasApiIntegratorRole
from apps.common.responses import error_response, success_response

from .models import (
    ApiIdempotencyRecord,
    CollectionTask,
    DeadLetterTask,
    InventorySyncLog,
    LogisticsRateCard,
    LogisticsShipment,
    LogisticsTrackingEvent,
    Order,
    PlatformToken,
    RegistrationAudit,
    UserPhoneBinding,
    AccountDeletionLog,
    SmsDispatchLog,
    PhoneRebindAppeal,
    DevicePhoneRelation,
    Product,
    ProductVariant,
    ReplayAuditLog,
    ScrapeRule,
    Shop,
    SyncRule,
)
from .platform_clients import get_platform_client
from .logistics_clients import get_logistics_aggregator_client
from .permissions import HasOrderEditPermission, IsOpsAdmin
from .serializers import (
    CollectionTaskCreateSerializer,
    CollectionTaskSerializer,
    InventorySyncLogSerializer,
    FreightEstimateQuerySerializer,
    LogisticsShipmentSerializer,
    LogisticsRateCardSerializer,
    OrderSerializer,
    OrderAddressUpdateSerializer,
    OrderStatusUpdateSerializer,
    ProductSerializer,
    SmsCodeSendSerializer,
    SmsCodeVerifySerializer,
    MobileAuthSerializer,
    AccountDeleteSerializer,
    PhoneRebindAppealSerializer,
    SmsChannelStatsQuerySerializer,
    ShopSerializer,
)
from .sms_providers import SmsSendError
from .sms_service import (
    check_send_rate_limits,
    create_captcha_challenge,
    generate_sms_code,
    get_client_ip,
    check_and_incr_global_sms_limit,
    is_device_blacklisted,
    register_device_phone_attempt,
    record_send_success,
    store_sms_code,
    verify_sms_code_with_lua,
    validate_captcha_if_required,
)
from .services import build_expire_time
from .tasks import execute_collection_task, refresh_platform_token, scheduled_inventory_sync, send_sms_with_failover


def _request_hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()


# RBAC：采集/同步/平台 Token 刷新等业务接口（Django Group + JWT）
_BUSINESS_API_PERMISSIONS = [IsAuthenticated, HasApiIntegratorRole]
class AuthLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="获取平台授权 URL")
    def get(self, request, platform):
        try:
            client = get_platform_client(platform)
            state = request.query_params.get("state", str(uuid.uuid4()))
            login_url = client.get_oauth_authorize_url(state=state)
            return success_response({"authorization_url": login_url, "state": state})
        except Exception as exc:
            return error_response(message=str(exc), status_code=status.HTTP_400_BAD_REQUEST)


class AuthCallbackView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="平台 OAuth 回调并保存 Token")
    def get(self, request, platform):
        code = request.query_params.get("code")
        if not code:
            return error_response(message="code is required", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            client = get_platform_client(platform)
            token_payload = client.exchange_code_for_token(code)
            token_obj, _ = PlatformToken.objects.get_or_create(
                platform=platform,
                account_id=token_payload.get("account_id", "default"),
            )
            token_obj.set_tokens(token_payload["access_token"], token_payload["refresh_token"])
            token_obj.expires_at = build_expire_time(token_payload["expires_in"])
            token_obj.save()
            token_obj.cache_tokens()
            return success_response(
                {
                    "platform": token_obj.platform,
                    "account_id": token_obj.account_id,
                    "expires_at": token_obj.expires_at,
                }
            )
        except Exception as exc:
            return error_response(message=str(exc), status_code=status.HTTP_400_BAD_REQUEST)


class AuthRefreshView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="手动刷新平台 Token")
    def post(self, request, platform):
        account_id = request.data.get("account_id", "default")
        token_obj = get_object_or_404(PlatformToken, platform=platform, account_id=account_id)
        refresh_platform_token.delay(token_obj.id)
        return success_response({"queued": True, "token_id": token_obj.id})


class CollectionTaskCreateView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="创建采集任务并推送队列")
    def post(self, request):
        idem_key = request.headers.get("X-Idempotency-Key", "").strip()
        if idem_key:
            req_hash = _request_hash(request.data)
            existing = ApiIdempotencyRecord.objects.filter(idem_key=idem_key, endpoint=request.path).first()
            if existing and existing.request_hash == req_hash:
                return success_response(existing.response_data, status_code=existing.status_code)

        serializer = CollectionTaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = CollectionTask.objects.create(
            platform=serializer.validated_data["platform"],
            target_ids=serializer.validated_data["target_ids"],
            status="pending",
        )
        execute_collection_task.delay(task.id)
        response_data = {"task_id": task.id, "status": task.status}
        if idem_key:
            ApiIdempotencyRecord.objects.update_or_create(
                idem_key=idem_key,
                endpoint=request.path,
                defaults={
                    "request_hash": _request_hash(request.data),
                    "response_data": response_data,
                    "status_code": status.HTTP_201_CREATED,
                },
            )
        return success_response(response_data, status_code=status.HTTP_201_CREATED)


class CollectionTaskStatusView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="查询采集任务状态")
    def get(self, request, task_id):
        task = get_object_or_404(CollectionTask, id=task_id)
        data = CollectionTaskSerializer(task).data
        return success_response(data)


class SyncTriggerView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="手动触发库存同步")
    def post(self, request):
        idem_key = request.headers.get("X-Idempotency-Key", "").strip()
        if idem_key:
            req_hash = _request_hash(request.data)
            existing = ApiIdempotencyRecord.objects.filter(idem_key=idem_key, endpoint=request.path).first()
            if existing and existing.request_hash == req_hash:
                return success_response(existing.response_data, status_code=existing.status_code)

        scheduled_inventory_sync.delay()
        response_data = {"queued": True}
        if idem_key:
            ApiIdempotencyRecord.objects.update_or_create(
                idem_key=idem_key,
                endpoint=request.path,
                defaults={"request_hash": _request_hash(request.data), "response_data": response_data, "status_code": 200},
            )
        return success_response(response_data)


class SyncLogView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="获取库存同步日志")
    def get(self, request):
        logs = InventorySyncLog.objects.all().order_by("-created_at")[:100]
        data = InventorySyncLogSerializer(logs, many=True).data
        return success_response(data)


class DeadLetterListView(APIView):
    permission_classes = [IsAuthenticated, IsOpsAdmin]

    @extend_schema(summary="查看 dead-letter 列表")
    def get(self, request):
        queryset = DeadLetterTask.objects.all().order_by("-created_at")
        status_value = request.query_params.get("status")
        task_name = request.query_params.get("task_name")
        if status_value:
            queryset = queryset.filter(status=status_value)
        if task_name:
            queryset = queryset.filter(task_name=task_name)

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_size = min(max(page_size, 1), 200)
        paginator = Paginator(queryset, page_size)
        current_page = paginator.get_page(page)
        rows = current_page.object_list
        data = [
            {
                "id": row.id,
                "task_name": row.task_name,
                "payload": row.payload,
                "error_message": row.error_message,
                "retry_count": row.retry_count,
                "status": row.status,
                "created_at": row.created_at,
            }
            for row in rows
        ]
        return success_response(
            {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "page": current_page.number,
                "page_size": page_size,
                "results": data,
            }
        )


class DeadLetterReplayView(APIView):
    permission_classes = [IsAuthenticated, IsOpsAdmin]

    @extend_schema(summary="重放 dead-letter 任务")
    def post(self, request, dead_letter_id):
        row = get_object_or_404(DeadLetterTask, id=dead_letter_id)
        task_name = row.task_name
        payload = row.payload or {}
        operator = request.user.username if getattr(request, "user", None) and request.user.is_authenticated else "system"

        try:
            if task_name == "execute_collection_task":
                execute_collection_task.delay(payload["task_id"])
            elif task_name == "refresh_platform_token":
                refresh_platform_token.delay(payload["token_id"])
            elif task_name == "sync_inventory_by_rule":
                from .tasks import sync_inventory_by_rule

                sync_inventory_by_rule.delay(payload["sync_rule_id"])
            else:
                ReplayAuditLog.objects.create(
                    dead_letter_task=row,
                    operator=operator,
                    result="failed",
                    detail=f"Unsupported task_name: {task_name}",
                )
                return error_response(message=f"Unsupported task_name: {task_name}", status_code=400)

            row.status = DeadLetterTask.STATUS_REPLAYED
            row.retry_count += 1
            row.save(update_fields=["status", "retry_count", "updated_at"])
            ReplayAuditLog.objects.create(dead_letter_task=row, operator=operator, result="success", detail="replay queued")
            return success_response({"replayed": True, "dead_letter_id": row.id})
        except Exception as exc:
            ReplayAuditLog.objects.create(dead_letter_task=row, operator=operator, result="failed", detail=str(exc))
            return error_response(message=str(exc), status_code=500)


class ReplayAuditLogListView(APIView):
    permission_classes = [IsAuthenticated, IsOpsAdmin]

    @extend_schema(summary="查看重放审计日志")
    def get(self, request):
        queryset = ReplayAuditLog.objects.all().order_by("-created_at")
        dead_letter_id = request.query_params.get("dead_letter_id")
        if dead_letter_id:
            queryset = queryset.filter(dead_letter_task_id=dead_letter_id)
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_size = min(max(page_size, 1), 200)
        paginator = Paginator(queryset, page_size)
        current_page = paginator.get_page(page)
        data = [
            {
                "id": row.id,
                "dead_letter_task_id": row.dead_letter_task_id,
                "operator": row.operator,
                "result": row.result,
                "detail": row.detail,
                "created_at": row.created_at,
            }
            for row in current_page.object_list
        ]
        return success_response(
            {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "page": current_page.number,
                "page_size": page_size,
                "results": data,
            }
        )


class OpsWhoAmIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="运维权限自检")
    def get(self, request):
        user = request.user
        ops_by_group = user.groups.filter(name="ops_admin").exists()
        ops_by_list = user.username in set(getattr(settings, "OPS_ADMIN_USERNAMES", []))
        is_ops_admin = user.is_superuser or ops_by_group or ops_by_list
        return success_response(
            {
                "username": user.username,
                "is_superuser": user.is_superuser,
                "ops_by_group": ops_by_group,
                "ops_by_list": ops_by_list,
                "is_ops_admin": is_ops_admin,
            }
        )


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(summary="系统健康检查")
    def get(self, request):
        # region agent log
        def _agent_log(hypothesis_id: str, message: str, data: dict) -> None:
            try:
                base_dir = getattr(settings, "BASE_DIR", ".")
                log_path = Path(str(base_dir)) / "debug-ac2c4e.log"
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(
                        json.dumps(
                            {
                                "sessionId": "ac2c4e",
                                "runId": "pre-fix",
                                "hypothesisId": hypothesis_id,
                                "location": "apps/core/views.py:HealthCheckView.get",
                                "message": message,
                                "data": data or {},
                                "timestamp": int(time.time() * 1000),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            except Exception:
                pass

        db = (getattr(settings, "DATABASES", {}) or {}).get("default", {}) or {}
        db_engine = db.get("ENGINE")
        db_host = db.get("HOST")
        db_port = db.get("PORT")
        _agent_log(
            "DB_H1_H2_H3_H4",
            "healthcheck db resolved",
            {"engine": db_engine, "host": db_host, "port": db_port, "path": request.path},
        )

        tcp_ok = None
        tcp_err = None
        try:
            port_int = int(str(db_port or "3306"))
            host_str = str(db_host or "127.0.0.1")
            with socket.create_connection((host_str, port_int), timeout=1.5):
                tcp_ok = True
        except Exception as exc:
            tcp_ok = False
            tcp_err = f"{type(exc).__name__}: {exc}"
        _agent_log(
            "DB_H1_H2",
            "healthcheck mysql tcp probe",
            {"tcp_ok": tcp_ok, "tcp_error": tcp_err, "host": db_host, "port": db_port},
        )
        # endregion

        checks = {"database": False, "cache": False}
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            checks["database"] = True
        except Exception:
            checks["database"] = False
            # region agent log
            _agent_log("DB_H1_H2_H3_H4_H5", "healthcheck db query failed", {"database": checks["database"]})
            # endregion
        else:
            # region agent log
            _agent_log("DB_H5", "healthcheck db query ok", {"database": checks["database"]})
            # endregion

        try:
            cache.set("healthcheck:ping", "pong", timeout=10)
            checks["cache"] = cache.get("healthcheck:ping") == "pong"
        except Exception:
            checks["cache"] = False

        ok = all(checks.values())
        code = 200 if ok else 503
        return success_response(
            data={
                "status": "ok" if ok else "degraded",
                "checks": checks,
                "ops_admin_usernames": getattr(settings, "OPS_ADMIN_USERNAMES", []),
            },
            status_code=code,
            code=code,
            message="success" if ok else "service unavailable",
        )


class AuthMeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="获取当前用户信息")
    def get(self, request):
        user = request.user
        return success_response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_superuser": user.is_superuser,
            }
        )


class UserRegisterView(APIView):
    """真实业务：用户注册（用户名/密码 或 手机号/密码）。"""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(summary="用户注册")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        username = (payload.get("username") or payload.get("phone") or "").strip()
        password = payload.get("password") or ""
        if not username or not password:
            return error_response(message="username and password are required", status_code=400, code=400)

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            return error_response(message="username already exists", status_code=400, code=400)

        user = User.objects.create_user(username=username, password=password)
        refresh = RefreshToken.for_user(user)
        return success_response(
            data={
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {"id": user.id, "username": user.username},
            },
            code=200,
            status_code=200,
            message="registered",
        )


class UserLoginView(APIView):
    """真实业务：用户登录（用户名/密码）。"""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(summary="用户登录")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        username = (payload.get("username") or payload.get("phone") or "").strip()
        password = payload.get("password") or ""
        if not username or not password:
            return error_response(message="username and password are required", status_code=400, code=400)

        user = authenticate(request, username=username, password=password)
        if not user:
            return error_response(message="invalid credentials", status_code=401, code=401)

        refresh = RefreshToken.for_user(user)
        return success_response(
            data={
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {"id": user.id, "username": user.username},
            },
            code=200,
            status_code=200,
            message="ok",
        )


class UserRegisterSubmitView(APIView):
    """注册申请提交（含实名认证信息，管理员审核）"""
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(summary="提交注册申请")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        phone = (payload.get("phone") or "").strip()
        if not phone:
            return error_response(message="phone is required", status_code=400)

        User = get_user_model()
        if User.objects.filter(username=phone).exists():
            return error_response(message="该手机号已注册", status_code=400)

        # 创建待审核用户
        user = User.objects.create_user(
            username=phone, password=payload.get("password", "123456"),
            is_active=False,
        )
        # 保存注册附加信息到 profile（如果有）或 JSON 字段
        # 保存注册附加信息
        UserPhoneBinding.objects.update_or_create(
            user=user, phone=phone,
            defaults={"is_verified": False},
        )

        # 构造审核记录
        RegistrationAudit.objects.create(
            user=user,
            phone=phone,
            user_type=payload.get("user_type", "personal"),
            real_name=payload.get("real_name", ""),
            id_card=payload.get("id_card", ""),
            company_name=payload.get("company_name", ""),
            credit_code=payload.get("credit_code", ""),
            legal_person=payload.get("legal_person", ""),
            category=payload.get("category", ""),
            markets=payload.get("markets", []),
            experience=payload.get("experience", ""),
            status="pending",
        )
        return success_response({"message": "注册申请已提交，请等待审核"})


class UserRegisterStatusView(APIView):
    """查询注册审核状态"""
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(summary="查询注册审核状态")
    def get(self, request):
        phone = request.query_params.get("phone", "").strip()
        if not phone:
            return error_response(message="phone is required", status_code=400)
        try:
            audit = RegistrationAudit.objects.filter(phone=phone).order_by("-id").first()
            if not audit:
                return success_response({"status": "not_found", "message": "未找到申请记录"})
            return success_response({
                "status": audit.status,
                "reason": audit.reject_reason or "",
                "message": "审核通过，请登录" if audit.status == "approved" else (
                    "审核中，预计1-3个工作日" if audit.status == "pending" else "审核未通过"
                ),
            })
        except Exception:
            return success_response({"status": "not_found", "message": "未找到申请记录"})


class UserTokenRefreshView(APIView):
    """真实业务：刷新 JWT access token。"""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(summary="刷新 Token")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        raw_refresh = payload.get("refresh_token") or payload.get("refresh") or ""
        if not raw_refresh:
            return error_response(message="refresh_token is required", status_code=400, code=400)
        try:
            refresh = RefreshToken(raw_refresh)
        except Exception:
            return error_response(message="invalid refresh token", status_code=401, code=401)
        return success_response(
            data={"access_token": str(refresh.access_token), "refresh_token": str(refresh)},
            code=200,
            status_code=200,
            message="ok",
        )


class DemoAuthLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】用户名密码登录（直通）")
    def post(self, request):
        return Response(
            {
                "code": 200,
                "message": "登录成功",
                "data": {
                    "access_token": "tuoyue_admin_token_2026",
                    "refresh_token": "refresh_token_string",
                },
            },
            status=200,
        )


class DemoAuthMeView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】获取当前用户信息（直通）")
    def get(self, request):
        return Response(
            {
                "code": 200,
                "data": {"username": "Admin", "role": "SuperAdmin", "company": "拓岳科技"},
            },
            status=200,
        )


class DemoAuthRefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】刷新 Token（直通）")
    def post(self, request):
        return Response(
            {
                "code": 200,
                "message": "刷新成功",
                "data": {
                    "access_token": "tuoyue_admin_token_2026_refreshed",
                    "refresh_token": "refresh_token_string_next",
                },
            },
            status=200,
        )


class DemoAuthRegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】注册（直通）")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        return Response(
            {
                "code": 200,
                "message": "注册成功",
                "data": {
                    "user_id": 10001,
                    "username": payload.get("username") or payload.get("phone") or "demo_user",
                    "access_token": "tuoyue_register_token_2026",
                    "refresh_token": "tuoyue_register_refresh_token_2026",
                },
            },
            status=200,
        )


class DemoGoodsListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】跨境商品列表（高质量演示数据）")
    def get(self, request):
        items = [
            {
                "id": 10001,
                "title": "2026新款 智能感应夜灯（Amazon爆款）",
                "platform": "Amazon",
                "sku": "TY-NL-2026-AZ",
                "price": 19.99,
                "currency": "USD",
                "stock": 1280,
                "status": "active",
                "tags": ["Smart Home", "Best Seller", "Low MOQ"],
                "images": [
                    "https://img.tuoyue-tech.shop/demo/goods/nightlight_1.jpg",
                    "https://img.tuoyue-tech.shop/demo/goods/nightlight_2.jpg",
                ],
                "updated_at": "2026-04-26T08:30:00+08:00",
            },
            {
                "id": 10002,
                "title": "Tuoyue Phantom 边缘计算自动化终端 RK3588（TikTok Shop）",
                "platform": "TikTok Shop",
                "sku": "TY-PHANTOM-RK3588",
                "price": 229.0,
                "currency": "USD",
                "stock": 260,
                "status": "active",
                "tags": ["Edge AI", "Industrial", "Creator Favorite"],
                "images": [
                    "https://img.tuoyue-tech.shop/demo/goods/phantom_1.jpg",
                    "https://img.tuoyue-tech.shop/demo/goods/phantom_2.jpg",
                ],
                "updated_at": "2026-04-26T08:30:00+08:00",
            },
            {
                "id": 10003,
                "title": "便携式多功能折叠水杯（1688源头厂货）",
                "platform": "1688",
                "sku": "TY-CUP-FOLD-1688",
                "price": 2.35,
                "currency": "USD",
                "stock": 8600,
                "status": "active",
                "tags": ["Outdoor", "Portable", "Factory Direct"],
                "images": [
                    "https://img.tuoyue-tech.shop/demo/goods/foldcup_1.jpg",
                    "https://img.tuoyue-tech.shop/demo/goods/foldcup_2.jpg",
                ],
                "updated_at": "2026-04-26T08:30:00+08:00",
            },
        ]
        return Response({"code": 200, "data": {"total": 3, "items": items}}, status=200)


class DemoGoodsDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】商品详情（直通）")
    def get(self, request, goods_id: int):
        return Response(
            {
                "code": 200,
                "data": {
                    "id": goods_id,
                    "title": f"演示商品 #{goods_id}",
                    "platform": "Amazon",
                    "sku": f"DEMO-{goods_id}",
                    "price": 19.99,
                    "currency": "USD",
                    "stock": 999,
                    "status": "active",
                },
            },
            status=200,
        )


class DemoGoodsListingSyncView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】商品上架/同步指令下发（直通）")
    def post(self, request):
        return Response({"code": 200, "message": "指令已下发，商品成功同步至目标平台！"}, status=200)


class DemoGoodsBatchListingSyncView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】商品批量上架/同步指令下发（直通）")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        item_count = len(payload.get("items", [])) if isinstance(payload.get("items"), list) else 0
        return Response(
            {
                "code": 200,
                "message": "批量上架指令已下发，任务队列处理中。",
                "data": {"task_id": "batch_listing_20260426_demo", "item_count": item_count},
            },
            status=200,
        )


class DemoAuthSendSmsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】发送短信验证码")
    def post(self, request):
        return Response(
            {
                "code": 200,
                "message": "验证码发送成功",
                "data": {"phone": (request.data or {}).get("phone", "138****8888"), "expires_in": 300},
            },
            status=200,
        )


class DemoAuthVerifySmsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】验证短信验证码")
    def post(self, request):
        return Response({"code": 200, "message": "验证码校验通过", "data": {"verified": True}}, status=200)


class DemoSmsQueryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】短信发送记录查询（直通）")
    def get(self, request):
        return Response(
            {
                "code": 200,
                "message": "ok",
                "data": {
                    "total": 1,
                    "items": [
                        {
                            "phone": "138****8888",
                            "status": "delivered",
                            "sent_at": "2026-04-27T13:00:00+08:00",
                        }
                    ],
                },
            },
            status=200,
        )


class DemoCollectAuthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】采集平台授权接口（直通）")
    def post(self, request, platform: str):
        return Response(
            {
                "code": 200,
                "message": "授权操作成功",
                "data": {"platform": platform, "authorized": True},
            },
            status=200,
        )

    @extend_schema(summary="【演示】采集平台授权查询/回调（直通）")
    def get(self, request, platform: str):
        return Response(
            {
                "code": 200,
                "message": "ok",
                "data": {"platform": platform, "authorized": True, "account": f"{platform}_demo_account"},
            },
            status=200,
        )


class DemoCollectTaskView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】采集任务接口（直通）")
    def post(self, request, task_id: int | None = None):
        return Response(
            {
                "code": 200,
                "message": "任务操作成功",
                "data": {"task_id": task_id or 1001, "status": "queued"},
            },
            status=200,
        )

    @extend_schema(summary="【演示】采集任务查询（直通）")
    def get(self, request, task_id: int | None = None):
        if task_id:
            return Response(
                {
                    "code": 200,
                    "message": "ok",
                    "data": {"task_id": task_id, "status": "running"},
                },
                status=200,
            )
        return Response(
            {
                "code": 200,
                "message": "ok",
                "data": {"total": 1, "items": [{"task_id": 1001, "status": "running"}]},
            },
            status=200,
        )

    def delete(self, request, task_id: int):
        return Response({"code": 200, "message": "任务删除成功", "data": {"task_id": task_id}}, status=200)


class DemoAiExtendedView(APIView):
    """
    AI 对话接口（支持拓跃AI）
    任何异常都必须兜底，严禁向前端抛 502
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】AI 对话接口（拓跃AI）")
    def post(self, request):
        # 拓跃AI配置
        target_url = "http://api.tuoyue-tech.shop/v1/chat/completions"
        api_key = getattr(settings, "TUOYUE_NEW_API_AUTHORIZATION", "")
        
        payload = request.data if isinstance(request.data, dict) else {}
        messages = payload.get("messages", [])
        system_prompt = payload.get("system_prompt", "")
        
        # 构建拓跃AI请求体
        tuoyue_payload = {
            "model": "deepseek-v4-flash",
            "messages": messages if messages else [
                {"role": "system", "content": system_prompt or "你是小辽，跨境电商ERP的AI助手。"},
                {"role": "user", "content": "你好"}
            ],
            "temperature": payload.get("temperature", 0.7),
            "max_tokens": payload.get("max_tokens", 800),
            "stream": False
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        try:
            # 注意：verify=False 仅用于开发测试，生产环境应启用SSL验证
            resp = requests.post(target_url, json=tuoyue_payload, headers=headers, timeout=30, verify=False)
            if resp.status_code >= 500:
                return Response({
                    "code": 200,
                    "message": "fallback",
                    "data": {"reply": "小辽暂时无法连接到AI服务，请稍后再试。"}
                }, status=200)
            
            # 解析拓跃AI响应
            try:
                data = resp.json()
                # 提取AI回复内容
                if "choices" in data and len(data["choices"]) > 0:
                    reply = data["choices"][0].get("message", {}).get("content", "")
                else:
                    reply = data.get("text", "抱歉，AI没有返回有效内容。")
                
                return Response({
                    "code": 200,
                    "message": "success",
                    "data": {"reply": reply}
                }, status=200)
            except Exception as e:
                return Response({
                    "code": 200,
                    "message": "parse_error",
                    "data": {"reply": "AI响应解析失败，请重试。"}
                }, status=200)
                
        except Exception as e:
            # 兜底响应
            return Response({
                "code": 200,
                "message": "error",
                "data": {"reply": "小辽暂时无法连接到AI服务，请稍后再试。"}
            }, status=200)


class DemoOrdersView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, order_id: int | None = None):
        if order_id is not None:
            return Response({"code": 200, "data": {"id": order_id, "status": "pending"}}, status=200)
        return Response({"code": 200, "data": {"total": 1, "items": [{"id": 1, "status": "pending"}]}}, status=200)

    def post(self, request, order_id: int | None = None, action: str | None = None):
        return Response(
            {"code": 200, "message": "订单操作成功", "data": {"id": order_id or 1, "action": action or "create"}},
            status=200,
        )


class DemoOrdersStatsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"code": 200, "data": {"total": 1, "pending": 1, "shipped": 0}}, status=200)


class DemoInventoryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, sku: str | None = None):
        if sku:
            return Response({"code": 200, "data": {"sku": sku, "stock": 100}}, status=200)
        return Response({"code": 200, "data": {"total": 1, "items": [{"sku": "DEMO-SKU", "stock": 100}]}}, status=200)

    def post(self, request):
        return Response({"code": 200, "message": "库存操作成功", "data": {"ok": True}}, status=200)


class DemoLogisticsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, waybill: str | None = None):
        if waybill:
            return Response({"code": 200, "data": {"waybill": waybill, "status": "in_transit"}}, status=200)
        return Response({"code": 200, "data": {"total": 1, "items": [{"waybill": "WB001", "status": "in_transit"}]}}, status=200)

    def post(self, request):
        return Response({"code": 200, "message": "物流操作成功", "data": {"ok": True}}, status=200)


class DemoCollect1688SingleView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】1688 单链接采集")
    def post(self, request):
        return Response(
            {
                "code": 200,
                "message": "采集成功",
                "data": {
                    "task_id": "collect_1688_single_demo_001",
                    "status": "completed",
                    "items": [{"title": "1688示例商品A", "source": "1688", "price": 3.99}],
                },
            },
            status=200,
        )


class DemoCollect1688BatchView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】1688 批量采集")
    def post(self, request):
        return Response(
            {
                "code": 200,
                "message": "批量采集任务已创建",
                "data": {"task_id": "collect_1688_batch_demo_001", "status": "queued"},
            },
            status=200,
        )


def _ai_fallback_copy() -> Dict[str, Any]:
    return {
        "title": "💡 Premium Smart Product | High-Quality, Minimalist Design",
        "description": (
            "✨ Upgrade your daily life with a sleek, reliable product built for performance. "
            "Designed for modern users, easy to use, and perfect for gifting."
        ),
        "bullets": [
            "🚀 Fast, dependable, and built to last",
            "🎯 Clean look with practical features",
            "🛡️ Quality materials, worry-free use",
            "📦 Ready for cross-border fulfillment",
        ],
    }


def _tuoyue_ai_call(messages: list, temperature: float = 0.7, max_tokens: int = 800, model: str = "deepseek-v4-flash") -> str:
    """统一拓岳AI调用，失败抛异常；支持代理"""
    target_url = "http://api.tuoyue-tech.shop/v1/chat/completions"
    api_key = os.getenv("TUOYUE_NEW_API_AUTHORIZATION", "") or getattr(settings, "TUOYUE_NEW_API_AUTHORIZATION", "")
    if not api_key:
        raise ValueError("AI API key not configured")

    tuoyue_payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # 代理支持：优先使用 HTTPS_PROXY 环境变量
    proxies = {}
    proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or ""
    if proxy_url:
        proxies = {"https": proxy_url}

    resp = requests.post(
        target_url, json=tuoyue_payload, headers=headers,
        timeout=30, verify=False, proxies=proxies if proxies else None,
    )
    if resp.status_code >= 500:
        raise RuntimeError(f"AI service returned {resp.status_code}")
    data = resp.json()
    if "choices" in data and len(data["choices"]) > 0:
        return data["choices"][0].get("message", {}).get("content", "")
    return data.get("text", "")


class AiGenerateTitleView(APIView):
    """AI 生成商品标题（真实拓岳AI）"""
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="AI 生成商品标题")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        name = payload.get("name") or payload.get("product_name") or ""
        category = payload.get("category") or ""
        material = payload.get("material") or ""
        style = payload.get("style") or ""
        features = payload.get("features") or ""
        target_market = payload.get("target_market") or "跨境电商通用"

        if not name:
            return error_response(message="name is required", status_code=400)

        system_prompt = (
            "你是一位专业的跨境电商商品标题优化专家，帮助卖家生成符合 TikTok Shop / Amazon / eBay 等平台搜索算法的商品标题。\n"
            "规则：1. 标题长度控制在80-120字符内 2. 必须包含：核心关键词 + 产品名 + 材质/规格 + 卖点 "
            "3. 标题开头优先放高搜索量关键词 4. 适当使用括号标注节日/促销场景 5. 不要堆砌关键词，保持自然可读。"
        )
        user_prompt = (
            f"请为以下商品生成5个高质量英文标题（每行一个）：\n"
            f"商品：{name}  品类：{category}  材质：{material}  风格：{style}  特点：{features}  目标市场：{target_market}"
        )

        try:
            result = _tuoyue_ai_call(
                [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.8,
                max_tokens=300,
            )
            titles = [t.strip().lstrip("0123456789.-、* ") for t in result.split("\n") if t.strip()]
            return success_response({"title": "\n".join(titles)})
        except Exception as exc:
            return error_response(message=str(exc), status_code=502)


class AiGenerateDescriptionView(APIView):
    """AI 生成商品描述（真实拓岳AI）"""
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="AI 生成商品描述")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        name = payload.get("name") or payload.get("product_name") or ""
        category = payload.get("category") or ""
        material = payload.get("material") or ""
        features = payload.get("features") or ""
        specs = payload.get("specs") or ""
        target_market = payload.get("target_market") or "跨境电商通用"

        if not name:
            return error_response(message="name is required", status_code=400)

        system_prompt = (
            "你是一位专业的跨境电商商品描述撰写专家。请使用 Markdown 格式输出，结构：产品特点→产品参数→适用范围→温馨提示。"
            "产品特点用 emoji 列表突出，强调差异化卖点。"
        )
        user_prompt = (
            f"请为以下商品生成英文描述：\n"
            f"商品：{name}  品类：{category}  材质：{material}  特点：{features}  规格：{specs}  目标市场：{target_market}"
        )

        try:
            description = _tuoyue_ai_call(
                [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.75,
                max_tokens=800,
            )
            return success_response({"description": description})
        except Exception as exc:
            return error_response(message=str(exc), status_code=502)


class AiGenerateFeaturesView(APIView):
    """AI 生成商品卖点（真实拓岳AI）"""
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="AI 生成商品卖点")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        name = payload.get("name") or payload.get("product_name") or ""
        category = payload.get("category") or ""
        material = payload.get("material") or ""
        style = payload.get("style") or ""

        if not name:
            return error_response(message="name is required", status_code=400)

        system_prompt = (
            "你是一位跨境电商选品专家。请为给定的商品输出5条核心卖点，每条一行，使用 emoji 开头，"
            "包含材质、功能、设计、使用场景、物流优势等角度。"
        )
        user_prompt = f"商品：{name}  品类：{category}  材质：{material}  风格：{style}"

        try:
            result = _tuoyue_ai_call(
                [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.8,
                max_tokens=300,
            )
            features = [f.strip().lstrip("0123456789.-、* ") for f in result.split("\n") if f.strip()]
            return success_response({"features": features})
        except Exception as exc:
            return error_response(message=str(exc), status_code=502)


class AiChatView(APIView):
    """AI 对话（真实拓岳AI）"""
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="AI 对话接口")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        messages = payload.get("messages", [])
        system_prompt = payload.get("system_prompt", "")

        if not messages:
            return error_response(message="messages is required", status_code=400)

        try:
            reply = _tuoyue_ai_call(
                messages if not system_prompt else [{"role": "system", "content": system_prompt}] + messages,
                temperature=payload.get("temperature", 0.7),
                max_tokens=payload.get("max_tokens", 800),
            )
            return success_response({"reply": reply})
        except Exception as exc:
            return error_response(message=str(exc), status_code=502)


class AiImageGenerateView(APIView):
    """AI 文生图（拓悦AI — 文本增强 + Markdown图片链接解析）"""
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="AI 文生图")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        prompt = payload.get("prompt", "")

        if not prompt:
            return error_response(message="prompt is required", status_code=400)

        try:
            # 使用文本模型生成增强的图片描述（更实用的跨境电商场景）
            enhanced = _tuoyue_ai_call(
                [{"role": "user", "content": (
                    f"你是一个跨境电商商品摄影专家。请根据以下信息生成3条商品主图的详细拍摄描述（每行一条），"
                    f"包含：构图、背景、灯光、角度、风格。描述越详细越好：\n\n产品信息：{prompt}"
                )}],
                temperature=0.9,
                max_tokens=900,
            )

            # 提取 Markdown 图片链接（如果模型返回了）
            import re
            urls = re.findall(r'!\[.*?\]\((https?://[^\s)]+)\)', enhanced) or re.findall(r'https?://[^\s<>"]+\.(?:png|jpg|jpeg|webp|gif)', enhanced)
            image_url = urls[0] if urls else ""

            # 解析提示词（处理 \\n、\\r\\n 和数字编号开头）
            prompt_lines = []
            for line in re.split(r'[\r\n]+', enhanced):
                line = line.strip()
                if not line:
                    continue
                # 去掉数字编号前缀如 "1. " "2、"
                line = re.sub(r'^[\d]+[\.\、\s]+', '', line).strip()
                if len(line) > 5:
                    prompt_lines.append(line)

            return success_response({
                "image_url": image_url,
                "image_base64": enhanced,
                "prompts": prompt_lines if prompt_lines else [enhanced],
            })
        except Exception as exc:
            return error_response(message=f"image generation failed: {exc}", status_code=502)


class AiImageEditView(APIView):
    """AI 图生图（真实拓岳AI）"""
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="AI 图生图")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        prompt = payload.get("prompt", "")
        image_base64 = payload.get("image_base64", "")

        if not prompt:
            return error_response(message="prompt is required", status_code=400)

        try:
            messages = []
            if image_base64:
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"请根据以下指令修改图片：{prompt}"},
                        {"type": "image_url", "image_url": {"url": image_base64}},
                    ],
                }]
            else:
                messages = [{"role": "user", "content": f"请根据指令生成图片：{prompt}"}]

            tuoyue_payload = {
                "model": "gemini-2.0-flash-exp-image-generation",
                "messages": messages,
                "temperature": 0.8,
                "stream": False,
            }
            api_key = getattr(settings, "TUOYUE_NEW_API_AUTHORIZATION", "")
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
            resp = requests.post(
                "http://api.tuoyue-tech.shop/v1/chat/completions",
                json=tuoyue_payload, headers=headers, timeout=120, verify=False,
            )
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return success_response({"image_url": "", "image_base64": content[:500] if content else ""})
        except Exception as exc:
            return error_response(message=f"image edit failed: {exc}", status_code=502)


class AiTranslateView(APIView):
    """AI 翻译（真实拓岳AI）"""
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="AI 翻译")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        text = payload.get("text", "")
        target_lang = payload.get("target_lang", "English")

        if not text:
            return error_response(message="text is required", status_code=400)

        system_prompt = f"你是一位专业翻译专家。请将以下文本翻译成{target_lang}，直接输出翻译结果，不要添加解释。"
        try:
            translation = _tuoyue_ai_call(
                [{"role": "system", "content": system_prompt}, {"role": "user", "content": text}],
                temperature=0.3,
                max_tokens=2000,
            )
            return success_response({"translation": translation.strip()})
        except Exception as exc:
            return error_response(message=str(exc), status_code=502)


class AiRefineDescriptionView(APIView):
    """AI 描述优化（真实拓岳AI）"""
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="AI 改写/优化描述")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        original_desc = payload.get("original_desc", "")
        adjustment = payload.get("adjustment", "")

        if not original_desc:
            return error_response(message="original_desc is required", status_code=400)
        if not adjustment:
            return error_response(message="adjustment is required", status_code=400)

        system_prompt = (
            "你是一位跨境电商文案优化专家。请根据要求改写商品描述，保持 bullet point 格式，直接输出改写后的内容。"
        )
        user_prompt = f"原始描述：\n{original_desc}\n\n改写要求：{adjustment}"

        try:
            refined = _tuoyue_ai_call(
                [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.7,
                max_tokens=600,
            )
            return success_response({"description": refined.strip()})
        except Exception as exc:
            return error_response(message=str(exc), status_code=502)


class AiProxyView(APIView):
    """
    前端 AI 文案请求转发到拓岳 New API。
    任何异常都必须兜底为演示文案，严禁向前端抛 502。
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="AI 中枢代理转发（失败兜底，永不 502）")
    def post(self, request):
        # region agent log
        try:
            with open("debug-12656f.log", "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "sessionId": "12656f",
                            "runId": "pre-fix",
                            "hypothesisId": "H3",
                            "location": "apps/core/views.py:AiProxyView.post",
                            "message": "ai proxy request enter",
                            "data": {"path": request.path},
                            "timestamp": int(time.time() * 1000),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except Exception:
            pass
        # endregion
        target_url = "http://api.tuoyue-tech.shop"
        api_key = getattr(settings, "TUOYUE_NEW_API_AUTHORIZATION", "")
        payload = request.data if isinstance(request.data, dict) else {}
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = api_key

        try:
            resp = requests.post(target_url, json=payload, headers=headers, timeout=10)
            # region agent log
            try:
                with open("debug-12656f.log", "a", encoding="utf-8") as f:
                    f.write(
                        json.dumps(
                            {
                                "sessionId": "12656f",
                                "runId": "pre-fix",
                                "hypothesisId": "H3",
                                "location": "apps/core/views.py:AiProxyView.post",
                                "message": "ai proxy upstream response",
                                "data": {"status_code": resp.status_code},
                                "timestamp": int(time.time() * 1000),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            except Exception:
                pass
            # endregion
            if resp.status_code >= 500:
                return Response({"code": 200, "data": _ai_fallback_copy(), "message": "fallback"}, status=200)
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            return Response({"code": 200, "data": data, "message": "success"}, status=200)
        except Exception:
            return Response({"code": 200, "data": _ai_fallback_copy(), "message": "fallback"}, status=200)


class DemoAiGenerateTitleView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】AI 生成标题")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        name = payload.get("name") or payload.get("product_name") or "Smart Product"
        category = payload.get("category") or "Home"
        title = f"💡 {name} | Premium {category} Choice for Global Market 2026"
        return Response({"code": 200, "data": {"title": title}}, status=200)


class DemoAiGenerateDescriptionView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】AI 生成描述")
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        name = payload.get("name") or payload.get("product_name") or "This product"
        description = (
            f"✨ {name} is designed for modern cross-border e-commerce sellers. "
            "It combines reliable quality, attractive appearance, and practical features "
            "to help boost conversion and customer satisfaction."
        )
        return Response({"code": 200, "data": {"description": description}}, status=200)


class DemoAiGenerateFeaturesView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="【演示】AI 生成卖点")
    def post(self, request):
        return Response(
            {
                "code": 200,
                "data": {
                    "features": [
                        "🚀 Fast-selling design optimized for global marketplaces",
                        "🛡️ Durable materials with strict quality control",
                        "📦 Cross-border friendly packaging and fulfillment readiness",
                        "💰 Competitive landed cost with strong profit potential",
                    ]
                },
            },
            status=200,
        )


class CaptchaChallengeView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="获取图形验证码（人机挑战）")
    def get(self, request):
        return success_response(data=create_captcha_challenge())


class SmsCodeSendView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="发送短信验证码")
    def post(self, request):
        serializer = SmsCodeSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        country_code = serializer.validated_data.get("country_code", "86")
        full_phone = f"+{country_code}{phone}"
        voice = serializer.validated_data.get("voice", False)
        captcha_err = validate_captcha_if_required(
            serializer.validated_data.get("captcha_id") or None,
            serializer.validated_data.get("captcha_answer"),
        )
        if captcha_err:
            return error_response(message=captcha_err, status_code=400)

        global_limit_err = check_and_incr_global_sms_limit()
        if global_limit_err:
            return error_response(message=global_limit_err, status_code=429, code=429)

        client_ip = get_client_ip(request.META)
        limit_err = check_send_rate_limits(full_phone, client_ip)
        if limit_err:
            return error_response(
                message=limit_err,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                code=429,
            )

        code = generate_sms_code()
        message_type = "voice" if voice else "sms"
        try:
            send_result = send_sms_with_failover.delay(phone=full_phone, code=code, message_type=message_type).get(timeout=15)
        except SmsSendError as exc:
            error_code = getattr(exc, "code", "SMS_SEND_FAILED")
            return error_response(
                message=str(exc),
                status_code=400,
                code=400,
                data={"error_code": error_code, "detail": str(exc)},
            )
        except Exception as exc:
            return error_response(
                message="短信服务暂时不可用，请稍后重试",
                status_code=400,
                code=400,
                data={"error_code": "DISPATCH_ERROR", "detail": str(exc)},
            )

        store_sms_code(full_phone, code)
        record_send_success(full_phone, client_ip)
        ttl = int(getattr(settings, "SMS_CODE_TTL_SECONDS", 300))
        is_dev = send_result.get("is_development", False)
        return success_response(
            {
                "phone": full_phone,
                "expires_in": ttl,
                "provider": send_result.get("provider"),
                "biz_id": send_result.get("biz_id"),
                "message_type": message_type,
                "code": code if settings.DEBUG else None,
                "is_development": is_dev,
                "dev_notice": "当前为开发/测试通道，验证码不会真实发送到手机" if is_dev else None,
            }
        )


class SmsCodeVerifyView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="校验短信验证码")
    def post(self, request):
        serializer = SmsCodeVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]
        ok, err_msg, status_code = verify_sms_code_with_lua(phone, code)
        if not ok:
            return error_response(message=err_msg or "error", status_code=status_code, code=status_code)
        return success_response({"verified": True, "phone": phone})


def _mask_mobile(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 7:
        return phone
    return f"{digits[:3]}****{digits[-4:]}"


class MobileAuthLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="手机号验证码登录/注册（合并）")
    def post(self, request):
        serializer = MobileAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data["agreed_privacy"]:
            return error_response(message="必须同意隐私协议", status_code=400)

        country_code = serializer.validated_data["country_code"]
        mobile = serializer.validated_data["mobile"]
        full_phone = f"+{country_code}{mobile}"
        device_id = request.headers.get("X-Device-ID", "").strip()
        if device_id and is_device_blacklisted(device_id):
            return error_response(message="设备已被风控拦截", status_code=403, code=403)

        ok, err_msg, status_code = verify_sms_code_with_lua(full_phone, serializer.validated_data["code"])
        if not ok:
            return error_response(message=err_msg or "error", status_code=status_code, code=status_code)

        User = get_user_model()
        with transaction.atomic():
            binding = UserPhoneBinding.objects.select_for_update().filter(
                country_code=country_code,
                phone_number=mobile,
            ).first()
            created = False
            if binding:
                user = binding.user
            else:
                ts = int(time.time())
                username = f"u_{country_code}_{mobile}_{ts}"
                user = User.objects.create_user(username=username)
                UserPhoneBinding.objects.create(user=user, country_code=country_code, phone_number=mobile, is_primary=True)
                created = True

            if created and getattr(settings, "RBAC_ENFORCE", False):
                # 为新用户自动分配业务集成角色，确保可访问业务 API
                from django.contrib.auth.models import Group
                integrator_groups = getattr(settings, "RBAC_API_INTEGRATOR_GROUPS", ["api_integrator"])
                for group_name in integrator_groups:
                    group, _ = Group.objects.get_or_create(name=group_name)
                    user.groups.add(group)

            if device_id:
                DevicePhoneRelation.objects.create(device_id=device_id, phone=full_phone)
                blacklisted = register_device_phone_attempt(device_id, full_phone)
                if blacklisted:
                    return error_response(message="设备触发风控限制", status_code=403, code=403)

        token = RefreshToken.for_user(user)
        return success_response(
            {
                "created": created,
                "access": str(token.access_token),
                "refresh": str(token),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "mobile": _mask_mobile(full_phone),
                    "country_code": country_code,
                },
            }
        )


class UserAccountDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="账号注销（软删除）")
    def delete(self, request):
        serializer = AccountDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        binding = UserPhoneBinding.objects.filter(user=user).first()
        if not binding:
            return error_response(message="未绑定手机号", status_code=400)
        full_phone = f"+{binding.country_code}{binding.phone_number}"
        ok, err_msg, status_code = verify_sms_code_with_lua(full_phone, serializer.validated_data["code"])
        if not ok:
            return error_response(message=err_msg or "验证码错误", status_code=status_code, code=status_code)

        old_username = user.username
        anonymized = f"{old_username}__deleted__{int(time.time())}"
        with transaction.atomic():
            user.is_active = False
            user.username = anonymized[:180]
            user.save(update_fields=["is_active", "username"])
            binding.phone_number = f"{binding.phone_number}__{int(time.time())}"[:20]
            binding.save(update_fields=["phone_number", "updated_at"])
            AccountDeletionLog.objects.create(
                user=user,
                original_username=old_username,
                anonymized_username=user.username,
                reason=serializer.validated_data.get("reason", ""),
            )
        return success_response({"deleted": True})


class PhoneRebindAppealCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="手机号换绑申诉")
    def post(self, request):
        serializer = PhoneRebindAppealSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(user=request.user)
        return success_response(PhoneRebindAppealSerializer(obj).data, status_code=201)


class SmsChannelStatsView(APIView):
    permission_classes = [IsAuthenticated, IsOpsAdmin]

    @extend_schema(summary="短信通道到达率统计")
    def get(self, request):
        serializer = SmsChannelStatsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        days = serializer.validated_data["days"]
        since = timezone.now() - timedelta(days=days)
        queryset = SmsDispatchLog.objects.filter(requested_at__gte=since)
        stats = {}
        for row in queryset:
            p = row.provider
            stats.setdefault(p, {"total": 0, "delivered": 0, "failed": 0})
            stats[p]["total"] += 1
            if row.status == SmsDispatchLog.STATUS_DELIVERED:
                stats[p]["delivered"] += 1
            elif row.status == SmsDispatchLog.STATUS_FAILED:
                stats[p]["failed"] += 1
        for provider, payload in stats.items():
            total = payload["total"] or 1
            payload["reach_rate"] = round(payload["delivered"] / total, 4)
        return success_response({"days": days, "channels": stats})


class GoodsListCreateView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="商品列表（分页/搜索）")
    def get(self, request):
        queryset = Product.objects.all().order_by("-updated_at")
        keyword = request.query_params.get("keyword", "").strip()
        platform = request.query_params.get("platform", "").strip()
        if keyword:
            queryset = queryset.filter(title__icontains=keyword)
        if platform:
            queryset = queryset.filter(platform=platform)

        page = int(request.query_params.get("page", 1))
        page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 200)
        paginator = Paginator(queryset, page_size)
        current_page = paginator.get_page(page)
        data = ProductSerializer(current_page.object_list, many=True).data
        return success_response(
            {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "page": current_page.number,
                "page_size": page_size,
                "results": data,
            }
        )

    @extend_schema(summary="创建商品")
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return success_response(ProductSerializer(obj).data, status_code=201)


class GoodsDetailView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="商品详情")
    def get(self, request, goods_id):
        obj = get_object_or_404(Product, id=goods_id)
        return success_response(ProductSerializer(obj).data)

    @extend_schema(summary="更新商品")
    def put(self, request, goods_id):
        obj = get_object_or_404(Product, id=goods_id)
        serializer = ProductSerializer(instance=obj, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return success_response(ProductSerializer(obj).data)

    @extend_schema(summary="删除商品")
    def delete(self, request, goods_id):
        obj = get_object_or_404(Product, id=goods_id)
        obj.delete()
        return success_response({"deleted": True, "id": goods_id})


class ShopListView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="店铺列表")
    def get(self, request):
        shops = Shop.objects.all().order_by("-updated_at")[:200]
        return success_response(ShopSerializer(shops, many=True).data)


class InventoryAlertsView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="库存预警")
    def get(self, request):
        threshold = int(request.query_params.get("threshold", 10))
        queryset = Product.objects.filter(stock__lte=threshold).order_by("stock", "-updated_at")[:500]
        return success_response(
            {
                "threshold": threshold,
                "count": queryset.count(),
                "results": ProductSerializer(queryset, many=True).data,
            }
        )


class InventoryLogsView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="库存同步日志")
    def get(self, request):
        logs = InventorySyncLog.objects.all().order_by("-created_at")[:200]
        return success_response(InventorySyncLogSerializer(logs, many=True).data)


class InventorySyncView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="手动触发库存同步")
    def post(self, request):
        scheduled_inventory_sync.delay()
        return success_response({"queued": True})


class OrdersListView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="订单列表")
    def get(self, request):
        queryset = Order.objects.all().order_by("-created_at")
        status_value = request.query_params.get("status", "").strip()
        if status_value:
            queryset = queryset.filter(status=status_value)
        page = int(request.query_params.get("page", 1))
        page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 200)
        paginator = Paginator(queryset, page_size)
        current_page = paginator.get_page(page)
        data = OrderSerializer(current_page.object_list, many=True, context={"request": request}).data
        return success_response(
            {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "page": current_page.number,
                "page_size": page_size,
                "results": data,
            }
        )


class OrderStatusUpdateView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="更新订单状态")
    def put(self, request, order_id):
        obj = get_object_or_404(Order, id=order_id)
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj.status = serializer.validated_data["status"]
        obj.save(update_fields=["status", "updated_at"])
        return success_response(OrderSerializer(obj).data)


class OrderAddressUpdateView(APIView):
    permission_classes = [IsAuthenticated, HasOrderEditPermission]

    @extend_schema(summary="手动修改订单地址（需 order_edit 权限）")
    def put(self, request, order_id):
        obj = get_object_or_404(Order, id=order_id)
        serializer = OrderAddressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        update_fields = []
        for field in ("recipient_name", "recipient_phone", "shipping_address"):
            if field in payload:
                setattr(obj, field, payload[field])
                update_fields.append(field)
        if not update_fields:
            return error_response(message="至少传入一个地址字段", status_code=400)
        obj.save(update_fields=update_fields + ["updated_at"])
        return success_response(OrderSerializer(obj, context={"request": request}).data)


class OrdersExportView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="导出订单")
    def get(self, request):
        queryset = Order.objects.all().order_by("-created_at")[:5000]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="orders_export.csv"'
        writer = csv.writer(response)
        writer.writerow(["id", "platform", "order_no", "buyer_name", "status", "amount", "created_at"])
        for row in queryset:
            writer.writerow([row.id, row.platform, row.order_no, row.buyer_name, row.status, row.amount, row.created_at])
        return response


class OrdersStatsView(APIView):
    """订单状态统计"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="订单各状态计数")
    def get(self, request):
        from django.db.models import Count
        counts = dict(Order.objects.values("status").annotate(cnt=Count("id")).values_list("status", "cnt"))
        return success_response({
            "pending": counts.get("pending", 0),
            "paid": counts.get("paid", 0),
            "shipped": counts.get("shipped", 0),
            "signed": counts.get("signed", 0),
            "completed": counts.get("completed", 0),
            "cancelled": counts.get("cancelled", 0),
            "exception": counts.get("exception", 0),
            "total": sum(counts.values()),
        })


class OrdersDetailView(APIView):
    """订单详情"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="获取订单详情")
    def get(self, request, order_id):
        obj = get_object_or_404(Order, id=order_id)
        return success_response(OrderSerializer(obj, context={"request": request}).data)


class OrderActionView(APIView):
    """订单操作：确认/发货/取消"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="订单操作确认/发货/取消")
    def post(self, request, order_id):
        obj = get_object_or_404(Order, id=order_id)
        path = request.path.rstrip("/")
        if path.endswith("/confirm"):
            if obj.status == Order.STATUS_PENDING:
                obj.status = Order.STATUS_PAID
        elif path.endswith("/ship"):
            if obj.status == Order.STATUS_PAID:
                obj.status = Order.STATUS_SHIPPED
        elif path.endswith("/cancel"):
            if obj.status not in (Order.STATUS_COMPLETED, Order.STATUS_CANCELLED):
                obj.status = Order.STATUS_CANCELLED
        else:
            return error_response(message="未知操作", status_code=400)
        obj.save(update_fields=["status", "updated_at"])
        return success_response(OrderSerializer(obj, context={"request": request}).data)


class LogisticsShipmentsView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="物流列表")
    def get(self, request):
        rows = LogisticsShipment.objects.select_related("order").all().order_by("-updated_at")[:500]
        return success_response(LogisticsShipmentSerializer(rows, many=True).data)


class LogisticsTrackView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="物流轨迹查询")
    def get(self, request, waybill):
        row = get_object_or_404(LogisticsShipment, waybill_no=waybill)
        client = get_logistics_aggregator_client()
        events = client.fetch_tracking_events(waybill_no=row.waybill_no, carrier=row.carrier)
        if events:
            latest = events[0]
            latest_status = str(latest.get("status") or "").strip()
            row.latest_event = latest_status or row.latest_event
            delivered_markers = {"投递成功", "已签收", "signed", "delivered"}
            normalized_marker = latest_status.lower()
            is_delivered = latest_status in delivered_markers or normalized_marker in delivered_markers
            if is_delivered:
                row.status = LogisticsShipment.STATUS_DELIVERED
                row.order.status = Order.STATUS_SIGNED
                row.order.save(update_fields=["status", "updated_at"])
                row.save(update_fields=["latest_event", "status", "updated_at"])
            else:
                row.save(update_fields=["latest_event", "updated_at"])
        else:
            events = [
                {
                    "time": row.updated_at.date().isoformat(),
                    "status": row.latest_event or "运输中",
                    "location": "",
                }
            ]
        # 统一轨迹格式：[{"time":"2026-04-16","status":"已揽收","location":"深圳"}]
        data = {"waybill_no": row.waybill_no, "carrier": row.carrier, "status": row.status, "tracks": events}
        return success_response(data)


class LogisticsWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="物流平台 Webhook 回调")
    def post(self, request):
        expected_token = (getattr(settings, "LOGISTICS_WEBHOOK_TOKEN", "") or "").strip()
        provided_token = (request.headers.get("X-Webhook-Token", "") or "").strip()
        if expected_token and expected_token != provided_token:
            return error_response(message="invalid webhook token", status_code=403, code=403)

        payload = request.data if isinstance(request.data, dict) else {}

        def _pick_waybill(data: dict) -> str:
            for key in ("waybill_no", "tracking_no", "trackingNo", "tracking_number", "number"):
                val = str(data.get(key) or "").strip()
                if val:
                    return val
            data_list = data.get("data")
            if isinstance(data_list, list) and data_list:
                item = data_list[0] if isinstance(data_list[0], dict) else {}
                for key in ("waybill_no", "tracking_no", "trackingNo", "tracking_number", "number"):
                    val = str(item.get(key) or "").strip()
                    if val:
                        return val
            return ""

        waybill_no = _pick_waybill(payload)
        if not waybill_no:
            return error_response(message="waybill_no is required", status_code=400)
        try:
            shipment = LogisticsShipment.objects.select_related("order").get(waybill_no=waybill_no)
        except LogisticsShipment.DoesNotExist:
            return success_response({"ok": True, "ignored": True, "reason": "unknown waybill_no"})

        def _normalize_events(data: dict):
            if isinstance(data.get("events"), list):
                return [e for e in data.get("events") if isinstance(e, dict)]
            data_list = data.get("data")
            if isinstance(data_list, list) and data_list:
                item = data_list[0] if isinstance(data_list[0], dict) else {}
                track_info = item.get("track_info") if isinstance(item.get("track_info"), dict) else {}
                tracking = track_info.get("tracking")
                if isinstance(tracking, list):
                    normalized = []
                    for e in tracking:
                        if not isinstance(e, dict):
                            continue
                        normalized.append(
                            {
                                "time": e.get("track_date") or e.get("time"),
                                "status": e.get("status_description") or e.get("description") or e.get("status"),
                                "location": e.get("location") or "",
                            }
                        )
                    return normalized
            top = {
                "time": data.get("time"),
                "status": data.get("status"),
                "location": data.get("location"),
            }
            return [top]

        events = _normalize_events(payload)
        top_event = events[0] if events else {}
        callback_status = str(top_event.get("status") or "").strip()
        location = str(top_event.get("location") or "").strip()
        event_time_raw = str(top_event.get("time") or timezone.now().isoformat()).strip()

        def _parse_event_time(value: str):
            v = (value or "").strip()
            if not v:
                return None
            dt = parse_datetime(v)
            if dt:
                return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
            d = parse_date(v[:10])
            if d:
                return timezone.make_aware(timezone.datetime(d.year, d.month, d.day, 0, 0, 0))
            return None

        delivered_markers = {"投递成功", "已签收", "signed", "delivered"}
        exception_markers = {"异常", "exception", "退回", "failed", "undelivered"}
        normalized_marker = callback_status.lower()
        is_delivered = callback_status in delivered_markers or normalized_marker in delivered_markers
        is_exception = callback_status in exception_markers or normalized_marker in exception_markers

        with transaction.atomic():
            for e in events[:50]:
                status_text = str(e.get("status") or "").strip()
                location_text = str(e.get("location") or "").strip()
                time_raw = str(e.get("time") or "").strip() or event_time_raw
                LogisticsTrackingEvent.objects.get_or_create(
                    shipment=shipment,
                    event_time_raw=time_raw[:64],
                    status=status_text[:255],
                    location=location_text[:255],
                    source="webhook",
                    defaults={
                        "event_time": _parse_event_time(time_raw),
                        "raw_payload": e if isinstance(e, dict) else {},
                    },
                )

            shipment.latest_event = f"{event_time_raw[:32]} {callback_status} {location}".strip()
            if is_delivered:
                shipment.status = LogisticsShipment.STATUS_DELIVERED
            elif is_exception:
                shipment.status = LogisticsShipment.STATUS_EXCEPTION
            else:
                shipment.status = LogisticsShipment.STATUS_IN_TRANSIT
            shipment.save(update_fields=["latest_event", "status", "updated_at"])

            if is_delivered and shipment.order.status != Order.STATUS_SIGNED:
                shipment.order.status = Order.STATUS_SIGNED
                shipment.order.save(update_fields=["status", "updated_at"])

        return success_response({"ok": True, "delivered": is_delivered, "exception": is_exception, "order_id": shipment.order_id})


class FreightEstimateView(APIView):
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="物流运费预估（体积重+目的地）")
    def post(self, request):
        serializer = FreightEstimateQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        divisor = int(getattr(settings, "LOGISTICS_VOLUME_DIVISOR", 6000))
        volume_weight = (payload["length_cm"] * payload["width_cm"] * payload["height_cm"]) / divisor
        chargeable_weight = max(payload["actual_weight_kg"], volume_weight)
        destination_country = str(payload["destination_country"]).upper()
        carrier = (payload.get("carrier") or "").strip()

        queryset = LogisticsRateCard.objects.filter(destination_country=destination_country, is_active=True)
        if carrier:
            queryset = queryset.filter(carrier=carrier)
        cards = list(queryset.order_by("carrier"))
        quotes = get_logistics_aggregator_client().estimate_quotes(
            chargeable_weight_kg=chargeable_weight,
            destination_country=destination_country,
            carrier=carrier,
        )
        for item in quotes:
            item.setdefault("source", "aggregator_api")
        for card in cards:
            extra_weight = max(chargeable_weight - card.base_weight_kg, 0)
            estimated_price = card.base_price + (extra_weight * card.additional_price_per_kg)
            quotes.append(
                {
                    "carrier": card.carrier,
                    "destination_country": card.destination_country,
                    "currency": card.currency,
                    "estimated_price": round(float(estimated_price), 2),
                    "source": "rate_card",
                }
            )
        return success_response(
            {
                "actual_weight_kg": float(payload["actual_weight_kg"]),
                "volume_weight_kg": round(float(volume_weight), 3),
                "chargeable_weight_kg": round(float(chargeable_weight), 3),
                "divisor": divisor,
                "destination_country": destination_country,
                "quotes": quotes,
                "rate_cards": LogisticsRateCardSerializer(cards, many=True).data if cards else [],
            }
        )


# ============================================================
# Dashboard 聚合 API（前端控制台首页数据）
# ============================================================

class DashboardStatsView(APIView):
    """控制台统计卡片（含交付时效）"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="控制台统计数据")
    def get(self, request):
        from django.db.models import Sum, Count, Avg
        from datetime import date, timedelta

        total_orders = Order.objects.count()
        pending = Order.objects.filter(status__in=("pending", "paid")).count()
        agg = Order.objects.aggregate(
            total_sales=Sum("amount"),
            avg_value=Avg("amount"),
        )

        # 交付时效统计
        today = date.today()
        days30 = today - timedelta(days=30)
        shipped = Order.objects.filter(status="shipped", updated_at__date__gte=days30).count()
        deliv = list(Order.objects.filter(
            status__in=("signed", "completed", "shipped"),
            updated_at__date__gte=days30,
        ).values("created_at", "updated_at"))

        avg_days = 5.0
        if deliv:
            total_delta, cnt = 0.0, 0
            for o in deliv:
                if o["created_at"] and o["updated_at"]:
                    delta = (o["updated_at"] - o["created_at"]).total_seconds() / 86400
                    if delta > 0:
                        total_delta += delta
                        cnt += 1
            if cnt > 0:
                avg_days = round(total_delta / cnt, 1)

        completed_cnt = Order.objects.filter(
            status__in=("signed", "completed"), updated_at__date__gte=days30
        ).count()
        on_time_rate = round((completed_cnt / shipped * 100) if shipped > 0 else 0, 1)
        in_transit = Order.objects.filter(status="shipped").count()

        return success_response({
            "orderCount": total_orders,
            "salesAmount": float(agg["total_sales"] or 0),
            "avgOrderValue": round(float(agg["avg_value"] or 0), 2),
            "pendingOrders": pending,
            "avgDeliveryDays": avg_days,
            "onTimeRate": on_time_rate,
            "inTransitOrders": in_transit,
        })


class DashboardRecentOrdersView(APIView):
    """控制台实时订单列表"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="最近订单")
    def get(self, request):
        recent = Order.objects.all().order_by("-created_at")[:8]
        return success_response([
            {
                "id": o.id,
                "platform": o.platform or "未知平台",
                "customer": o.buyer_name or "匿名客户",
                "country": o.shipping_address or "未知",
                "city": "",
                "amount": float(o.amount or 0),
                "time": o.created_at.strftime("%H:%M") if o.created_at else "",
            }
            for o in recent
        ])


class DashboardSalesTrendView(APIView):
    """控制台销售额趋势"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="销售额趋势")
    def get(self, request):
        from datetime import date, timedelta
        from django.db.models import Sum

        labels = []
        values = []
        today = date.today()
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_name = ["周一","周二","周三","周四","周五","周六","周日"][day.weekday()]
            labels.append(day_name)
            total = Order.objects.filter(
                created_at__date=day
            ).aggregate(s=Sum("amount"))["s"] or 0
            values.append(float(total))
        return success_response({"labels": labels, "values": values})


# ============================================================
# 数据报表 聚合 API
# ============================================================

class ReportsSummaryView(APIView):
    """数据报表总览 - GET /api/reports/summary/"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="数据报表总览")
    def get(self, request):
        from datetime import date, timedelta
        from django.db.models import Sum, Count

        period = request.query_params.get("period", "7d")
        days = 7 if period == "7d" else 30
        today = date.today()
        current_start = today - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)

        def _trend(current_val, previous_val):
            if not previous_val:
                return 0
            return round((current_val - previous_val) / previous_val * 100, 1)

        # 采集商品数
        collect_now = CollectionTask.objects.filter(created_at__date__gte=current_start).count()
        collect_prev = CollectionTask.objects.filter(
            created_at__date__gte=previous_start, created_at__date__lt=current_start
        ).count()

        # 上货商品数（Product 总数作为代理）
        listing_now = Product.objects.filter(updated_at__date__gte=current_start).count()
        listing_prev = Product.objects.filter(
            updated_at__date__gte=previous_start, updated_at__date__lt=current_start
        ).count()

        # 订单
        order_now = Order.objects.filter(created_at__date__gte=current_start).count()
        order_prev = Order.objects.filter(
            created_at__date__gte=previous_start, created_at__date__lt=current_start
        ).count()

        # 销售额
        sales_now = Order.objects.filter(created_at__date__gte=current_start).aggregate(s=Sum("amount"))["s"] or 0
        sales_prev = Order.objects.filter(
            created_at__date__gte=previous_start, created_at__date__lt=current_start
        ).aggregate(s=Sum("amount"))["s"] or 0

        # 库存预警（取库存最低的10个商品）
        alerts = list(
            ProductVariant.objects.order_by("stock")
            .values("sku", "title", "stock", "product_id")[:10]
        )
        alerts = [{
            "skuId": a["sku"],
            "name": a["title"],
            "stock": a["stock"],
            "safeStock": 20,
            "status": "out" if a["stock"] == 0 else "low",
        } for a in alerts]

        # 热销商品 TOP10
        hot = (
            Order.objects.filter(created_at__date__gte=current_start)
            .values("buyer_name")
            .annotate(sales=Count("id"))
            .order_by("-sales")[:10]
        )
        hot_products = [{"name": h["buyer_name"] or "未知商品", "sales": h["sales"]} for h in hot]

        return success_response({
            "collectCount": collect_now,
            "collectTrend": _trend(collect_now, collect_prev),
            "listingCount": listing_now,
            "listingTrend": _trend(listing_now, listing_prev),
            "orderCount": order_now,
            "orderTrend": _trend(order_now, order_prev),
            "salesAmount": float(sales_now),
            "salesTrend": _trend(sales_now, sales_prev),
            "alerts": alerts,
            "hotProducts": hot_products,
        })


# ============================================================
# 新增缺失接口 (v2)
# ============================================================

class ImageUploadView(APIView):
    """图片上传"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="上传图片")
    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return error_response(message="file is required", status_code=400)
        # 写入本地 media 目录（生产环境替换为 OSS/COS）
        import uuid as _uuid
        import os as _os
        ext = file.name.rsplit(".", 1)[-1] if "." in file.name else "jpg"
        filename = f"{_uuid.uuid4().hex}.{ext}"
        media_dir = _os.path.join(settings.BASE_DIR, "media", "uploads")
        _os.makedirs(media_dir, exist_ok=True)
        filepath = _os.path.join(media_dir, filename)
        with open(filepath, "wb+") as dst:
            for chunk in file.chunks():
                dst.write(chunk)
        url = f"{getattr(settings, 'BACKEND_PUBLIC_URL', 'http://127.0.0.1:8000')}/media/uploads/{filename}"
        return success_response({"url": url})


class LogisticsCarriersView(APIView):
    """物流商列表"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="物流商列表")
    def get(self, request):
        carriers = LogisticsShipment.objects.values_list("carrier", flat=True).distinct()
        return success_response(sorted([c for c in carriers if c]))


class LogisticsSyncView(APIView):
    """批量同步物流轨迹"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="批量同步物流轨迹")
    def post(self, request):
        waybills = request.data.get("waybill_nos", [])
        if not waybills:
            return error_response(message="waybill_nos is required", status_code=400)
        client = get_logistics_aggregator_client()
        results = []
        for wb in waybills:
            try:
                shipment = LogisticsShipment.objects.filter(waybill_no=wb).first()
                if shipment:
                    events = client.fetch_tracking_events(waybill_no=wb, carrier=shipment.carrier)
                    results.append({"waybill_no": wb, "status": "synced", "events_count": len(events)})
                else:
                    results.append({"waybill_no": wb, "status": "not_found"})
            except Exception as exc:
                results.append({"waybill_no": wb, "status": "failed", "reason": str(exc)})
        return success_response({"results": results})


class LogisticsSubscribeView(APIView):
    """订阅物流轨迹推送"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="订阅物流轨迹")
    def post(self, request):
        waybill = request.data.get("waybill_no", "")
        callback_url = request.data.get("callback_url", "")
        if not waybill:
            return error_response(message="waybill_no is required", status_code=400)
        # TODO: 接入17Track订阅API
        return success_response({"waybill_no": waybill, "subscribed": True})


class OrderRemarkView(APIView):
    """订单备注"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="添加订单备注")
    def post(self, request, order_id):
        obj = get_object_or_404(Order, id=order_id)
        remark = request.data.get("remark", "").strip()
        if not remark:
            return error_response(message="remark is required", status_code=400)
        # Order 模型无 remark 字段，更新 shipping_address JSON 扩展
        addr = obj.shipping_address or {}
        if isinstance(addr, dict):
            addr["remark"] = remark
        else:
            addr = {"remark": remark, "_raw": str(addr)}
        obj.shipping_address = addr
        obj.save(update_fields=["shipping_address", "updated_at"])
        return success_response({"order_id": obj.id, "remark": remark})


class InventoryOverviewView(APIView):
    """库存概览统计"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="库存概览")
    def get(self, request):
        from django.db.models import Sum
        total_sku = ProductVariant.objects.count()
        agg = ProductVariant.objects.aggregate(t=Sum("stock"))
        total_stock = agg["t"] or 0
        alerts = ProductVariant.objects.filter(stock__lte=10).count()
        out = ProductVariant.objects.filter(stock=0).count()
        return success_response({
            "total_sku": total_sku,
            "total_stock": total_stock,
            "alert_count": alerts,
            "out_of_stock_count": out,
        })


class InventoryAdjustView(APIView):
    """库存调整（入库/出库）"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="库存调整")
    def post(self, request):
        sku = request.data.get("sku", "")
        warehouse = request.data.get("warehouse", "")
        adjust_type = request.data.get("type", "in")  # in / out
        quantity = int(request.data.get("quantity", 0))
        reason = request.data.get("reason", "")
        if not sku or quantity <= 0:
            return error_response(message="sku and quantity are required", status_code=400)

        variant = ProductVariant.objects.filter(sku=sku).first()
        if not variant:
            return error_response(message="SKU not found", status_code=404)

        if adjust_type == "out":
            if variant.stock < quantity:
                return error_response(message="库存不足", status_code=400)
            variant.stock -= quantity
        else:
            variant.stock += quantity
        variant.save(update_fields=["stock", "updated_at"])

        # 记录操作日志
        InventorySyncLog.objects.create(
            platform="manual", warehouse_id=warehouse,
            total_items=1, success_count=1, fail_count=0,
            message=f"{adjust_type}:{sku} qty={quantity} reason={reason}",
        )
        return success_response({"sku": sku, "new_stock": variant.stock})


class WarehouseListView(APIView):
    """仓库列表"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="仓库列表")
    def get(self, request):
        return success_response([
            {"id": "sz", "name": "深圳仓", "address": "深圳市龙华区"},
            {"id": "gz", "name": "广州仓", "address": "广州市白云区"},
            {"id": "uk", "name": "海外仓(英国)", "address": "UK"},
        ])


class ShopUnbindView(APIView):
    """店铺解绑"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="解绑店铺")
    def post(self, request):
        shop_id = request.data.get("shop_id")
        if not shop_id:
            return error_response(message="shop_id is required", status_code=400)
        shop = get_object_or_404(Shop, id=shop_id)
        shop.status = "inactive"
        shop.save(update_fields=["status", "updated_at"])
        return success_response({"shop_id": shop.id, "status": shop.status})


class DashboardNewOrdersSinceView(APIView):
    """控制台实时订单轮询"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="新订单轮询")
    def get(self, request):
        since = request.query_params.get("since", "0")
        try:
            since_id = int(since)
        except (TypeError, ValueError):
            since_id = 0
        orders = Order.objects.filter(id__gt=since_id).order_by("-id")[:20]
        return success_response([
            {
                "id": o.id,
                "platform": o.platform or "未知",
                "customer": o.buyer_name or "匿名",
                "amount": float(o.amount or 0),
                "time": o.created_at.strftime("%H:%M:%S") if o.created_at else "",
            }
            for o in orders
        ])


# ============================================================
# 商品上货 — 真实实现（替换 DemoGoodsListingSyncView）
# ============================================================

class GoodsListingView(APIView):
    """商品上货到目标平台（真实实现）"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="商品上货")
    def post(self, request):
        goods_id = request.data.get("goods_id")
        platforms = request.data.get("platforms", [])
        title = request.data.get("title", "")
        description = request.data.get("description", "")
        price = request.data.get("price", 0)
        images = request.data.get("images", [])

        if not goods_id or not platforms:
            return error_response(message="goods_id and platforms are required", status_code=400)

        goods = get_object_or_404(Product, id=goods_id)

        results = []
        for platform_key in platforms:
            try:
                # 尝试调用平台客户端上架
                client = get_platform_client(platform_key)
                listing_payload = {
                    "title": title or goods.title,
                    "description": description or "",
                    "price": float(price or goods.price),
                    "images": images or goods.images or [],
                }
                listing_resp = client.create_listing(listing_payload)
                results.append({
                    "platform": platform_key,
                    "status": "success",
                    "external_id": listing_resp.get("id") or listing_resp.get("product_id", ""),
                })
            except Exception as exc:
                # 平台客户端不可用 → 本地记录为待上架
                results.append({
                    "platform": platform_key,
                    "status": "pending",
                    "reason": f"platform client unavailable: {exc}",
                })

        # 标记商品已发布
        goods.attributes = goods.attributes or {}
        goods.attributes["listed_platforms"] = list(set(
            goods.attributes.get("listed_platforms", []) + platforms
        ))
        goods.save(update_fields=["attributes", "updated_at"])

        return success_response({"goods_id": goods_id, "results": results})


class GoodsBatchListingView(APIView):
    """批量商品上货（真实实现）"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="批量商品上货")
    def post(self, request):
        goods_ids = request.data.get("goods_ids", [])
        platforms = request.data.get("platforms", [])

        if not goods_ids or not platforms:
            return error_response(message="goods_ids and platforms are required", status_code=400)

        results = []
        for gid in goods_ids:
            goods = Product.objects.filter(id=gid).first()
            if not goods:
                results.append({"goods_id": gid, "status": "not_found"})
                continue
            for platform_key in platforms:
                try:
                    client = get_platform_client(platform_key)
                    client.create_listing({
                        "title": goods.title,
                        "price": float(goods.price or 0),
                        "images": goods.images or [],
                    })
                    results.append({"goods_id": gid, "platform": platform_key, "status": "success"})
                except Exception as exc:
                    results.append({"goods_id": gid, "platform": platform_key, "status": "pending", "reason": str(exc)})

        return success_response({"results": results})


# ============================================================
# 1688 采集 — 真实实现（替换 DemoCollect1688SingleView）
# ============================================================

class Collect1688SingleView(APIView):
    """1688 单链接采集（真实实现）"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="1688 单链接采集")
    def post(self, request):
        url = request.data.get("url", "").strip()
        if not url:
            return error_response(message="url is required", status_code=400)

        import re as _re

        # 尝试从1688页面抓取数据
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            resp = requests.get(url, headers=headers, timeout=15)
            html = resp.text

            # 从页面提取 JSON 数据
            title = ""
            price = ""
            images = []
            stock = 0

            # 尝试提取 offer 数据
            offer_match = _re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.+?});', html, _re.DOTALL)
            if offer_match:
                import json as _json
                try:
                    data = _json.loads(offer_match.group(1))
                    extracted = {"t": "", "p": "", "img": []}
                    def _find(obj):
                        if isinstance(obj, dict):
                            for k, v in obj.items():
                                if k in ("offerTitle", "title", "subject") and isinstance(v, str):
                                    extracted["t"] = extracted["t"] or v
                                if k in ("price", "offerPrice", "amount") and not extracted["p"]:
                                    extracted["p"] = str(v)
                                if k in ("images", "offerImgList") and isinstance(v, list):
                                    extracted["img"] = extracted["img"] or [i.get("url") or i for i in v if isinstance(i, (dict, str))]
                                _find(v)
                        elif isinstance(obj, list):
                            for item in obj:
                                _find(item)
                    _find(data)
                    title = title or extracted["t"]
                    if not price:
                        price = extracted["p"]
                    images = images or extracted["img"]
                except Exception:
                    pass

            # 提取图片（降级方案）
            if not images:
                images = _re.findall(r'<img[^>]+src="([^"]+\.(?:jpg|png|jpeg|webp))"', html)
                images = images[:10]

            # 提取标题（降级方案）
            if not title:
                title_match = _re.search(r'<title>(.+?)</title>', html)
                title = title_match.group(1).strip() if title_match else "1688商品"

            if not price:
                price_match = _re.search(r'(?:price|优惠价)[:\s]*[¥￥]?\s*([\d.]+)', html)
                price = price_match.group(1) if price_match else "0"

            # 保存到数据库
            product = Product.objects.create(
                platform="1688",
                platform_product_id=_re.search(r'offer/(\d+)', url).group(1) if _re.search(r'offer/(\d+)', url) else str(int(time.time())),
                title=title,
                images=[images[0]] if images else [],
                price=float(price),
                stock=stock,
            )

            return success_response({
                "id": product.id,
                "title": title,
                "price": float(price),
                "images": images,
                "platform": "1688",
                "stock": stock,
            })

        except requests.RequestException as exc:
            return error_response(message=f"采集失败: {exc}", status_code=400)
        except Exception as exc:
            return error_response(message=f"解析失败: {exc}", status_code=400)


# ============================================================
# 批量采集 + 导出（v3 采集引擎）
# ============================================================

class BatchScrapeView(APIView):
    """批量采集多链接（多平台）"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="批量采集商品链接")
    def post(self, request):
        urls = request.data.get("urls", [])
        platform = request.data.get("platform", "")

        if not urls:
            return error_response(message="urls is required", status_code=400)

        from .collect_scraper import scrape_batch

        # 限制单次最多20个链接
        results = scrape_batch(urls[:20], platform)

        # 保存到 Product 表
        saved = []
        for item in results:
            if item.get("status") == "success":
                pid = item.get("platform_product_id", "")
                plat = item.get("platform", "")
                if pid and plat:
                    product, created = Product.objects.get_or_create(
                        platform=plat,
                        platform_product_id=pid,
                        defaults={
                            "title": item.get("title", ""),
                            "price": item.get("price", 0),
                            "images": item.get("images", [])[:5],
                            "stock": item.get("stock", 0),
                        },
                    )
                    item["product_id"] = product.id
                    item["is_new"] = created
            saved.append(item)

        return success_response({
            "total": len(urls),
            "success_count": sum(1 for r in results if r.get("status") == "success"),
            "results": saved,
        })


class CollectExportView(APIView):
    """导出采集数据为 Excel/CSV"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="导出采集数据")
    def post(self, request):
        product_ids = request.data.get("product_ids", [])
        fmt = request.data.get("format", "xlsx")  # xlsx 或 csv

        if product_ids:
            products = list(Product.objects.filter(id__in=product_ids).values(
                "id", "title", "platform", "price", "stock", "images",
                "platform_product_id", "attributes",
            ))
        else:
            # 导出最近100条
            products = list(Product.objects.order_by("-id").values(
                "id", "title", "platform", "price", "stock", "images",
                "platform_product_id", "attributes",
            )[:100])

        from .collect_exporter import export_products

        rows = []
        for p in products:
            attrs = p.get("attributes") or {}
            source_url = attrs.get("source_url", "") if isinstance(attrs, dict) else ""
            rows.append({
                "title": p.get("title", ""),
                "platform": p.get("platform", ""),
                "price": float(p.get("price") or 0),
                "stock": p.get("stock") or 0,
                "source_url": source_url,
                "platform_product_id": p.get("platform_product_id", ""),
                "images": p.get("images") or [],
                "status": "已采集",
            })

        data, mime, filename = export_products(rows, fmt)

        if fmt == "csv":
            from django.http import HttpResponse
            response = HttpResponse(data.getvalue(), content_type=mime)
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            response.write('\ufeff')  # BOM for Excel
            return response
        else:
            from django.http import HttpResponse
            response = HttpResponse(data.getvalue(), content_type=mime)
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response


class ScrapeRulesView(APIView):
    """采集规则 CRUD"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="获取采集规则")
    def get(self, request):
        platform = request.query_params.get("platform", "")
        qs = ScrapeRule.objects.filter(is_active=True)
        if platform:
            qs = qs.filter(platform=platform)
        rules = list(qs.values("id", "platform", "field_name", "css_selector",
                                "regex_pattern", "image_attr", "data_script_regex", "priority"))
        return success_response(rules)

    @extend_schema(summary="创建/更新采集规则")
    def post(self, request):
        data = request.data
        rule_id = data.get("id")
        if rule_id:
            rule = get_object_or_404(ScrapeRule, id=rule_id)
            for k in ("platform", "field_name", "css_selector", "regex_pattern",
                        "image_attr", "data_script_regex", "priority", "is_active"):
                if k in data:
                    setattr(rule, k, data[k])
            rule.save()
        else:
            rule = ScrapeRule.objects.create(
                platform=data.get("platform", "1688"),
                field_name=data.get("field_name", "title"),
                css_selector=data.get("css_selector", ""),
                regex_pattern=data.get("regex_pattern", ""),
                image_attr=data.get("image_attr", "src"),
                data_script_regex=data.get("data_script_regex", ""),
                priority=data.get("priority", 0),
            )
        return success_response({"id": rule.id})


# ============================================================
# 页面代理 —— 绕过 X-Frame-Options 实现 iframe 内嵌抓取
# ============================================================
# 页面代理 —— 绕过 X-Frame-Options 实现 iframe 内嵌抓取
# ============================================================

class PageProxyView(APIView):
    """页面代理：iframe 加载货源平台（无需认证）"""
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(summary="代理加载外部页面")
    def get(self, request):
        import re as _re
        url = request.query_params.get("url", "").strip()
        if not url:
            return error_response(message="url is required", status_code=400)
        allowed = ["1688.com", "taobao.com", "tmall.com", "yangkeduo.com", "pinduoduo.com"]
        domain = _re.search(r'https?://([^/]+)', url)
        if not domain or not any(d in domain.group(1) for d in allowed):
            return error_response(message="不支持的域名", status_code=400)
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"}
            resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
            resp.encoding = resp.apparent_encoding or "utf-8"
            html = resp.text
            html = html.replace('src="/', 'src="https://' + domain.group(1).split('/')[0] + '/')
            html = html.replace('href="/', 'href="https://' + domain.group(1).split('/')[0] + '/')
            response = HttpResponse(html, content_type="text/html; charset=utf-8")
            response["X-Frame-Options"] = ""
            return response
        except requests.RequestException as e:
            return error_response(message=f"页面加载失败: {e}", status_code=502)


class DashboardDeliveryStatsView(APIView):
    """控制台交付时效统计"""
    permission_classes = _BUSINESS_API_PERMISSIONS

    @extend_schema(summary="交付时效统计")
    def get(self, request):
        from datetime import date, timedelta

        today = date.today()
        days30 = today - timedelta(days=30)

        shipped = Order.objects.filter(status="shipped", updated_at__date__gte=days30)
        total_shipped = shipped.count()

        # 平均交付天数
        deliv = list(Order.objects.filter(
            status__in=("signed", "completed", "shipped"),
            updated_at__date__gte=days30,
        ).values("created_at", "updated_at"))

        avg_days = 5.0
        if deliv:
            total_delta, cnt = 0.0, 0
            for o in deliv:
                if o["created_at"] and o["updated_at"]:
                    delta = (o["updated_at"] - o["created_at"]).total_seconds() / 86400.0
                    if delta > 0:
                        total_delta += delta
                        cnt += 1
            if cnt > 0:
                avg_days = round(total_delta / cnt, 1)

        completed = Order.objects.filter(
            status__in=("signed", "completed"), updated_at__date__gte=days30
        ).count()
        on_time_rate = round((completed / total_shipped * 100) if total_shipped > 0 else 0, 1)

        in_transit = Order.objects.filter(status="shipped").count()

        return success_response({
            "avg_delivery_days": avg_days,
            "on_time_rate": on_time_rate,
            "in_transit_orders": in_transit,
        })

    @extend_schema(summary="代理加载外部页面（支持 iframe）")
    def get(self, request):
        import re as _re
        import html as _html

        url = request.query_params.get("url", "").strip()
        if not url:
            return error_response(message="url is required", status_code=400)

        # 安全校验：只允许白名单域名
        allowed_domains = [
            "1688.com", "detail.1688.com",
            "taobao.com", "item.taobao.com",
            "tmall.com", "detail.tmall.com",
            "yangkeduo.com", "mobile.yangkeduo.com",
            "pinduoduo.com",
        ]
        domain = _re.search(r'https?://([^/]+)', url)
        if not domain or not any(d in domain.group(1) for d in allowed_domains):
            return error_response(message="不支持的域名", status_code=400)

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,*/*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Accept-Encoding": "gzip, deflate",
            }
            resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
            resp.encoding = resp.apparent_encoding or "utf-8"
            html_content = resp.text

            # 1. 将相对路径改为绝对路径
            base = f"{domain.group(1).split('/')[0]}"
            html_content = html_content.replace('src="/', f'src="https://{base}/')
            html_content = html_content.replace("src='/", f"src='https://{base}/")
            html_content = html_content.replace('href="/', f'href="https://{base}/')
            html_content = html_content.replace("href='/", f"href='https://{base}/")

            # 2. 注入采集辅助脚本
            inject_script = """
<script>
(function() {
  if (window.__erpProxyInjected__) return;
  window.__erpProxyInjected__ = true;

  // 识别鼠标悬停的商品卡片
  let selectedEl = null;
  document.addEventListener('mouseover', function(e) {
    let el = e.target;
    for (let i = 0; i < 6; i++) {
      if (!el || el.tagName === 'BODY') break;
      if (el.matches && (
        el.matches('[data-offer-id]') || el.matches('[class*="offer"]') ||
        el.matches('[class*="product"]') || el.matches('[class*="item"]') ||
        el.matches('[class*="goods"]') || el.matches('.mod-detail-offer')
      )) {
        // 高亮选中元素
        if (selectedEl && selectedEl !== el) selectedEl.style.outline = '';
        selectedEl = el;
        el.style.outline = '3px solid #22c55e';
        el.style.outlineOffset = '-2px';
        el.style.cursor = 'grab';
        el.title = '拖拽此商品到平台浏览器即可采集';
        break;
      }
      el = el.parentElement;
    }
  }, true);

  // 拖拽时提取商品数据
  document.addEventListener('dragstart', function(e) {
    if (!selectedEl) return;
    e.dataTransfer.effectAllowed = 'copy';

    var getText = function(cls) {
      var n = selectedEl.querySelector(cls);
      return n ? n.innerText.trim() : '';
    };

    var title = getText('h1') || getText('h2') || getText('.title') || getText('[class*="title"]') || '';
    var priceText = getText('.price') || getText('[class*="price"]') || '';
    var price = parseFloat(priceText.replace(/[^0-9.]/g, '')) || 0;
    var img = selectedEl.querySelector('img');
    var image = img ? (img.src || img.getAttribute('data-src') || '') : '';
    var link = selectedEl.querySelector('a');
    var sourceUrl = link ? link.href : window.location.href;

    var productData = {
      name: title, title: title, price: price,
      images: image ? [image] : [], sourceUrl: sourceUrl,
      platform: window.location.hostname.includes('1688') ? '1688' :
                window.location.hostname.includes('taobao') ? 'taobao' : 'pdd',
      _source: 'dragDrop', _timestamp: Date.now()
    };

    e.dataTransfer.setData('text/plain', title + '\\n' + sourceUrl);
    e.dataTransfer.setData('application/json', JSON.stringify(productData));
    e.dataTransfer.setData('text/uri-list', sourceUrl);
  }, true);

  console.log('[ERP Proxy] 采集脚本已注入，悬停商品卡片后拖拽到平台浏览器即可');
})();
</script>
"""
            html_content = html_content.replace('</body>', inject_script + '</body>')

            # 3. 返回页面
            response = HttpResponse(html_content, content_type="text/html; charset=utf-8")
            # 关键：不设置 X-Frame-Options，允许 iframe 加载
            response["X-Frame-Options"] = ""
            response["Content-Security-Policy"] = "frame-ancestors *"
            return response

        except requests.RequestException as e:
            return error_response(message=f"页面加载失败: {e}", status_code=502)
