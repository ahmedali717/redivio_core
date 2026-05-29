from django.db import models
from apps.core.models import OpCo
from apps.item_master.models import Material
import uuid

# =========================================================
# 1. هندسة المنيو والوصفات (Menu & Recipe Engineering)
# =========================================================

class Recipe(models.Model):
    """
    Recipe / Bill of Materials (BOM)
    وصفة المنتج النهائي التي سيتم تفكيكها لخصم المخزون
    """
    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE)
    finished_good = models.OneToOneField(Material, on_delete=models.CASCADE, related_name='recipe')
    name = models.CharField(max_length=200, help_text="اسم الوصفة (مثال: وصفة برجر لحم دبل)")
    is_active = models.BooleanField(default=True)
    preparation_time = models.IntegerField(default=0, help_text="وقت التحضير بالدقائق")
    
    # تحديد طابعة المطبخ أو شاشة المطبخ KDS
    KITCHEN_STATIONS = [
        ('grill', 'الجريل (Grill)'),
        ('bar', 'البار والمشروبات (Bar)'),
        ('salads', 'المقبلات والسلطات (Salads)'),
        ('pizza', 'البيتزا والمعجنات (Pizza)'),
        ('dessert', 'الحلويات (Dessert)')
    ]
    kitchen_station = models.CharField(max_length=50, choices=KITCHEN_STATIONS, default='grill')

    def __str__(self):
        return f"Recipe: {self.name} for {self.finished_good.name}"


class RecipeItem(models.Model):
    """
    مكونات الوصفة (المواد الخام التي سيتم خصمها)
    """
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    ingredient = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='used_in_recipes')
    quantity = models.DecimalField(max_digits=10, decimal_places=4, help_text="الكمية المراد خصمها من المخزن")
    uom = models.CharField(max_length=20, default='KG', help_text="وحدة القياس (مثال: جرام، مل، حبة)")
    
    # لدعم التعديلات (بدون بصل مثلاً)
    is_removable = models.BooleanField(default=True, help_text="هل يمكن للعميل طلب إزالة هذا المكون؟")

    def __str__(self):
        return f"{self.quantity} {self.uom} of {self.ingredient.name}"


class ModifierGroup(models.Model):
    """
    مجموعات التعديل (مثال: الإضافات، نوع الجبنة، درجة السواء)
    """
    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    is_required = models.BooleanField(default=False)
    min_choices = models.IntegerField(default=0)
    max_choices = models.IntegerField(default=1)

    def __str__(self):
        return self.name


class Modifier(models.Model):
    """
    تعديل معين (مثال: إضافة جبنة شيدر)
    """
    group = models.ForeignKey(ModifierGroup, on_delete=models.CASCADE, related_name='modifiers')
    name = models.CharField(max_length=100)
    extra_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # الربط بصنف خام لخصمه من المخزن إذا طلب العميل الإضافة!
    linked_material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    material_qty = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)

    def __str__(self):
        return f"{self.name} (+{self.extra_price})"


# =========================================================
# 2. أكواد العروض والخصومات (Promo Codes & Discounts)
# =========================================================

class PromoCode(models.Model):
    """
    كود العرض / الخصم المسبق التعريف
    """
    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE, related_name='promo_codes')
    code = models.CharField(max_length=50, help_text="كود العرض (مثال: WELCOME10)")
    description = models.CharField(max_length=200, null=True, blank=True, help_text="وصف العرض")

    DISCOUNT_TYPES = [
        ('percentage', 'نسبة مئوية (%)'),
        ('fixed', 'قيمة ثابتة (Fixed Amount)'),
    ]
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="قيمة الخصم (نسبة أو مبلغ)")

    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="الحد الأدنى للطلب لتطبيق الكود")
    max_uses = models.IntegerField(default=0, help_text="أقصى عدد مرات الاستخدام (0 = غير محدود)")
    used_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="تاريخ انتهاء العرض (اختياري)")

    class Meta:
        unique_together = ('opco', 'code')

    def __str__(self):
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type == 'percentage' else ' EGP'})"


