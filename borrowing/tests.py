from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import datetime

from items.models import Category, Item
from borrowing.models import BorrowRequest, Notification
from borrowing.forms import BorrowRequestForm, ReturnItemForm, DeclineRequestForm
from borrowing.services import (
    sync_overdue_statuses,
    overlapping_requests,
    approve_request,
    activate_if_due,
    mark_returned,
)


class BorrowingViewsTest(TestCase):
    def setUp(self):
        self.lender = User.objects.create_user(username='lender_view', password='password123')
        self.borrower = User.objects.create_user(username='borrower_view', password='password123')
        self.category = Category.objects.create(name='Drilling Tools')
        self.item = Item.objects.create(
            owner=self.lender,
            category=self.category,
            title='Core Drill',
            description='Diamond core drill for concrete.'
        )

    def test_create_borrow_request_view(self):
        self.client.login(username='borrower_view', password='password123')
        today = timezone.now().date()
        response = self.client.post(reverse('borrowing:create_request', kwargs={'item_pk': self.item.pk}), {
            'start_date': today + datetime.timedelta(days=1),
            'end_date': today + datetime.timedelta(days=4),
            'message': 'Basement plumbing installation.'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BorrowRequest.objects.filter(item=self.item, borrower=self.borrower).exists())

    def test_owner_cannot_borrow_own_item(self):
        self.client.login(username='lender_view', password='password123')
        response = self.client.get(reverse('borrowing:create_request', kwargs={'item_pk': self.item.pk}))
        self.assertEqual(response.status_code, 302)

    def test_approve_and_decline_views(self):
        today = timezone.now().date()
        req = BorrowRequest.objects.create(
            item=self.item,
            borrower=self.borrower,
            start_date=today + datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=3),
            status='pending'
        )

        self.client.login(username='lender_view', password='password123')
        approve_res = self.client.post(reverse('borrowing:approve_request', kwargs={'pk': req.pk}))
        self.assertEqual(approve_res.status_code, 302)
        req.refresh_from_db()
        self.assertEqual(req.status, 'approved')

        # Test decline view on another pending request
        req2 = BorrowRequest.objects.create(
            item=self.item,
            borrower=self.borrower,
            start_date=today + datetime.timedelta(days=5),
            end_date=today + datetime.timedelta(days=7),
            status='pending'
        )
        decline_res = self.client.post(reverse('borrowing:decline_request', kwargs={'pk': req2.pk}), {
            'decline_reason': 'Out of town.'
        })
        self.assertEqual(decline_res.status_code, 302)
        req2.refresh_from_db()
        self.assertEqual(req2.status, 'declined')

    def test_mark_returned_view(self):
        today = timezone.now().date()
        req = BorrowRequest.objects.create(
            item=self.item,
            borrower=self.borrower,
            start_date=today - datetime.timedelta(days=2),
            end_date=today,
            status='active'
        )
        self.client.login(username='lender_view', password='password123')
        res = self.client.post(reverse('borrowing:mark_returned', kwargs={'pk': req.pk}), {
            'return_condition': 'good',
            'return_note': 'Returned complete.'
        })
        self.assertEqual(res.status_code, 302)
        req.refresh_from_db()
        self.assertEqual(req.status, 'returned')

    def test_dashboards_and_notifications(self):
        self.client.login(username='borrower_view', password='password123')
        borrower_dash = self.client.get(reverse('borrowing:borrower_dashboard'))
        self.assertEqual(borrower_dash.status_code, 200)

        self.client.login(username='lender_view', password='password123')
        owner_dash = self.client.get(reverse('borrowing:owner_dashboard'))
        self.assertEqual(owner_dash.status_code, 200)

        notif = Notification.objects.create(recipient=self.lender, message='Test notification', link='/items/')
        notifs_res = self.client.get(reverse('borrowing:notifications'))
        self.assertEqual(notifs_res.status_code, 200)

        read_res = self.client.get(reverse('borrowing:mark_notification_read', kwargs={'pk': notif.pk}))
        self.assertEqual(read_res.status_code, 302)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)


class BorrowingFormsTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='form_owner', password='password123')
        self.borrower = User.objects.create_user(username='form_borrower', password='password123')
        self.category = Category.objects.create(name='Ladders')
        self.item = Item.objects.create(
            owner=self.owner,
            category=self.category,
            title='24ft Extension Ladder',
            description='Aluminum extension ladder.'
        )

    def test_borrow_request_form_valid(self):
        today = timezone.now().date()
        form_data = {
            'start_date': today + datetime.timedelta(days=1),
            'end_date': today + datetime.timedelta(days=5),
            'message': 'Need for gutter cleaning.'
        }
        form = BorrowRequestForm(data=form_data, item=self.item)
        self.assertTrue(form.is_valid(), form.errors)

    def test_borrow_request_form_past_start_date(self):
        today = timezone.now().date()
        form_data = {
            'start_date': today - datetime.timedelta(days=2),
            'end_date': today + datetime.timedelta(days=2),
            'message': 'Gutter cleaning.'
        }
        form = BorrowRequestForm(data=form_data, item=self.item)
        self.assertFalse(form.is_valid())
        self.assertIn('start_date', form.errors)

    def test_borrow_request_form_end_before_start(self):
        today = timezone.now().date()
        form_data = {
            'start_date': today + datetime.timedelta(days=5),
            'end_date': today + datetime.timedelta(days=2),
            'message': 'Gutter cleaning.'
        }
        form = BorrowRequestForm(data=form_data, item=self.item)
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)

    def test_borrow_request_form_exceeds_30_days(self):
        today = timezone.now().date()
        form_data = {
            'start_date': today + datetime.timedelta(days=1),
            'end_date': today + datetime.timedelta(days=35),
            'message': 'Long project.'
        }
        form = BorrowRequestForm(data=form_data, item=self.item)
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)

    def test_borrow_request_form_overlapping_rejection(self):
        today = timezone.now().date()
        # Existing approved request
        BorrowRequest.objects.create(
            item=self.item,
            borrower=self.borrower,
            start_date=today + datetime.timedelta(days=5),
            end_date=today + datetime.timedelta(days=10),
            status='approved'
        )

        form_data = {
            'start_date': today + datetime.timedelta(days=7),
            'end_date': today + datetime.timedelta(days=12),
            'message': 'Overlapping request.'
        }
        form = BorrowRequestForm(data=form_data, item=self.item)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_return_item_form(self):
        form_data = {
            'return_condition': 'good',
            'return_note': 'Returned in great shape.'
        }
        form = ReturnItemForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_decline_request_form(self):
        form_data = {
            'decline_reason': 'Tool currently scheduled for personal maintenance.'
        }
        form = DeclineRequestForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)


class BorrowingServicesTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='tool_lender', password='password123')
        self.borrower1 = User.objects.create_user(username='borrower_one', password='password123')
        self.borrower2 = User.objects.create_user(username='borrower_two', password='password123')
        self.category = Category.objects.create(name='Heavy Equipment')
        self.item = Item.objects.create(
            owner=self.owner,
            category=self.category,
            title='Rotary Hammer Drill',
            description='Heavy duty rotary hammer drill with SDS plus bits.',
            condition='excellent'
        )

    def test_sync_overdue_statuses(self):
        today = timezone.now().date()
        # Active but past end date
        overdue_req = BorrowRequest.objects.create(
            item=self.item,
            borrower=self.borrower1,
            start_date=today - datetime.timedelta(days=7),
            end_date=today - datetime.timedelta(days=2),
            status='active'
        )
        # Active and not past end date
        current_req = BorrowRequest.objects.create(
            item=self.item,
            borrower=self.borrower2,
            start_date=today - datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=3),
            status='active'
        )

        updated = sync_overdue_statuses()
        self.assertEqual(updated, 1)

        overdue_req.refresh_from_db()
        current_req.refresh_from_db()
        self.assertEqual(overdue_req.status, 'overdue')
        self.assertEqual(current_req.status, 'active')

    def test_overlapping_requests(self):
        today = timezone.now().date()
        approved_req = BorrowRequest.objects.create(
            item=self.item,
            borrower=self.borrower1,
            start_date=today + datetime.timedelta(days=2),
            end_date=today + datetime.timedelta(days=6),
            status='approved'
        )

        # Overlapping period
        overlaps = overlapping_requests(
            self.item,
            start_date=today + datetime.timedelta(days=4),
            end_date=today + datetime.timedelta(days=8)
        )
        self.assertEqual(overlaps.count(), 1)
        self.assertIn(approved_req, overlaps)

        # Exclude ID
        overlaps_excluded = overlapping_requests(
            self.item,
            start_date=today + datetime.timedelta(days=4),
            end_date=today + datetime.timedelta(days=8),
            exclude_id=approved_req.id
        )
        self.assertEqual(overlaps_excluded.count(), 0)

        # Non-overlapping period
        non_overlaps = overlapping_requests(
            self.item,
            start_date=today + datetime.timedelta(days=7),
            end_date=today + datetime.timedelta(days=10)
        )
        self.assertEqual(non_overlaps.count(), 0)

    def test_approve_request_declines_overlapping_pending(self):
        today = timezone.now().date()
        req1 = BorrowRequest.objects.create(
            item=self.item,
            borrower=self.borrower1,
            start_date=today + datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=5),
            status='pending'
        )
        req2_conflict = BorrowRequest.objects.create(
            item=self.item,
            borrower=self.borrower2,
            start_date=today + datetime.timedelta(days=3),
            end_date=today + datetime.timedelta(days=7),
            status='pending'
        )

        approved = approve_request(req1)
        self.assertEqual(approved.status, 'approved')

        req2_conflict.refresh_from_db()
        self.assertEqual(req2_conflict.status, 'declined')
        self.assertEqual(req2_conflict.decline_reason, 'Item booked for overlapping dates')

        # Check notifications generated for both
        self.assertTrue(Notification.objects.filter(recipient=self.borrower1, message__contains='approved').exists())
        self.assertTrue(Notification.objects.filter(recipient=self.borrower2, message__contains='declined').exists())

    def test_activate_if_due(self):
        today = timezone.now().date()
        due_req = BorrowRequest.objects.create(
            item=self.item,
            borrower=self.borrower1,
            start_date=today,
            end_date=today + datetime.timedelta(days=3),
            status='approved'
        )
        future_req = BorrowRequest.objects.create(
            item=self.item,
            borrower=self.borrower2,
            start_date=today + datetime.timedelta(days=5),
            end_date=today + datetime.timedelta(days=8),
            status='approved'
        )

        activated_count = activate_if_due(self.borrower1)
        self.assertEqual(activated_count, 1)

        due_req.refresh_from_db()
        future_req.refresh_from_db()
        self.assertEqual(due_req.status, 'active')
        self.assertEqual(future_req.status, 'approved')

    def test_mark_returned(self):
        today = timezone.now().date()
        req = BorrowRequest.objects.create(
            item=self.item,
            borrower=self.borrower1,
            start_date=today - datetime.timedelta(days=3),
            end_date=today,
            status='active'
        )

        returned = mark_returned(req, condition='good', note='Returned clean with all bits in box.')
        self.assertEqual(returned.status, 'returned')
        self.assertIsNotNone(returned.returned_at)
        self.assertEqual(returned.return_condition, 'good')
        self.assertEqual(returned.return_note, 'Returned clean with all bits in box.')

        self.item.refresh_from_db()
        self.assertEqual(self.item.condition, 'good')
        self.assertTrue(Notification.objects.filter(recipient=self.borrower1, message__contains='Return confirmed').exists())
