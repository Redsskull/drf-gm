from django.test import TestCase
from rest_framework.test import APIClient
from .models import Profile

class ProfileTestCase(TestCase):
    """
    the test names mostly speak for themselves. I'm testing the creation of a profile with and without body fat, with height in feet and inches, and the TDEE calculation."""
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testpassword'
        }
        self.profile_data = {
            'user': self.user_data,
            'gender': 'M',
            'weight_unit': 'kg',
            'height_unit': 'cm',
            'weight': '70',
            'height': '170',
            'activity_level': 'Sedentary',
            'age': 30
        }

    def test_create_profile_with_body_fat(self):
        self.profile_data['body_fat'] = 15.0
        response = self.client.post('/profiles/', self.profile_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(Profile.objects.get().body_fat, 15.0)

    def test_create_profile_without_body_fat(self):
        response = self.client.post('/profiles/', self.profile_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Profile.objects.count(), 1)
        self.assertIsNone(Profile.objects.get().body_fat)

    def test_create_profile_with_height_in_feet_and_inches(self):
        self.profile_data.update({
            'height_unit': 'ft',
            'height_feet': 5,
            'height_inches': 7
        })
        response = self.client.post('/profiles/', self.profile_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Profile.objects.count(), 1)
        profile = Profile.objects.get()
        self.assertEqual(profile.height_unit, 'cm')
        self.assertAlmostEqual(float(profile.height), 170.18, places=2)  # 5'7" is approximately 170.18 cm

    def test_tdee_calculation(self):
        self.profile_data.update({
            'weight': 70,  # kg
            'height': 170,  # cm
            'age': 25,
            'gender': 'M',
            'activity_level': 'Sedentary'
        })
        response = self.client.post('/profiles/', self.profile_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Profile.objects.count(), 1)
        profile = Profile.objects.get()
        expected_bmr = (10 * 70) + (6.25 * 170) - (5 * 25) + 5  # Mifflin-St Jeor Equation for men
        expected_tdee = expected_bmr * 1.2  # Sedentary activity level
        self.assertAlmostEqual(profile.TDEE, expected_tdee, places=2)

    def test_tdee_calculation_with_feet_and_pounds(self):
        self.profile_data.update({
            'weight': 154,  # pounds
            'weight_unit': 'lb',
            'height_feet': 5,
            'height_inches': 7,
            'height_unit': 'ft',
            'age': 25,
            'gender': 'M',
            'activity_level': 'Sedentary'
        })
        response = self.client.post('/profiles/', self.profile_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Profile.objects.count(), 1)
        profile = Profile.objects.get()
        expected_bmr = (10 * 70) + (6.25 * 170) - (5 * 25) + 5  # Mifflin-St Jeor Equation for men
        expected_tdee = expected_bmr * 1.2  # Sedentary activity level
        self.assertAlmostEqual(profile.TDEE, expected_tdee, places=3)