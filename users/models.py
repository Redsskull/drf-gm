from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

class Profile(models.Model):
    """
    Every user in this app will have their profile. It expands the User model of django into a very large profile model.
    the model will store the users fitness measurements during registration. another model in another app will keep track of progress using this model as a foreign key.
    """
    WEIGHT_UNITS = [
        ('kg', 'Kilograms'),
        ('lb', 'Pounds'),
    ]
    HEIGHT_UNITS = [
        ('cm', 'Centimeters'),
        ('ft', 'Feet'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    weight_unit = models.CharField(max_length=3, choices=WEIGHT_UNITS, default='kg')
    height_unit = models.CharField(max_length=3, choices=HEIGHT_UNITS, default='cm')
    height_feet = models.IntegerField(null=True, blank=True)
    height_inches = models.IntegerField(null=True, blank=True)
    weight = models.CharField(max_length=10)
    height = models.CharField(max_length=10)
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
    body_fat = models.FloatField(null=True, blank=True) 
    age = models.IntegerField()
    TDEE = models.FloatField(blank=True, null=True) # Calculated field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):

        # Update height and weight units first
        self.height_unit = self.height_unit or 'cm'
        self.weight_unit = self.weight_unit or 'kg'
        
        # Convert weight to kilograms if not already
        if self.weight_unit == 'lb':
            pounds = float(str(self.weight).replace('lb', ''))
            self.weight = str(pounds * 0.45359237)  # Convert pounds to kilograms
            self.weight_unit = 'kg'  # Update weight unit in memory

        # Convert height to centimeters if not already
        if self.height_unit == 'ft':
            feet = self.height_feet or 0
            inches = self.height_inches or 0
            total_height_in_inches = feet * 12 + inches
            self.height = str(total_height_in_inches * 2.54)  # Convert inches to centimeters
            self.height_unit = 'cm'  # Update height unit in memory

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

        # Convert weight and height to floats
        weight = float(self.weight)
        height = float(self.height) 

        # Calculate BMR
        if self.gender == 'M':
            bmr = 10 * weight + 6.25 * height - 5 * self.age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * self.age - 161

        # Calculate TDEE
        activity_level_multiplier = activity_levels[self.activity_level]
        TDEE = bmr * activity_level_multiplier

        return TDEE
     
        

    def __str__(self):  
        return self.user.username