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
# 2. محرك الطلبات ونقاط البيع (POS Orders Engine)
# =========================================================

class POSSession(models.Model):
    """
    وردية الكاشير
    """
    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE)
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    cashier_name = models.CharField(max_length=100)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return f"Session {self.session_id} - {self.cashier_name}"


class POSOrder(models.Model):
    """
    طلب العميل الرئيسي
    """
    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE)
    session = models.ForeignKey(POSSession, on_delete=models.CASCADE, related_name='orders')
    order_ref = models.CharField(max_length=50, unique=True)
    
    ORDER_TYPES = [
        ('dine_in', 'Dine In (محلي)'),
        ('takeaway', 'Takeaway (سفري)'),
        ('delivery', 'Delivery (توصيل)')
    ]
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='takeaway')
    table_number = models.CharField(max_length=20, null=True, blank=True)
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('draft', 'Draft (لم يدفع)'),
        ('paid', 'Paid (تم الدفع - في المطبخ)'),
        ('done', 'Done (جاهز للاستلام)'),
        ('cancelled', 'Cancelled (ملغي)')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # لمعرفة هل تم خصم المخزون بالفعل أم لا في الخلفية؟
    inventory_deducted = models.BooleanField(default=False)

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

