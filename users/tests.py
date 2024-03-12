from django.test import TestCase
from .models import Profile, CustomUser
from .serializers import ProfileSerializer, UserSerializer
from rest_framework import status
from rest_framework.test import APITestCase

class ProfileModelTest(TestCase):
    """
    Tests the model profile creation part. Making sure all data is saved to the database.
    It also makes sure methods are working and feeding the correct field with the number calculated.
    """
    def test_profile_creation(self):
        user = CustomUser.objects.create_user(username='testuser', password='testpass', email='testuser@example.com')
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
        user = CustomUser.objects.create_user(username='testuser', password='testpass', email='testuser@example.com')
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
            expected_bmr = 10 * profile.weight + 6.25 * (profile.height / 100) - 5 * profile.age + 5
        else:
            expected_bmr = 10 * profile.weight + 6.25 * (profile.height / 100) - 5 * profile.age - 161

        # Calculate expected TDEE
        expected_tdee = expected_bmr * activity_levels[profile.activity_level]

        calculated_tdee = profile.calculate_tdee()
        self.assertEqual(calculated_tdee, expected_tdee)

class ProfileModelUnitConversionTest(TestCase):
    def test_convert_units(self):
        user = CustomUser.objects.create(username='testuser', email='testuser@example.com', password='testpass')
        profile = Profile(
            user=user,
            gender='M',
            weight_unit='lb',
            height_unit='ft',
            weight='150', # 150 lbs is approximately 68.04 kg
            height='6\'0"', # 6 ft is approximately 1.83 meters
            activity_level='Sedentary',
            age=30
        )
        profile.save() # Save the profile to apply the conversion
        profile = Profile.objects.get(id=profile.id)

        self.assertAlmostEqual(float(profile.weight), 68.04, places=2)
        self.assertAlmostEqual(float(profile.height), 182.88, places=2) # Height should be in centimeters

class UserSerializerTest(APITestCase):
    """
    Testing the user serializer. The user model which was customized to make email unique becomes part of the user profile
    """
    def test_create_user(self):
        data = {'username': 'testuser', 'email': 'testuser@example.com', 'password': 'testpass'}
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.email, data['email'])
        self.assertTrue(user.check_password(data['password']))

class ProfileSerializerTest(APITestCase):
    """
    Tests a profile creation where the user enters their body fat manually
    """
    def test_create_profile_with_body_fat(self):
        profile_data = {
            'user': {'username': 'testuser', 'email': 'testuser@example.com', 'password': 'testpass'},
            'age': 30,
            'activity_level': 'Moderately Active',
            'weight': 150, 
            'weight_unit': 'lb', 
            'gender': 'M',
            'height': "6'0", 
            'height_unit': 'in', 
            'body_fat': 15,
        }
        serializer = ProfileSerializer(data=profile_data)
        is_valid = serializer.is_valid()

        if not is_valid:
            print(serializer.errors)  # Print the serializer's errors if it's not valid

        
        self.assertTrue(serializer.is_valid())
        profile = serializer.save()
        self.assertEqual(profile.user.username, profile_data['user']['username'])
        self.assertEqual(profile.age, profile_data['age'])
        self.assertEqual(profile.activity_level, profile_data['activity_level'])
        self.assertEqual(profile.weight, profile_data['weight'])
        self.assertEqual(profile.gender, profile_data['gender'])
        self.assertEqual(profile.height, profile_data['height'])

    """
    Tests a profile where the user does not know their body fat but would like it calculated
    """
    def test_calculate_body_fat(self):
        profile_data = {
            'user': {'username': 'testuser', 'email': 'testuser@example.com', 'password': 'testpass'},
            'age': 30,
            'activity_level': 'Moderately Active',
            'weight': 70,
            'weight_unit': 'kg',
            'height_unit': 'cm',
            'gender': 'M',
            'height': 175,
            'do_not_know_body_fat': True,
            'waist_measurement': 80,
            'hip_measurement': 100
        }
        serializer = ProfileSerializer(data=profile_data)
        
        is_valid = serializer.is_valid()
        if not is_valid:
            print(serializer.errors)
        self.assertTrue(is_valid)
        profile = serializer.save()

        expected_body_fat = serializer.calculate_body_fat(profile_data['waist_measurement'], profile_data['hip_measurement'])
        self.assertEqual(profile.body_fat, expected_body_fat)

    """
    Tests a profile where the user does not enter body fat
    """
    def test_create_profile_without_body_fat(self):
        profile_data = {
            'user': {'username': 'testuser', 'email': 'testuser@example.com', 'password': 'testpass'},
            'age': 30,
            'activity_level': 'Moderately Active',
            'weight_unit':'kg',
            'weight': 70,
            'gender': 'M',
            'height_unit':'cm',
            'height': 175,
        }
        serializer = ProfileSerializer(data=profile_data)
        
        self.assertTrue(serializer.is_valid())
        profile = serializer.save()
        self.assertEqual(profile.user.username, profile_data['user']['username'])
        self.assertEqual(profile.age, profile_data['age'])
        self.assertEqual(profile.activity_level, profile_data['activity_level'])
        self.assertEqual(profile.weight, str(profile_data['weight'])) # Convert weight to string before comparing
        self.assertEqual(profile.gender, profile_data['gender'])
        self.assertEqual(profile.height, str(profile_data['height'])) # Convert height to string before comparing
        self.assertIsNone(profile.body_fat)

class ProfileCreationTest(APITestCase):
    """
    Testing the profile creation itself
    """
    def test_create_profile(self):
        user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testpass'
        }

        profile_data = {
            'user': user_data,
            'age': 30,
            'activity_level': 'Moderately Active',
            'weight': '70',
            'weight_unit': 'kg',
            'gender': 'M',
            'height': '175',
            'height_unit': 'cm',
            'body_fat': 15,
        }
        response = self.client.post('/profiles/', data=profile_data, format='json')

        # Print the response data and status code

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['age'], profile_data['age'])
        self.assertEqual(response.data['activity_level'], profile_data['activity_level'])
        self.assertEqual(response.data['weight'], profile_data['weight'])
        self.assertEqual(response.data['weight_unit'], profile_data['weight_unit'])
        self.assertEqual(response.data['gender'], profile_data['gender'])
        self.assertEqual(response.data['height'], profile_data['height'])
        self.assertEqual(response.data['height_unit'], profile_data['height_unit'])
        self.assertEqual(response.data['body_fat'], profile_data['body_fat'])