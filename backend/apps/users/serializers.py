from rest_framework import serializers
from .models import User

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'password',
            'password_confirm',
            'full_name',
            'target_exam',
            'exam_date',
            'study_hours_per_day'
        )

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({
                "password": "Passwords do not match"  # nosec B105
            })
            
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        return user

class UserProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'password',
            'full_name',
            'phone',
            'target_exam',
            'exam_date',
            'study_hours_per_day',
            'is_premium',
            'subscription_end_date',
            'created_at',
            'last_activity'
        )

        read_only_fields = (
            'id',
            'email',
            'created_at',
            'is_premium',
            'subscription_end_date'
        )

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password and str(password).strip():
            user.set_password(password)
            user.save(update_fields=["password"])

        return user
