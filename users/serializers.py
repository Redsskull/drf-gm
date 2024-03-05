from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    activity_level = serializers.CharField()
    body_fat = serializers.FloatField(required=False)
    waist_circumference = serializers.FloatField(required=False)
    hip_circumference = serializers.FloatField(required=False)

    class Meta:
        model = Profile
        fields = ('user', 'gender', 'weight', 'height', 'activity_level', 'body_fat', 'waist_circumference', 'hip_circumference', 'tdee')
        depth = 1

    def validate(self, data):
        # Check if both body fat and measurements are provided
        if 'body_fat' in data and ('waist_circumference' in data or 'hip_circumference' in data):
            raise serializers.ValidationError("Please provide either body fat percentage or waist and hip circumferences, not both.")

        # If body fat is not provided, calculate it using measurements
        if 'body_fat' not in data:
            waist_circumference = data.get('waist_circumference')
            hip_circumference = data.get('hip_circumference')
            if waist_circumference and hip_circumference:
                # Implement the Deurenberg formula for body fat estimation
                body_fat = self.calculate_body_fat(waist_circumference, hip_circumference)
                data['body_fat'] = body_fat
            else:
                raise serializers.ValidationError("Either body fat percentage or waist and hip circumferences must be provided.")

        return data

    def calculate_body_fat(self, waist_circumference, hip_circumference):
        # Deurenberg formula for body fat estimation
        body_fat = (waist_circumference - hip_circumference) / waist_circumference * 100
        return body_fat

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer().create(user_data)
        profile = Profile(user=user, **validated_data)
        profile.save()
        return profile