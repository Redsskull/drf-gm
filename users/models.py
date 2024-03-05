from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    WEIGHT_UNITS = [
        ('kg', 'Kilograms'),
        ('lbs', 'Pounds'),
    ]
    HEIGHT_UNITS = [
        ('cm', 'Centimeters'),
        ('in', 'Inches'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    weight_unit = models.CharField(max_length=2, choices=WEIGHT_UNITS, default='kg')
    height_unit = models.CharField(max_length=2, choices=HEIGHT_UNITS, default='m')
    weight = models.FloatField()
    height = models.FloatField()
    activity_level = models.CharField(
        max_length=20,
        choices=[
            ('Sedentary', 'Sedentary'),
            ('Lightly Active', 'Lightly Active'),
            ('Moderately Active', 'Moderately Active'),
            ('Very Active', 'Very Active'),
            ('Extra Active', 'Extra Active'),
        ]
    )
    body_fat = models.FloatField(null=True, blank=True) #TODO this needs to be a percentege entry for the user
    age = models.IntegerField()
    TDEE = models.FloatField(blank=True, null=True) # Calculated field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Convert weight to kilograms if not already
        if self.weight_unit == 'lb':
            self.weight = self.weight * 0.453592 # Convert pounds to kilograms

        # Convert height to meters if not already
        if self.height_unit == 'ft':
            self.height = self.height * 0.3048 # Convert feet to meters
            
        # Calculate TDEE here based on the user's input
        self.TDEE = self.calculate_tdee()
        super().save(*args, **kwargs)

    def calculate_tdee(self):
        # Define activity level multipliers
        activity_levels = {
            'Sedentary': 1.2,
            'Lightly Active': 1.375,
            'Moderately Active': 1.55,
            'Very Active': 1.725,
            'Extra Active': 1.9
        }

        # Calculate BMR
        if self.gender == 'M':
            bmr = (10 * self.weight + 6.25 * self.height - 5 * self.user.profile.age + 5) * 1.55
        else:
            bmr = (10 * self.weight + 6.25 * self.height - 5 * self.user.profile.age - 161) * 1.55

        # Calculate TDEE
        TDEE = bmr * activity_levels[self.activity_level]
        return TDEE

#TODO give user a choice of units to use and input for weight and height