# =========================================================
# 3. محرك الطلبات ونقاط البيع (POS Orders Engine)
# =========================================================

class POSTerminal(models.Model):
    """
    جهاز نقطة البيع - POS Terminal / Register
    """
    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE, related_name='pos_terminals')
    name = models.CharField(max_length=100, help_text="اسم جهاز نقطة البيع")
    code = models.CharField(max_length=20, help_text="كود نقطة البيع")
    
    TERMINAL_TYPES = [
        ('DIRECT', 'Direct Sales (مبيعات مباشرة)'),
        ('RESTAURANT', 'Restaurant (مطعم)')
    ]
    terminal_type = models.CharField(max_length=20, choices=TERMINAL_TYPES, default='DIRECT', help_text="طبيعة التشغيل")
    is_active = models.BooleanField(default=True)
    allowed_users = models.ManyToManyField(
        'auth.User',
        blank=True,
        related_name='allowed_pos_terminals',
        help_text='المستخدمون المسموح لهم بفتح نقطة البيع هذه'
    )

    class Meta:
        unique_together = ('opco', 'code')

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.get_terminal_type_display()}"


class POSSession(models.Model):
    """
    وردية الكاشير -Shift Management
    """
    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE)
    terminal = models.ForeignKey(POSTerminal, on_delete=models.CASCADE, related_name='sessions', null=True, blank=True)
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    cashier_name = models.CharField(max_length=100)
    
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    expected_closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    actual_closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return f"Shift {self.id} ({self.cashier_name})"

class POSCashTransaction(models.Model):
    """
    حركات النقدية الخارجة والداخلة (مصاريف، عجز، زيادة)
    """
    session = models.ForeignKey(POSSession, on_delete=models.CASCADE, related_name='transactions')
    TRANS_TYPES = [('IN', 'إيداع'), ('OUT', 'صرف / مصاريف')]
    type = models.CharField(max_length=10, choices=TRANS_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.amount} ({self.reason})"


