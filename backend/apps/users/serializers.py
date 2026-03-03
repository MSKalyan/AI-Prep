from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


# =====================================
# User Registration
# =====================================

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
                "password": "Passwords do not match"
            })
            
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        return user


# =====================================
# User Login
# =====================================

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError(
                'Must include "email" and "password"'
            )

        # IMPORTANT:
        # Works only if USERNAME_FIELD = 'email'
        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError('Invalid credentials')

        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')

        attrs['user'] = user
        return attrs


# =====================================
# User Profile Serializer
# =====================================

class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
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
