from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from users.models import Profile
from .views import team_members_list
from django.contrib.auth.models import AnonymousUser

class TeamMembersListTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user1 = User.objects.create_user(username='user1', password='password', first_name='User', last_name='One')
        self.profile1 = Profile.objects.create(user=self.user1, company='TestCorp')
        
        self.user2 = User.objects.create_user(username='user2', password='password', first_name='User', last_name='Two')
        self.profile2 = Profile.objects.create(user=self.user2, company='TestCorp')
        
        self.user3 = User.objects.create_user(username='user3', password='password', first_name='User', last_name='Three')
        self.profile3 = Profile.objects.create(user=self.user3, company='AnotherCorp')

        self.user4 = User.objects.create_user(username='user4', password='password', first_name='User', last_name='Four')
        # User 4 has no profile/company

    def test_team_members_list_with_company(self):
        request = self.factory.get('/team/')
        request.user = self.user1
        response = team_members_list(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Two')
        self.assertNotContains(response, 'User One') # Should not include self
        self.assertNotContains(response, 'User Three') # Should not include user from another company

    def test_team_members_list_without_company(self):
        # Test for a user who doesn't have a company in their profile
        user_no_company = User.objects.create_user(username='user5', password='password')
        Profile.objects.create(user=user_no_company, company='') # Profile with empty company
        
        request = self.factory.get('/team/')
        request.user = user_no_company
        response = team_members_list(request)
        
        self.assertEqual(response.status_code, 200)
        # Should contain all other users
        self.assertContains(response, 'User One')
        self.assertContains(response, 'User Two')
        self.assertContains(response, 'User Three')
        self.assertContains(response, 'User Four')
        self.assertNotContains(response, 'user5') # Should not include self

    def test_team_members_list_no_profile(self):
        # Test for a user who doesn't have a profile at all
        request = self.factory.get('/team/')
        request.user = self.user4
        response = team_members_list(request)
        
        self.assertEqual(response.status_code, 200)
        # Should contain all other users
        self.assertContains(response, 'User One')
        self.assertContains(response, 'User Two')
        self.assertContains(response, 'User Three')
        self.assertNotContains(response, 'User Four') # Should not include self

    def test_team_members_list_unauthenticated(self):
        # This view has @login_required, so it should redirect
        request = self.factory.get('/team/')
        request.user = AnonymousUser()
        # In a real request/response cycle, the decorator would redirect.
        # Calling the view directly will raise an exception or behave differently
        # without the full middleware stack. A full client test is better for this.
        # For now, we'll just check that it doesn't return a 200 with the list.
        # A proper test for login_required would use self.client.get('/team/')
        response = self.client.get('/team/')
        self.assertEqual(response.status_code, 302) # 302 is redirect
        self.assertTrue(response.url.startswith('/login/'))