class POSOrder(models.Model):
    """
    طلب العميل الرئيسي
    """
    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE)
    session = models.ForeignKey(POSSession, on_delete=models.CASCADE, related_name='orders')
    order_ref = models.CharField(max_length=50, unique=True)
    
    ORDER_TYPES = [
        ('DINE_IN', 'Dine In (محلي)'),
        ('TAKEAWAY', 'Takeaway (سفري)'),
        ('DELIVERY', 'Delivery (توصيل)')
    ]
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='TAKEAWAY')
    table_number = models.CharField(max_length=20, null=True, blank=True)
    guest_count = models.IntegerField(default=1)
    
    PAYMENT_METHODS = [
        ('cash', 'Cash (كاش)'),
        ('credit', 'Credit (آجل)'),
        ('instapay', 'InstaPay (إلكتروني)')
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    # الخصومات والعروض
    DISCOUNT_TYPES = [
        ('none', 'بدون خصم'),
        ('percentage', 'نسبة مئوية (%)'),
        ('fixed', 'قيمة ثابتة (Fixed Amount)'),
    ]
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='none')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="قيمة الخصم (% أو مبلغ)")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="قيمة الخصم الفعلية بالجنيه")
    promo_code = models.ForeignKey('PromoCode', null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
    promo_code_text = models.CharField(max_length=50, null=True, blank=True, help_text="نص كود العرض المستخدم")
    discount_approved_by = models.CharField(max_length=100, null=True, blank=True, help_text="اسم من وافق على الخصم")

    STATUS_CHOICES = [
        ('draft', 'Draft (لم يدفع)'),
        ('paid', 'Received (تم الاستلام - في المطبخ)'),
        ('inprogress', 'In Progress (جاري التحضير)'),
        ('done', 'Done (جاهز للاستلام)'),
        ('refunded', 'Refunded (مرتجع)'),
        ('cancelled', 'Cancelled (ملغي)')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_refunded = models.BooleanField(default=False)
    
    # KDS Timestamps
    kitchen_received_at = models.DateTimeField(null=True, blank=True)
    kitchen_started_at = models.DateTimeField(null=True, blank=True)
    kitchen_done_at = models.DateTimeField(null=True, blank=True)
    kitchen_cancelled_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.order_ref:
            import time, random
            # Added a random suffix to prevent 500 errors from duplicate keys
            self.order_ref = f"POS-{int(time.time())}-{random.randint(1000, 9999)}"
        super().save(*args, **kwargs)
    
    # لمعرفة هل تم خصم المخزون بالفعل أم لا في الخلفية؟
    inventory_deducted = models.BooleanField(default=False)

    # ===== حقول عميل التوصيل =====
    customer_name = models.CharField(max_length=200, null=True, blank=True, help_text="اسم عميل التوصيل")
    customer_phone = models.CharField(max_length=30, null=True, blank=True, help_text="رقم تليفون العميل")
    customer_address = models.TextField(null=True, blank=True, help_text="عنوان التوصيل")
    delivery_notes = models.TextField(null=True, blank=True, help_text="ملاحظات التوصيل")
    # رابط للعميل في موديول المبيعات (يُنشأ تلقائياً عند تأكيد الدفع)
    sales_customer = models.ForeignKey(
        'sales.Customer',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='pos_delivery_orders',
        help_text="العميل المرتبط في موديول المبيعات"
    )

    def deduct_inventory(self):
        """
        محرك خصم المكونات (BOM Engine)
        يتم استدعاؤه عند تأكيد الطلب أو دفع الفاتورة
        """
        if self.inventory_deducted:
            return
        
        from apps.wms.models import StockMove
        from apps.item_master.models import MaterialLocation
        
        # دالة مساعدة للتحقق من استبعاد المكون
        def is_ingredient_excluded(notes, ingredient_name):
            if not notes:
                return False
            notes = notes.lower().strip()
            exclude_keywords = [
                "بدون", "من غير", "لا", "إلغاء", "حذف", "شيل", "بلا",
                "without", "no", "exclude", "remove", "w/o", "ex ", "less"
            ]
            has_exclude_keyword = any(kw in notes for kw in exclude_keywords)
            if not has_exclude_keyword:
                return False
                
            clean_name = ingredient_name.lower().strip()
            if clean_name.startswith("ال"):
                clean_name = clean_name[2:]
                
            if clean_name in notes:
                return True
            if ingredient_name.lower() in notes:
                return True
            return False
            
        for line in self.lines.all():
            material = line.material
            
            # 1. تحقق من وجود وصفة (Recipe) لتفكيكها
            recipe = None
            try:
                recipe = material.recipe
            except:
                recipe = None
                
            if recipe and recipe.ingredients.exists():
                for ingredient_line in recipe.ingredients.all():
                    # تحقق مما إذا طلب العميل أو حالة المنتج تقتضي إزالة هذا المكون
                    if is_ingredient_excluded(line.kitchen_notes, ingredient_line.ingredient.name):
                        continue
                        
                    qty_to_deduct = ingredient_line.quantity * line.qty
                    source_bin = self._find_best_bin(ingredient_line.ingredient)
                    
                    StockMove.objects.create(
                        opco=self.opco,
                        material=ingredient_line.ingredient,
                        source_bin=source_bin,
                        dest_bin=None,
                        quantity=qty_to_deduct,
                        reference=f"POS Order {self.order_ref} (BOM)",
                        move_type='OUT'
                    )
            else:
                # 2. إذا لم تكن هناك وصفة (أو وصفة فارغة)، يتم خصم المنتج نفسه إذا كان POS Item
                if material.is_pos_item:
                    source_bin = self._find_best_bin(material)
                    
                    StockMove.objects.create(
                        opco=self.opco,
                        material=material,
                        source_bin=source_bin,
                        dest_bin=None,
                        quantity=line.qty,
                        reference=f"POS Order {self.order_ref}",
                        move_type='OUT'
                    )
        
        self.inventory_deducted = True
        self.save()

    def _find_best_bin(self, material):
        """
        البحث عن أفضل رف للخصم منه:
        1. الرف الرئيسي (Primary)
        2. أول رف مرتبط بالصنف
        3. أول رف به رصيد فعلي (StockQuant)
        4. أول رف متاح في النظام للشركة (Fallback)
        """
        from apps.item_master.models import MaterialLocation
        from apps.wms.models import StockQuant, StorageBin
        
        # 1. الرف الرئيسي
        loc = MaterialLocation.objects.filter(material=material, material__opco=self.opco, is_primary=True).first()
        if loc: return loc.storage_bin
        
        # 2. أي رف مرتبط بالصنف
        loc = MaterialLocation.objects.filter(material=material, material__opco=self.opco).first()
        if loc: return loc.storage_bin
        
        # 3. أي رف به رصيد
        quant = StockQuant.objects.filter(material=material, opco=self.opco, quantity__gt=0).first()
        if quant: return quant.storage_bin
        
        # 4. الملاذ الأخير: أي رف متاح في الشركة
        fallback_bin = StorageBin.objects.filter(storage_location__plant__opco=self.opco, is_active=True).first()
        return fallback_bin

    def __str__(self):
        return f"Order {self.order_ref} - {self.status}"


class POSOrderLine(models.Model):
    """
    المنتجات المطلوبة داخل الفاتورة
    """
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name='lines')
    material = models.ForeignKey(Material, on_delete=models.CASCADE) # Finished Good
    qty = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    # مثال لتسجيل الملاحظات للمطبخ: "بدون بصل، استواء كامل"
    kitchen_notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.qty}x {self.material.name} ({self.order.order_ref})"


