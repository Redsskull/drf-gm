from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
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
    body_fat = models.FloatField(null=True, blank=True)
    age = models.IntegerField()
    TDEE = models.FloatField(blank=True, null=True) # Calculated field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
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

#TODO give user a choice of units to use.