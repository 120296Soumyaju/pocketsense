from rest_framework.test import APITestCase
from rest_framework import status
from .models import Student, Group

class GroupTestCase(APITestCase):
    def setUp(self):
        # Create sample students
        self.student1 = Student.objects.create_user(
            username="student1", password="password123", email="student1@example.com"
        )
        self.student2 = Student.objects.create_user(
            username="student2", password="password123", email="student2@example.com"
        )

    def test_create_group(self):
        # Define the request payload
        payload = {
            'name': 'Test Group',
            'group_type': 'trip_groups',
            'members': [self.student1.id, self.student2.id],  # Pass existing Student IDs
        }

        # Make POST request to the endpoint
        response = self.client.post('/api/groups/', payload, format='json')

        # Assert the status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert the group was created in the database
        self.assertEqual(Group.objects.count(), 1)

        # Verify the response data
        response_data = response.json()
        self.assertEqual(response_data['name'], payload['name'])
        self.assertEqual(response_data['group_type'], payload['group_type'])
        self.assertEqual(len(response_data['members']), len(payload['members']))
