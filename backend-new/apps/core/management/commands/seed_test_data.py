"""
测试数据生成器
用法:
    python manage.py seed_test_data                          # 默认各 10 条
    python manage.py seed_test_data --orders 50 --products 30
    python manage.py seed_test_data --clear                  # 仅清理
    python manage.py seed_test_data --clear --orders 20      # 清理后重生成
"""
import random
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

# ============================================================
# 参数化数据源 —— 按品类定义真实商品（非硬编码，可扩展）
# ============================================================
_CATEGORIES = ["电子产品", "服装鞋帽", "家居用品", "美妆个护", "运动户外", "箱包皮具", "母婴玩具", "汽车用品"]
_PLATFORMS = ["tiktok", "shopee", "amazon", "temu", "shein", "lazada"]
_COLORS = ["黑色", "白色", "红色", "蓝色", "绿色", "灰色", "粉色"]
_SIZES  = ["S", "M", "L", "XL", "2XL"]
_MATERIALS = ["纯棉", "涤纶", "硅胶", "不锈钢", "ABS塑料", "铝合金", "TPE橡胶", "牛津布", "碳纤维"]
_IMAGE_TEMPLATES = [
    "https://picsum.photos/seed/{seed}/400/400",
    "https://picsum.photos/seed/{seed}a/400/400",
    "https://picsum.photos/seed/{seed}b/400/400",
]

# 按品类定义的参数化商品模板：{ category, titles:[{cn,en}], price_range:(min,max), features:[...], desc_template }
_PRODUCT_TEMPLATES = [
    {
        "category": "电子产品",
        "items": [
            {"cn": "无线降噪蓝牙耳机 TWS-5.3", "en": "Wireless ANC Earbuds TWS 5.3", "price": (49, 129),
             "features": ["主动降噪", "蓝牙5.3", "续航30小时", "IPX5防水", "触控操作"]},
            {"cn": "快速充电数据线  Type-C 100W", "en": "100W PD Fast Charging Cable USB-C", "price": (8, 25),
             "features": ["100W快充", "尼龙编织", "2米长度", "兼容iPhone/Android"]},
            {"cn": "智能手表 心率血氧监测", "en": "Smart Watch Heart Rate SpO2 Monitor", "price": (89, 199),
             "features": ["心率监测", "血氧检测", "睡眠分析", "IP68防水", "7天续航"]},
            {"cn": "便携无线充电宝 20000mAh", "en": "20000mAh Portable Power Bank Wireless", "price": (35, 79),
             "features": ["20000毫安", "无线充电", "PD快充", "LED电量显示", "超薄设计"]},
            {"cn": "RGB机械键盘 87键青轴", "en": "RGB Mechanical Keyboard 87 Keys Blue Switch", "price": (59, 139),
             "features": ["青轴手感", "RGB背光", "热插拔", "PBT键帽", "Type-C接口"]},
        ],
    },
    {
        "category": "服装鞋帽",
        "items": [
            {"cn": "纯棉情侣T恤 宽松oversize", "en": "Cotton Couple T-Shirt Oversize Unisex", "price": (29, 69),
             "features": ["100%纯棉", "oversize版型", "情侣款", "多色可选", "不易变形"]},
            {"cn": "轻量透气跑步鞋 网面减震", "en": "Lightweight Breathable Running Shoes Mesh", "price": (89, 199),
             "features": ["飞织网面", "减震中底", "防滑大底", "仅重220g", "运动休闲"]},
            {"cn": "防晒冰丝连帽外套 UPF50+", "en": "UPF50+ Ice Silk Sun Protection Hoodie", "price": (49, 99),
             "features": ["UPF50+防晒", "冰丝面料", "连帽设计", "轻薄透气", "速干"]},
            {"cn": "弹力修身牛仔裤 直筒高腰", "en": "Stretch Slim Fit Jeans High Waist Straight", "price": (59, 129),
             "features": ["弹力面料", "高腰设计", "直筒版型", "四季可穿", "经典五袋"]},
            {"cn": "冬季加厚羽绒服 防风保暖", "en": "Winter Thick Down Jacket Windproof Warm", "price": (159, 399),
             "features": ["90%白鸭绒", "防风面料", "可拆卸帽", "多口袋", "抗寒-20°C"]},
        ],
    },
    {
        "category": "家居用品",
        "items": [
            {"cn": "双层玻璃保温杯 316不锈钢", "en": "Double-Wall Thermos Cup 316 Stainless Steel", "price": (25, 59),
             "features": ["316不锈钢", "双层真空", "12小时保温", "500ml容量", "食品级材质"]},
            {"cn": "LED护眼台灯 无频闪触控调光", "en": "LED Eye-Care Desk Lamp Flicker-Free Dimmable", "price": (45, 99),
             "features": ["无频闪", "3档调光", "触控开关", "360°旋转", "USB供电"]},
            {"cn": "加厚珊瑚绒毛毯 双面绒", "en": "Thick Coral Fleece Blanket Double-Sided", "price": (39, 89),
             "features": ["双面珊瑚绒", "可机洗", "不褪色", "多种尺寸", "保暖柔软"]},
        ],
    },
    {
        "category": "运动户外",
        "items": [
            {"cn": "防水登山双肩包 40L大容量", "en": "Waterproof Hiking Backpack 40L Large Capacity", "price": (69, 159),
             "features": ["防水面料", "40L容量", "人体工学背负", "多隔层", "反光条"]},
            {"cn": "瑜伽垫 NBR加厚防滑", "en": "NBR Yoga Mat Thick Non-Slip Exercise", "price": (29, 69),
             "features": ["NBR材质", "6mm加厚", "双面防滑", "含背包带", "易清洁"]},
            {"cn": "运动速干毛巾 超细纤维", "en": "Sports Quick-Dry Towel Microfiber", "price": (15, 35),
             "features": ["超细纤维", "3秒吸水", "轻便携带", "不掉毛", "可重复使用"]},
        ],
    },
    {
        "category": "美妆个护",
        "items": [
            {"cn": "超声波洁面仪 IPX7防水", "en": "Ultrasonic Facial Cleanser IPX7 Waterproof", "price": (59, 129),
             "features": ["超声波震动", "IPX7防水", "3档调节", "USB充电", "硅胶刷头"]},
            {"cn": "负离子护发吹风机 大风量", "en": "Negative Ion Hair Dryer Strong Airflow", "price": (79, 169),
             "features": ["负离子护发", "2000W功率", "3档温度", "磁吸风嘴", "低噪音"]},
        ],
    },
]

