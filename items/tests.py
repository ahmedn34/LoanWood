from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from items.models import Category, Item
from items.forms import ItemForm
from borrowing.models import BorrowRequest
import datetime


class ItemsViewsTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='viewowner', password='password123')
        self.other = User.objects.create_user(username='viewother', password='password123')
        self.category = Category.objects.create(name='Woodworking Tools')
        self.item = Item.objects.create(
            owner=self.owner,
            category=self.category,
            title='Router Table',
            description='Precision woodworking router table.',
            condition='excellent'
        )

    def test_browse_items_view(self):
        response = self.client.get(reverse('items:browse'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Router Table')

        # Test search query
        search_res = self.client.get(reverse('items:browse') + '?q=Router')
        self.assertEqual(search_res.status_code, 200)
        self.assertContains(search_res, 'Router Table')

        # Test category filter
        cat_res = self.client.get(reverse('items:browse') + f'?category={self.category.slug}')
        self.assertEqual(cat_res.status_code, 200)
        self.assertContains(cat_res, 'Router Table')

    def test_item_detail_view(self):
        response = self.client.get(reverse('items:detail', kwargs={'pk': self.item.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Router Table')

    def test_item_create_view(self):
        self.client.login(username='viewowner', password='password123')
        response = self.client.post(reverse('items:create'), {
            'category': self.category.pk,
            'title': 'Belt Sander',
            'description': '3x21 inch belt sander with dust collector.',
            'condition': 'good'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Item.objects.filter(title='Belt Sander').exists())

    def test_item_update_view(self):
        self.client.login(username='viewowner', password='password123')
        response = self.client.post(reverse('items:update', kwargs={'pk': self.item.pk}), {
            'category': self.category.pk,
            'title': 'Router Table Deluxe',
            'description': 'Precision woodworking router table with lift.',
            'condition': 'excellent'
        })
        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, 'Router Table Deluxe')

    def test_item_soft_delete_view(self):
        self.client.login(username='viewowner', password='password123')
        response = self.client.post(reverse('items:delete', kwargs={'pk': self.item.pk}))
        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertTrue(self.item.is_deleted)
        self.assertFalse(self.item.is_available)


class ItemFormsTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='formowner', password='password123')
        self.category = Category.objects.create(name='Cutting Tools')

    def test_item_form_valid(self):
        form_data = {
            'category': self.category.id,
            'title': 'Jigsaw 6.5 Amp',
            'description': 'Orbital action jigsaw with variable speed trigger.',
            'condition': 'good',
        }
        form = ItemForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        item = form.save(commit=False)
        item.owner = self.owner
        item.save()
        self.assertEqual(item.title, 'Jigsaw 6.5 Amp')


class ItemModelAndSignalTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='lender', password='password123')
        self.borrower = User.objects.create_user(username='borrower', password='password123')
        self.category = Category.objects.create(name='Power Tools', icon='drill')

    def test_category_auto_slugify(self):
        cat = Category.objects.create(name='Garden & Lawn Equipment')
        self.assertEqual(cat.slug, 'garden-lawn-equipment')

    def test_item_creation_and_soft_delete(self):
        item = Item.objects.create(
            owner=self.owner,
            category=self.category,
            title='DeWalt Cordless Drill',
            description='20V Max cordless drill with 2 batteries.',
            condition='excellent',
            is_available=True,
            is_deleted=False
        )
        self.assertEqual(item.condition, 'excellent')
        self.assertFalse(item.is_deleted)
        self.assertTrue(item.is_available)

        # Perform soft-delete
        item.is_deleted = True
        item.is_available = False
        item.save()

        refreshed = Item.objects.get(pk=item.pk)
        self.assertTrue(refreshed.is_deleted)
        self.assertFalse(refreshed.is_available)

    def test_currently_borrowed_status(self):
        item = Item.objects.create(
            owner=self.owner,
            category=self.category,
            title='Miter Saw',
            description='10-inch sliding compound miter saw.'
        )
        self.assertFalse(item.currently_borrowed())

        # Create active borrow request
        today = datetime.date.today()
        borrow_req = BorrowRequest.objects.create(
            item=item,
            borrower=self.borrower,
            start_date=today,
            end_date=today + datetime.timedelta(days=3),
            status='active'
        )
        self.assertTrue(item.currently_borrowed())

        borrow_req.status = 'returned'
        borrow_req.save()
        self.assertFalse(item.currently_borrowed())
