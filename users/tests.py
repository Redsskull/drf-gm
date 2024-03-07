from django.test import TestCase
from .models import Profile
from django.contrib.auth.models import User
from .serializers import ProfileSerializer
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase
from .serializers import UserSerializer



class ProfileModelTest(TestCase):
    def test_profile_creation(self):
        user = User.objects.create_user(username='testuser', password='testpass')
        profile = Profile.objects.create(
            user=user,
            gender='M',
            weight_unit='kg',
            height_unit='cm',
            weight=70,
            height=175,
            activity_level='Moderately Active',
            age=30
        )
        self.assertIsInstance(profile, Profile)
        self.assertEqual(profile.__str__(), user.username)

    def test_calculate_tdee(self):
        user = User.objects.create_user(username='testuser', password='testpass')
        profile = Profile.objects.create(
            user=user,
            gender='M',
            weight_unit='kg',
            height_unit='cm',
            weight=70,
            height=175,
            activity_level='Moderately Active',
            age=30
        )

        # Define activity level multipliers
        activity_levels = {
            'Sedentary': 1.2,
            'Lightly Active': 1.375,
            'Moderately Active': 1.55,
            'Very Active': 1.725,
            'Extra Active': 1.9
        }

        # Calculate expected BMR
        if profile.gender == 'M':
            expected_bmr = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age + 5
        else:
            expected_bmr = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age - 161

        # Calculate expected TDEE
        expected_tdee = expected_bmr * activity_levels[profile.activity_level]

        calculated_tdee = profile.calculate_tdee()
        self.assertEqual(calculated_tdee, expected_tdee)

class UserSerializerTest(APITestCase):
    def test_create_user(self):
        data = {'username': 'testuser', 'email': 'testuser@example.com', 'password': 'testpass'}
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.email, data['email'])
        self.assertTrue(user.check_password(data['password']))

class ProfileSerializerTest(APITestCase):
    def test_create_profile(self):
        profile_data = {
            'user': {'username': 'testuser', 'email': 'testuser@example.com', 'password': 'testpass'},
            'age': 30,
            'activity_level': 'Moderately Active',
            'weight': 70,
            'gender': 'M',
            'height': 175,
            'body_fat': 15,
        }
        serializer = ProfileSerializer(data=profile_data)
        
        if not serializer.is_valid():
            print(serializer.errors)
        
        self.assertTrue(serializer.is_valid())
        profile = serializer.save()
        self.assertEqual(profile.user.username, profile_data['user']['username'])
        self.assertEqual(profile.age, profile_data['age'])
        self.assertEqual(profile.activity_level, profile_data['activity_level'])
        self.assertEqual(profile.weight, profile_data['weight'])
        self.assertEqual(profile.gender, profile_data['gender'])
        self.assertEqual(profile.height, profile_data['height'])

class ProfileSerializerTest(APITestCase):
    def test_calculate_body_fat(self):
        profile_data = {
            'user': {'username': 'testuser', 'email': 'testuser@example.com', 'password': 'testpass'},
            'age': 30,
            'activity_level': 'Moderately Active',
            'weight': 70,
            'gender': 'M',
            'height': 175,
            'do_not_know_body_fat': True,
            'waist_measurement': 80,
            'hip_measurement': 100
        }
        serializer = ProfileSerializer(data=profile_data)
        
        if not serializer.is_valid():
            print(serializer.errors)
        
        self.assertTrue(serializer.is_valid())
        profile = serializer.save()

        expected_body_fat = serializer.calculate_body_fat(profile_data['waist_measurement'], profile_data['hip_measurement'])
        print(f"Expected body fat: {expected_body_fat}")
        print(f"Actual body fat: {profile.body_fat}")
        self.assertEqual(profile.body_fat, expected_body_fat)



def test_create_profile(self):
    user_data = {
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'testpass'
    }
    user = User.objects.create_user(**user_data)
    self.client.force_authenticate(user=user)

    profile_data = {
        'user': user.id,
        'age': 30,
        'activity_level': 'Moderately Active',
        'weight': 70,
        'gender': 'M',
        'height': 175,
        'body_fat': 15,
    }
    response = self.client.post('/profiles/profiles/', data=profile_data, format='json')


    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    self.assertEqual(response.data['age'], profile_data['age'])
    self.assertEqual(response.data['activity_level'], profile_data['activity_level'])
    self.assertEqual(response.data['weight'], profile_data['weight'])
    self.assertEqual(response.data['gender'], profile_data['gender'])
    self.assertEqual(response.data['height'], profile_data['height'])

