from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.urls import reverse
from core.context_processors import global_context
from items.models import Category, Item
from borrowing.models import BorrowRequest, Notification


class CoreContextProcessorTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='tester', password='password123')

    def test_anonymous_user_unread_notifications_count(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        context = global_context(request)
        self.assertEqual(context['unread_notifications_count'], 0)

    def test_authenticated_user_unread_notifications_count(self):
        Notification.objects.create(recipient=self.user, message='Message 1', is_read=False)
        Notification.objects.create(recipient=self.user, message='Message 2', is_read=False)
        Notification.objects.create(recipient=self.user, message='Message 3', is_read=True)

        request = self.factory.get('/')
        request.user = self.user
        context = global_context(request)
        self.assertEqual(context['unread_notifications_count'], 2)


class HomeViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='homelender', password='password123')
        self.category = Category.objects.create(name='Woodworking')
        self.item = Item.objects.create(
            owner=self.user,
            category=self.category,
            title='Band Saw',
            description='Precision band saw'
        )

    def test_home_page_renders_categories_and_trending(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
        self.assertContains(response, 'Woodworking')
        self.assertContains(response, 'Band Saw')
        self.assertIn('categories', response.context)
        self.assertIn('most_borrowed', response.context)