class RestaurantFloor(models.Model):
    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, help_text="اسم الدور (مثال: الدور الأول)")
    number = models.IntegerField(default=1, help_text="رقم ترتيب الدور")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['number']
        unique_together = ('opco', 'number')

    def __str__(self):
        return f"{self.name} ({self.opco.name})"


class RestaurantTable(models.Model):
    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE)
    floor = models.ForeignKey(RestaurantFloor, on_delete=models.CASCADE, related_name='tables')
    number = models.CharField(max_length=50, help_text="رقم أو اسم الترابيزة")
    seats_limit = models.IntegerField(default=4, help_text="عدد الكراسي المخصصة للترابيزة")
    current_guests = models.IntegerField(default=0, help_text="عدد الأفراد المتواجدين حالياً")
    
    STATUS_CHOICES = [
        ('available', 'متاح (Available)'),
        ('occupied', 'مشغول (Occupied)'),
        ('reserved', 'محجوز (Reserved)'),
        ('cleaning', 'تنظيف (Cleaning)')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    SHAPE_CHOICES = [
        ('square', 'مربع (Square)'),
        ('round', 'دائري (Round)')
    ]
    shape = models.CharField(max_length=20, choices=SHAPE_CHOICES, default='square')
    
    # الإحداثيات بالنسبة المئوية لوضع الترابيزة على الخريطة
    position_x = models.IntegerField(default=50, help_text="الموقع الأفقي X (%)")
    position_y = models.IntegerField(default=50, help_text="الموقع الرأسي Y (%)")
    
    active_order = models.ForeignKey('POSOrder', null=True, blank=True, on_delete=models.SET_NULL, related_name='active_table')

    class Meta:
        unique_together = ('opco', 'floor', 'number')
        ordering = ['number']

    def __str__(self):
        return f"Table {self.number} - Floor {self.floor.name}"


