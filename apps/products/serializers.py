from rest_framework import serializers
from .models import Category, Product, ProductImage, Review


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "parent", "image", "children")

    def get_children(self, obj):
        # Рекурсивно возвращаем дочерние категории
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "is_main", "order")


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "user_email", "rating", "comment", "created_at")
        read_only_fields = ("id", "user_email", "created_at")

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        validated_data["product_id"] = self.context["product_id"]
        return super().create(validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    """Компактный сериализатор для списка товаров."""
    main_image = serializers.SerializerMethodField()
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "price", "discount_percent",
            "discounted_price", "stock", "main_image", "category_name",
        )

    def get_main_image(self, obj):
        img = obj.images.filter(is_main=True).first() or obj.images.first()
        if img:
            request = self.context.get("request")
            return request.build_absolute_uri(img.image.url) if request else img.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Полный сериализатор для детальной страницы товара."""
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    avg_rating = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "description", "price", "discount_percent",
            "discounted_price", "stock", "in_stock", "category",
            "images", "reviews", "avg_rating", "created_at",
        )

    def get_avg_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)
