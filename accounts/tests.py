from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import datetime

from accounts.models import Profile
from accounts.forms import UserSignupForm, UserLoginForm, ProfileUpdateForm
from accounts.services import get_reputation_stats, get_most_borrowed_items
from items.models import Category, Item
from borrowing.models import BorrowRequest


class AccountsFormsTest(TestCase):
    def test_signup_form_valid(self):
        form_data = {
            'username': 'newuser123',
            'email': 'newuser@example.com',
            'password1': 'StrongPass987!',
            'password2': 'StrongPass987!',
            'neighborhood': 'Highland Park',
            'bio': 'Lover of woodworking and lawncare.',
        }
        form = UserSignupForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.profile.neighborhood, 'Highland Park')
        self.assertEqual(user.profile.bio, 'Lover of woodworking and lawncare.')

    def test_profile_update_form_valid(self):
        user = User.objects.create_user(username='updater', password='password123')
        form_data = {
            'neighborhood': 'Greenwood Hills',
            'bio': 'Restoring vintage furniture.',
        }
        form = ProfileUpdateForm(data=form_data, instance=user.profile)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.neighborhood, 'Greenwood Hills')


class AccountsViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='johndoe',
            email='john@example.com',
            password='TestPassword123!'
        )

    def test_signup_view_get_and_post(self):
        response = self.client.get(reverse('accounts:signup'))
        self.assertEqual(response.status_code, 200)

        post_data = {
            'username': 'janedoe',
            'email': 'jane@example.com',
            'password1': 'SecretPassword123!',
            'password2': 'SecretPassword123!',
            'neighborhood': 'Sunnyside',
            'bio': 'Gardening expert',
        }
        post_response = self.client.post(reverse('accounts:signup'), post_data)
        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(User.objects.filter(username='janedoe').exists())

    def test_login_and_logout_views(self):
        login_response = self.client.post(reverse('accounts:login'), {
            'username': 'johndoe',
            'password': 'TestPassword123!'
        })
        self.assertEqual(login_response.status_code, 302)

        logout_response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(logout_response.status_code, 302)

    def test_profile_view_and_profile_edit_view(self):
        self.client.login(username='johndoe', password='TestPassword123!')
        profile_response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(profile_response.status_code, 200)
        self.assertContains(profile_response, 'johndoe')

        edit_response = self.client.post(reverse('accounts:profile_edit'), {
            'neighborhood': 'Riverside',
            'bio': 'Updated bio description',
        })
        self.assertEqual(edit_response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.neighborhood, 'Riverside')


class AccountsModelAndSignalTest(TestCase):
    def test_user_creation_auto_creates_profile(self):
        user = User.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='secretpassword123'
        )
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, Profile)
        self.assertEqual(user.profile.neighborhood, '')

    def test_profile_update_on_user_save(self):
        user = User.objects.create_user(username='bob', password='password123')
        user.profile.neighborhood = 'Pine Hills'
        user.profile.bio = 'Woodworking enthusiast'
        user.profile.save()

        user.first_name = 'Robert'
        user.save()

        refreshed_profile = Profile.objects.get(user=user)
        self.assertEqual(refreshed_profile.neighborhood, 'Pine Hills')
        self.assertEqual(refreshed_profile.bio, 'Woodworking enthusiast')


class AccountsServicesTest(TestCase):
    def setUp(self):
        self.lender = User.objects.create_user(username='lender_pro', password='password123')
        self.borrower = User.objects.create_user(username='borrower_pro', password='password123')
        self.category = Category.objects.create(name='Woodworking')

        self.item1 = Item.objects.create(
            owner=self.lender,
            category=self.category,
            title='Table Saw',
            description='10-inch contractor table saw.'
        )
        self.item2 = Item.objects.create(
            owner=self.lender,
            category=self.category,
            title='Planer',
            description='13-inch thickness planer.'
        )

    def test_reputation_stats_no_borrows(self):
        stats = get_reputation_stats(self.borrower)
        self.assertEqual(stats['total_borrows'], 0)
        self.assertIsNone(stats['on_time_rate'])
        self.assertEqual(stats['damaged_returns'], 0)
        self.assertEqual(stats['items_owned'], 0)

    def test_reputation_stats_with_borrows(self):
        today = timezone.now().date()
        # On-time return
        BorrowRequest.objects.create(
            item=self.item1,
            borrower=self.borrower,
            start_date=today - datetime.timedelta(days=10),
            end_date=today - datetime.timedelta(days=5),
            status='returned',
            returned_at=timezone.now() - datetime.timedelta(days=6),
            return_condition='good'
        )
        # Late return with worn condition
        BorrowRequest.objects.create(
            item=self.item2,
            borrower=self.borrower,
            start_date=today - datetime.timedelta(days=4),
            end_date=today - datetime.timedelta(days=2),
            status='returned',
            returned_at=timezone.now(),
            return_condition='worn'
        )

        stats = get_reputation_stats(self.borrower)
        self.assertEqual(stats['total_borrows'], 2)
        self.assertEqual(stats['on_time_rate'], 50)
        self.assertEqual(stats['damaged_returns'], 1)
        self.assertEqual(stats['items_owned'], 0)

    def test_get_most_borrowed_items(self):
        today = timezone.now().date()
        # item1 has 2 borrows
        BorrowRequest.objects.create(
            item=self.item1,
            borrower=self.borrower,
            start_date=today,
            end_date=today + datetime.timedelta(days=1),
            status='approved'
        )
        BorrowRequest.objects.create(
            item=self.item1,
            borrower=self.borrower,
            start_date=today + datetime.timedelta(days=2),
            end_date=today + datetime.timedelta(days=3),
            status='returned'
        )

        # item2 has 1 borrow
        BorrowRequest.objects.create(
            item=self.item2,
            borrower=self.borrower,
            start_date=today,
            end_date=today + datetime.timedelta(days=1),
            status='active'
        )

        # item3 is soft-deleted and shouldn't appear
        deleted_item = Item.objects.create(
            owner=self.lender,
            category=self.category,
            title='Old Sanders',
            description='Orbital sander',
            is_deleted=True
        )
        BorrowRequest.objects.create(
            item=deleted_item,
            borrower=self.borrower,
            start_date=today,
            end_date=today + datetime.timedelta(days=1),
            status='returned'
        )

        most_borrowed = get_most_borrowed_items(limit=5)
        self.assertEqual(len(most_borrowed), 2)
        self.assertEqual(most_borrowed[0].id, self.item1.id)
        self.assertEqual(most_borrowed[0].borrow_count, 2)
        self.assertEqual(most_borrowed[1].id, self.item2.id)
        self.assertEqual(most_borrowed[1].borrow_count, 1)
