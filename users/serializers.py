from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.password_validation import validate_password
import re
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    class Meta:
        model = CustomUser
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
    """
    this and the user serializer above will work together to make sure the profile is validated, has no duplicates, body fat if not know is calucalted along with of course a TDEE.
    With the methods in the model and the validate and create methods, what I'm attempting to do is create a user profile with a tdee, use the measurments the user prefers(and convert them for easier math) and change the input display based on selection
    """
    user = UserSerializer()
    age = serializers.IntegerField()
    activity_level = serializers.ChoiceField(choices=Profile._meta.get_field('activity_level').choices)
    weight = serializers.CharField(
        error_messages={
            'invalid': "Please enter a valid weight.",
            'required': "Weight is required."
        }
    )
    height = serializers.CharField(
        required=False,
        error_messages={
            'invalid': "Please enter a valid height in the format '5'9\"'.",
            'required': "Height is required."
        }
    )
    height_feet = serializers.IntegerField(required=False)
    height_inches = serializers.IntegerField(required=False)
    body_fat = serializers.FloatField(required=False)
    do_not_know_body_fat = serializers.BooleanField(required=False)
    waist_measurement = serializers.FloatField(required=False)
    hip_measurement = serializers.FloatField(required=False)
    weight_unit = serializers.ChoiceField(choices=Profile._meta.get_field('weight_unit').choices)
    height_unit = serializers.ChoiceField(choices=Profile._meta.get_field('height_unit').choices)

    class Meta:
        model = Profile
        fields = ('user', 'gender','weight_unit', 'height_unit', 'weight', 'height', 'activity_level', 'body_fat', 'do_not_know_body_fat', 'waist_measurement', 'hip_measurement', 'TDEE', 'created_at', 'updated_at', 'age', 'height_feet', 'height_inches')
        read_only_fields = ('do_not_know_body_fat','created_at', 'updated_at', 'TDEE')
        depth = 1


    def validate(self, data):
        do_not_know_body_fat = data.get('do_not_know_body_fat', False)
        waist_measurement = data.get('waist_measurement')
        hip_measurement = data.get('hip_measurement')

        if do_not_know_body_fat and (waist_measurement is None or hip_measurement is None):
            raise serializers.ValidationError("If you do not know your body fat percentage, waist and hip measurements must be provided.")
        elif do_not_know_body_fat and waist_measurement and hip_measurement:
            # Implement the Deurenberg formula for body fat estimation
            body_fat = self.calculate_body_fat(waist_measurement, hip_measurement)
            data['body_fat'] = body_fat

        # New validation for weight and height based on the selected unit
        weight = data.get('weight')
        height = data.get('height')
        height_feet = data.get('height_feet')
        height_inches = data.get('height_inches')
        height_unit = data.get('height_unit')

        if not weight.isdigit():
            raise serializers.ValidationError("Weight must be a numeric value.")
        if height_unit == 'ft' and (height_feet is None or height_inches is None):
            raise serializers.ValidationError("Both feet and inches must be provided when the unit is 'ft'.")
        if height_unit != 'ft' and not height:
            raise serializers.ValidationError("Height is required when the unit is not 'ft'.")
        
        # Convert height to centimeters if necessary
        if height_unit == 'ft':
            total_height_in_inches = height_feet * 12 + height_inches
            data['height'] = str(total_height_in_inches * 2.54)  # Convert inches to centimeters
            data['height_unit'] = 'cm'  # Update height unit in memory

        return data

    def calculate_body_fat(self, waist_measurement, hip_measurement):
        # Deurenberg formula for body fat estimation
        body_fat = (waist_measurement - hip_measurement) / waist_measurement * 100
        return body_fat
    

   
    def create(self, validated_data):
        # Extract 'do_not_know_body_fat', 'waist_measurement', and 'hip_measurement' from the data
        do_not_know_body_fat = validated_data.pop('do_not_know_body_fat', False)
        waist_measurement = validated_data.pop('waist_measurement', None)
        hip_measurement = validated_data.pop('hip_measurement', None)
            
        # Extract 'user' data for creating the User instance
        user_data = validated_data.pop('user')
        user = UserSerializer.create(UserSerializer(), validated_data=user_data)
        
        # Create the Profile instance without 'do_not_know_body_fat', 'waist_measurement', 'hip_measurement', and 'user'
        profile = Profile(user=user, **validated_data)
        profile.save()  # This will call the `save` method of your `Profile` model
        
        # If 'do_not_know_body_fat' is False and both waist and hip measurements are provided, calculate body fat
        if not do_not_know_body_fat and waist_measurement is not None and hip_measurement is not None:
            # Calculate body fat using the provided measurements
            body_fat = self.calculate_body_fat(waist_measurement, hip_measurement)
            # Update the 'body_fat' field of the Profile instance
            profile.body_fat = body_fat
            profile.save()
        
        return profile
    
    def update(self, instance, validated_data):
        # Extract weight and height units
        weight_unit = validated_data.pop('weight_unit', None)
        height_unit = validated_data.pop('height_unit', None)

        # Convert weight to kilograms if necessary
        if weight_unit == 'lb':
            validated_data['weight'] = validated_data['weight'] * 0.453592
            validated_data['weight_unit'] = 'kg'
        else:
            validated_data['weight'] = instance.weight

        # Convert height to meters if necessary
        if height_unit == 'ft':
            validated_data['height'] = validated_data['height'] * 0.3048
            validated_data['height_unit'] = 'm'
        else:
            validated_data['height'] = instance.height

        # Update the profile instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
