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
    weight = serializers.FloatField(
        error_messages={
            'invalid': "Please enter a valid weight.",
            'required': "Weight is required."
        }
    )
    body_fat = serializers.FloatField(required=False)
    do_not_know_body_fat = serializers.BooleanField(required=False)
    waist_measurement = serializers.FloatField(required=False)
    hip_measurement = serializers.FloatField(required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    TDEE = serializers.FloatField(read_only=True)

    class Meta:
        model = Profile
        fields = ('user', 'gender','weight_unit', 'height_unit', 'weight', 'height', 'activity_level', 'body_fat', 'do_not_know_body_fat', 'waist_measurement', 'hip_measurement', 'TDEE', 'created_at', 'updated_at')
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

        # New validation for weight and height based on the selected unit
        weight_unit = data.get('weight_unit')
        height_unit = data.get('height_unit')
        weight = data.get('weight')
        height = data.get('height')

        if weight_unit == 'lbs' and (weight < 1 or weight > 1000): # Assuming a reasonable range for pounds
            raise serializers.ValidationError("Weight in pounds must be between 1 and 1000.")
        if height_unit == 'ft' and (height < 1 or height > 10): # Assuming a reasonable range for feet
            raise serializers.ValidationError("Height in feet must be between 1 and 10.")

        return data

    def calculate_body_fat(self, waist_measurement, hip_measurement):
        # Deurenberg formula for body fat estimation
        body_fat = (waist_measurement - hip_measurement) / waist_measurement * 100
        return body_fat
    
    def validate_body_fat(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Body fat percentage must be between 0 and 100.")
        return value

    def create(self, validated_data):
        # Extract 'do_not_know_body_fat', 'waist_measurement', and 'hip_measurement' from the data
        do_not_know_body_fat = validated_data.pop('do_not_know_body_fat', False)
        waist_measurement = validated_data.pop('waist_measurement', None)
        hip_measurement = validated_data.pop('hip_measurement', None)
        
        # Extract 'user' data for creating the User instance
        user_data = validated_data.pop('user')
        user = UserSerializer().create(user_data)
        
        # Create the Profile instance without 'do_not_know_body_fat', 'waist_measurement', 'hip_measurement', and 'user'
        profile = Profile.objects.create(user=user, **validated_data)
        
        # If 'do_not_know_body_fat' is False and both waist and hip measurements are provided, calculate body fat
        if not do_not_know_body_fat and waist_measurement is not None and hip_measurement is not None:
            # Calculate body fat using the provided measurements
            body_fat = self.calculate_body_fat(waist_measurement, hip_measurement)
            # Update the 'body_fat' field of the Profile instance
            profile.body_fat = body_fat
            profile.save()
        
        return profile
