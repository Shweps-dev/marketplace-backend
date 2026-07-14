from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.users.models import User


class Category(models.Model):
    """
    Категории с вложенностью (self-referential FK).
    Пример: Электроника → Смартфоны → iPhone
    parent=None означает корневую категорию.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "categories"
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name


class Product(models.Model):
    """
    Основная модель товара.
    Связана с категорией через FK и с изображениями через отдельную таблицу.
    """
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="products"
    )
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(100)]
    )
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]

    @property
    def discounted_price(self):
        """Цена с учётом скидки."""
        if self.discount_percent:
            return self.price * (1 - self.discount_percent / 100)
        return self.price

    @property
    def in_stock(self):
        return self.stock > 0

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    """
    Изображения вынесены в отдельную таблицу —
    у одного товара может быть несколько фото.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    is_main = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "product_images"
        ordering = ["order"]

    def __str__(self):
        return f"Image for {self.product.name}"


class Review(models.Model):
    """Отзывы покупателей с рейтингом от 1 до 5."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reviews"
        # Один пользователь — один отзыв на товар
        unique_together = ("product", "user")

    def __str__(self):
        return f"{self.user.email} → {self.product.name} ({self.rating}★)"