_BUYER_NAMES = [
    "John Smith", "Maria Garcia", "David Chen", "Sarah Wilson",
    "Ali Rahman", "Linda Johnson", "Mike Brown", "Anna Lee",
    "Tom Zhang", "Emily Davis", "Sophia Kim", "James Wang",
    "Olivia Liu", "Daniel Park", "Emma Thompson", "Lucas Martin",
    "Mia Rodriguez", "Noah Taylor", "Ava Martinez", "Ethan Jones",
]
_TAG_TEMPLATE = "TEST_SEED_{ts}"


class Command(BaseCommand):
    help = "生成参数化测试数据（前缀 TEST_SEED_*）"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=10)
        parser.add_argument("--shops", type=int, default=6)
        parser.add_argument("--products", type=int, default=30)
        parser.add_argument("--variants-per-product", type=int, default=3)
        parser.add_argument("--orders", type=int, default=50)
        parser.add_argument("--shipments", type=int, default=20)
        parser.add_argument("--clear", action="store_true", help="只清理测试数据")

    def handle(self, *args, **options):
        ts = int(timezone.now().timestamp())
        tag = _TAG_TEMPLATE.format(ts=ts)

        # ── 清理旧测试数据 ──
        self._clear(tag)

        if options["clear"]:
            self.stdout.write(self.style.SUCCESS("测试数据已清理"))
            return

        # ── 生成顺序 ──
        self._seed_users(options["users"], tag)
        self._seed_shops(options["shops"], tag)
        self._seed_products(options["products"], options["variants_per_product"], tag)
        self._seed_orders(options["orders"], tag)
        self._seed_shipments(options["shipments"], tag)
        self._seed_collection_tasks(tag)

        self.stdout.write(self.style.SUCCESS(
            f"测试数据生成完毕 (tag={tag}) 删除命令: python manage.py seed_test_data --clear"
        ))

    # ================ 清理 ================
    def _clear(self, tag):
        from apps.core.models import (
            Order, Product, ProductVariant, CollectionTask,
            LogisticsShipment, InventorySyncLog, Shop, ScrapeRule,
        )
        # 按外键顺序删
        LogisticsShipment.objects.all().delete()
        Order.objects.all().delete()
        InventorySyncLog.objects.all().delete()
        CollectionTask.objects.all().delete()
        ProductVariant.objects.all().delete()
        Product.objects.all().delete()
        Shop.objects.all().delete()
        ScrapeRule.objects.all().delete()
        # 清理测试用户
        User.objects.filter(username__startswith="test_").delete()

    # ================ 用户 ================
    def _seed_users(self, count, tag):
        for i in range(count):
            username = f"test_user_{i:03d}"
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    password="Test123456",
                    email=f"{username}@test.com",
                )
        self.stdout.write(f"  [OK] 用户: {count}")

    # ================ 店铺 ================
    def _seed_shops(self, count, tag):
        from apps.core.models import Shop
        names = ["深圳主店", "广州分店", "义乌仓店", "英国海外仓", "泰国站点", "菲律宾店铺"]
        for i, platform in enumerate(_PLATFORMS[:count]):
            ext_id = f"{tag}_shop_{platform}"
            if not Shop.objects.filter(external_shop_id=ext_id).exists():
                Shop.objects.create(
                    platform=platform,
                    external_shop_id=ext_id,
                    name=names[i] if i < len(names) else f"{platform}_测试店",
                    status="active",
                )
        self.stdout.write(f"  [OK] 店铺: {count}")

    # ================ 商品 & SKU（按品类模板生成真实商品）==========
    def _seed_products(self, count, variants_per, tag):
        from apps.core.models import Product, ProductVariant

        # 展开所有品类商品模板
        all_items = []
        for tmpl in _PRODUCT_TEMPLATES:
            for item in tmpl["items"]:
                all_items.append({**item, "category": tmpl["category"]})

        for i in range(count):
            # 从模板中循环选取（不够则随机复用）
            base = all_items[i % len(all_items)]
            platform = random.choice(_PLATFORMS)
            pid = f"{tag}_prod_{i:04d}"
            lo, hi = base["price"]
            price = round(random.uniform(lo, hi), 2)
            stock = random.randint(10, 500)
            material = random.choice(_MATERIALS)

            # 商品主标题：中英双语
            title = f"{base['cn']} {material} / {base['en']}"

            # 商品描述
            features_text = "、".join(base["features"])
            desc = f"【{base['category']}】{base['cn']}。核心卖点：{features_text}。材质：{material}，适合跨境电商多平台销售。"

            img_seed = hash(pid) % 10000
            images = [t.format(seed=img_seed) for t in _IMAGE_TEMPLATES]

            product, _ = Product.objects.update_or_create(
                platform=platform, platform_product_id=pid,
                defaults={
                    "title": title,
                    "price": price,
                    "stock": stock,
                    "images": images,
                    "attributes": {
                        "category": base["category"],
                        "material": material,
                        "features": base["features"],
                        "description": desc,
                        "description_cn": desc,
                        "sku": f"ERP-{base['category'][:2]}-{i:04d}",
                        "barcode": f"BAR{random.randint(100000000000, 999999999999)}",
                        "source_url": f"https://detail.1688.com/offer/{random.randint(600000000, 700000000)}.html",
                    },
                },
            )

            # 生成 SKU 变体
            for v in range(variants_per):
                sku = f"{pid}_SKU_{v:02d}"
                color = random.choice(_COLORS)
                size  = random.choice(_SIZES)
                sku_price = round(price * random.uniform(0.8, 1.2), 2)
                sku_stock = max(0, random.randint(0, stock // variants_per))
                ProductVariant.objects.update_or_create(
                    product=product, sku=sku,
                    defaults={
                        "title": f"{title} ({color}/{size})",
                        "price": sku_price,
                        "stock": sku_stock,
                        "attributes": {"color": color, "size": size},
                    },
                )

        self.stdout.write(f"  [OK] 商品: {count} (每款 {variants_per} SKU, 覆盖{len(all_items)}种品类)")

    # ================ 订单（覆盖全部状态、金额、地区）============
    def _seed_orders(self, count, tag):
        from apps.core.models import Order
        from apps.core.models import Product

        products = list(Product.objects.all())
        if not products:
            self.stdout.write("  [WARN] 无商品，跳订单")
            return

        statuses = ["pending", "paid", "shipped", "signed", "completed", "cancelled"]
        status_weights = [0.15, 0.20, 0.25, 0.15, 0.20, 0.05]
        regions = ["美国", "英国", "马来西亚", "泰国", "新加坡", "印尼", "中国"]

        today = timezone.now().date()
        for i in range(count):
            product = random.choice(products)
            status = random.choices(statuses, weights=status_weights, k=1)[0]
            qty = random.randint(1, 5)
            amount = round(float(product.price) * qty * random.uniform(0.9, 1.3), 2)

            # 过去 30 天内随机时间
            days_ago = random.randint(0, 30)
            created = timezone.make_aware(
                datetime.datetime.combine(
                    today - datetime.timedelta(days=days_ago),
                    datetime.time(hour=random.randint(0, 23), minute=random.randint(0, 59)),
                )
            )
            updated = created + datetime.timedelta(
                hours=random.randint(1, 72),
                minutes=random.randint(0, 59),
            ) if status not in ("pending", "cancelled") else created

            Order.objects.create(
                platform=product.platform,
                order_no=f"{tag}_order_{i:05d}",
                status=status,
                buyer_name=random.choice(_BUYER_NAMES),
                amount=amount,
                shipping_address={
                    "country": random.choice(regions),
                    "city": f"测试城市{i%10}",
                    "street": f"测试街道{i%20}号",
                },
                created_at=created,
                updated_at=updated,
            )
        self.stdout.write(f"  [OK] 订单: {count} (pending/paid/shipped/signed/completed/cancelled)")

    # ================ 物流单 ================
    def _seed_shipments(self, count, tag):
        from apps.core.models import LogisticsShipment, Order

        shipped = list(Order.objects.filter(status__in=("shipped", "signed", "completed")))
        carriers = ["顺丰国际", "云途物流", "燕文物流", "DHL", "FedEx", "UPS"]
        if not shipped:
            self.stdout.write("  [WARN] 无已发货订单，跳物流")
            return

        for i in range(min(count, len(shipped))):
            order = shipped[i]
            LogisticsShipment.objects.create(
                waybill_no=f"{tag}_WB_{i:05d}",
                carrier=random.choice(carriers),
                order=order,
                status=random.choice(["in_transit", "delivered"]),
            )
        self.stdout.write(f"  [OK] 物流单: {min(count, len(shipped))}")

    # ================ 采集任务 ================
    def _seed_collection_tasks(self, tag):
        from apps.core.models import CollectionTask
        from apps.core.models import Product

        products = list(Product.objects.all())
        if not products:
            return

        for status, label in [("success", "成功"), ("pending", "等待中"), ("failed", "失败")]:
            CollectionTask.objects.create(
                platform=random.choice(_PLATFORMS),
                target_ids=[p.platform_product_id for p in random.sample(products, min(3, len(products)))],
                status=status,
                result_message=f"测试采集任务 ({label})",
            )
        self.stdout.write(f"  [OK] 采集任务: 3 (success/pending/failed)")
