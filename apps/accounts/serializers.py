from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    """Register a new tenant or landlord account.

    Only the TENANT and LANDLORD roles are available through public
    registration. Administrator accounts are created administratively and must
    never be creatable through this endpoint.
    """

    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    role = serializers.ChoiceField(
        choices=[User.Role.TENANT, User.Role.LANDLORD],
        default=User.Role.TENANT,
    )

    def validate_email(self, value):
        email = value.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate_role(self, value):
        if value == User.Role.ADMIN:
            raise serializers.ValidationError(
                "Administrator accounts are created administratively, not by registration."
            )
        return value

    def validate_password(self, value):
        # Validate against Django's built-in password validators.
        validate_password(value, user=self.instance)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def to_representation(self, instance):
        return {
            "id": instance.pk,
            "email": instance.email,
            "full_name": instance.full_name,
            "phone": instance.phone or "",
            "role": instance.role,
        }
