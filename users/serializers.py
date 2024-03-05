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
    activity_level = serializers.ChoiceField(choices=Profile._meta.get_field('activity_level').choices)
    body_fat = serializers.FloatField(required=False)
    do_not_know_body_fat = serializers.BooleanField(required=False)
    waist_measurement = serializers.FloatField(required=False)
    hip_measurement = serializers.FloatField(required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    TDEE = serializers.FloatField(read_only=True)

    class Meta:
        model = Profile
        fields = ('user', 'gender', 'weight', 'height', 'activity_level', 'body_fat', 'do_not_know_body_fat', 'waist_measurement', 'hip_measurement', 'TDEE', 'created_at', 'updated_at')
        read_only_fields = ('do_not_know_body_fat',)
        depth = 1

    def validate(self, data):
        do_not_know_body_fat = data.get('do_not_know_body_fat', False)
        if do_not_know_body_fat:
            waist_measurement = data.get('waist_measurement')
            hip_measurement = data.get('hip_measurement')
            if waist_measurement and hip_measurement:
                # Implement the Deurenberg formula for body fat estimation
                body_fat = self.calculate_body_fat(waist_measurement, hip_measurement)
                data['body_fat'] = body_fat
            else:
                raise serializers.ValidationError("If you do not know your body fat percentage, waist and hip measurements must be provided.")
        elif 'body_fat' not in data:
            raise serializers.ValidationError("Either body fat percentage or 'do not know body fat' must be provided.")
        return data

    def calculate_body_fat(self, waist_measurement, hip_measurement):
        # Deurenberg formula for body fat estimation
        body_fat = (waist_measurement - hip_measurement) / waist_measurement * 100
        return body_fat

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer().create(user_data)
        profile = Profile(user=user, **validated_data)
        profile.save()
        return profile