from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import CustomUser, PasswordResetRequest


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Credenciales incorrectas.")
        if not user.is_active:
            raise serializers.ValidationError("La cuenta está desactivada.")
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "avatar": user.avatar.url if user.avatar else None,
            },
        }


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = CustomUser.objects.get(email=value, is_active=True)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No existe ningún usuario activo con ese email.")
        self.context["reset_user"] = user
        return value


class PasswordResetResolveSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8)


class PasswordResetRequestDetailSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = PasswordResetRequest
        fields = ["id", "user_email", "user_name", "user_role", "status", "created_at", "resolved_at"]


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ["email", "full_name", "role", "password"]

    def validate(self, attrs):
        requester = self.context["request"].user
        target_role = attrs.get("role")
        if requester.role == CustomUser.EMPLOYEE:
            allowed = (CustomUser.CLIENT, CustomUser.CONTENT_MAKER)
            if target_role not in allowed:
                raise serializers.ValidationError(
                    {"role": "Los empleados solo pueden crear usuarios de tipo 'client' o 'content_maker'."}
                )
        return attrs

    def create(self, validated_data):
        requester = self.context["request"].user
        password = validated_data.pop("password")
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.created_by = requester
        if validated_data["role"] == CustomUser.ADMIN:
            user.is_staff = True
            user.is_superuser = True
        user.save()
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ["id", "email", "full_name", "role", "avatar", "is_active", "created_at", "created_by"]

    def get_created_by(self, obj):
        if obj.created_by:
            return obj.created_by.full_name
        return None


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["full_name", "avatar", "is_active", "role"]

    def validate(self, attrs):
        requester = self.context["request"].user
        if "role" in attrs and not requester.is_admin:
            raise serializers.ValidationError({"role": "Solo los administradores pueden cambiar el rol."})
        return attrs

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if instance.role == CustomUser.ADMIN:
            instance.is_staff = True
            instance.is_superuser = True
        instance.save()
        return instance
