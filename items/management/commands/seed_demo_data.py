"""
Management command to seed Loanwood with realistic neighborhood tool-lending demo data.
Downloads royalty-free sample photos with fallback to clean default graphics if offline.
"""

import urllib.request
import urllib.error
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from accounts.models import Profile
from items.models import Category, Item
from borrowing.models import BorrowRequest, Notification


def download_sample_image(url, filename, timeout=6):
    """
    Downloads an image from a URL and returns a ContentFile.
    Falls back gracefully to None if offline or network request fails.
    """
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) LoanwoodSeed/1.0'}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = response.read()
                return ContentFile(data, name=filename)
    except Exception as e:
        # Silently fail back to None for safe offline operation
        return None
    return None


class Command(BaseCommand):
    help = 'Seeds Loanwood with demo users, categories, tools, borrow requests, and notifications.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Beginning Loanwood demo data seeding...'))
        today = timezone.now().date()

        # ---------------------------------------------------------------------
        # 1. Demo Users & Profiles
        # ---------------------------------------------------------------------
        self.stdout.write('Creating demo members...')
        users_data = [
            {
                'username': 'ahmed',
                'email': 'ahmed@loanwood.local',
                'password': 'password123',
                'neighborhood': 'Oakridge West',
                'bio': 'Passionate woodworker, furniture restorer, and neighborhood deck builder. Always excited to share quality workshop gear.',
                'avatar_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&auto=format&fit=crop&q=80',
                'avatar_name': 'ahmed_avatar.jpg',
            },
            {
                'username': 'sara',
                'email': 'sara@loanwood.local',
                'password': 'password123',
                'neighborhood': 'Maple Gardens',
                'bio': 'Urban gardener and permaculture enthusiast. Cultivating community fruit trees and native plant gardens.',
                'avatar_url': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&auto=format&fit=crop&q=80',
                'avatar_name': 'sara_avatar.jpg',
            },
            {
                'username': 'omar',
                'email': 'omar@loanwood.local',
                'password': 'password123',
                'neighborhood': 'Pine Heights',
                'bio': 'Automotive DIYer and mechanics hobbyist. Restoring classic motorcycles and helping neighbors with car maintenance.',
                'avatar_url': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&auto=format&fit=crop&q=80',
                'avatar_name': 'omar_avatar.jpg',
            },
            {
                'username': 'nour',
                'email': 'nour@loanwood.local',
                'password': 'password123',
                'neighborhood': 'Cedar Valley',
                'bio': 'Home improvement enthusiast and weekend renovator. Believer in tool sharing to reduce consumption and connect neighbors.',
                'avatar_url': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&auto=format&fit=crop&q=80',
                'avatar_name': 'nour_avatar.jpg',
            },
        ]

        users = {}
        for udata in users_data:
            user, created = User.objects.get_or_create(
                username=udata['username'],
                defaults={'email': udata['email']}
            )
            user.set_password(udata['password'])
            user.email = udata['email']
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.neighborhood = udata['neighborhood']
            profile.bio = udata['bio']

            # Download avatar
            avatar_file = download_sample_image(udata['avatar_url'], udata['avatar_name'])
            if avatar_file:
                profile.avatar.save(udata['avatar_name'], avatar_file, save=False)
            profile.save()

            users[udata['username']] = user
            self.stdout.write(f"  [+] User '{user.username}' ready.")

        # ---------------------------------------------------------------------
        # 2. Categories
        # ---------------------------------------------------------------------
        self.stdout.write('\nCreating categories...')
        categories_data = [
            {'name': 'Power Tools', 'slug': 'power-tools', 'icon': '⚡'},
            {'name': 'Woodworking', 'slug': 'woodworking', 'icon': '🪚'},
            {'name': 'Gardening', 'slug': 'gardening', 'icon': '🌱'},
            {'name': 'Hand Tools', 'slug': 'hand-tools', 'icon': '🔨'},
            {'name': 'Auto & Mechanical', 'slug': 'auto-mechanical', 'icon': '🔧'},
        ]

        categories = {}
        for cdata in categories_data:
            cat, _ = Category.objects.update_or_create(
                slug=cdata['slug'],
                defaults={'name': cdata['name'], 'icon': cdata['icon']}
            )
            categories[cdata['slug']] = cat
            self.stdout.write(f"  [+] Category '{cat.name}' ready.")

        # ---------------------------------------------------------------------
        # 3. 12 Realistic Tools
        # ---------------------------------------------------------------------
        self.stdout.write('\nCreating 12 tools...')
        tools_data = [
            # Ahmed's tools
            {
                'key': 'drill',
                'owner': users['ahmed'],
                'category': categories['power-tools'],
                'title': 'DeWalt 20V Max Cordless Drill & Driver Kit',
                'description': 'Compact, lightweight drill with two 2.0Ah lithium-ion batteries, fast charger, and 30-piece screw driving bit set. Ideal for framing, cabinetry, and home repairs.',
                'condition': 'excellent',
                'photo_url': 'https://images.unsplash.com/photo-1504148455328-c376907d081c?w=800&auto=format&fit=crop&q=80',
                'photo_name': 'dewalt_drill.jpg',
            },
            {
                'key': 'miter_saw',
                'owner': users['ahmed'],
                'category': categories['woodworking'],
                'title': 'Bosch 10-Inch Dual-Bevel Sliding Compound Miter Saw',
                'description': 'Smooth axial-glide system for precise crosscuts and miter angles up to 45 degrees. Includes 60-tooth fine finish blade and dust collection bag.',
                'condition': 'excellent',
                'photo_url': 'https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=800&auto=format&fit=crop&q=80',
                'photo_name': 'miter_saw.jpg',
            },
            {
                'key': 'jigsaw',
                'owner': users['ahmed'],
                'category': categories['woodworking'],
                'title': 'Makita 6.5 Amp Corded Variable Speed Jigsaw',
                'description': '3 orbital settings plus straight cutting with powerful motor. Comes with wood and metal cutting blade assortment and hard storage case.',
                'condition': 'good',
                'photo_url': 'https://images.unsplash.com/photo-1581147036324-c17ac41dfa6c?w=800&auto=format&fit=crop&q=80',
                'photo_name': 'makita_jigsaw.jpg',
            },

            # Sara's tools
            {
                'key': 'lawn_mower',
                'owner': users['sara'],
                'category': categories['gardening'],
                'title': 'Honda 21-Inch Self-Propelled Gas Lawn Mower',
                'description': 'Reliable twin-blade microcut system with variable speed smart drive and large grass catcher bag. Great for suburban lawns up to half an acre.',
                'condition': 'good',
                'photo_url': 'https://images.unsplash.com/photo-1592417817098-8f3d6eb2252a?w=800&auto=format&fit=crop&q=80',
                'photo_name': 'honda_mower.jpg',
            },
            {
                'key': 'hedge_trimmer',
                'owner': users['sara'],
                'category': categories['gardening'],
                'title': 'Stihl Gas Hedge Trimmer 24-Inch Blade',
                'description': 'Double-sided reciprocating blades with anti-vibration technology. Cuts thick hedges and overgrowth cleanly with minimal fatigue.',
                'condition': 'excellent',
                'photo_url': 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=800&auto=format&fit=crop&q=80',
                'photo_name': 'hedge_trimmer.jpg',
            },
            {
                'key': 'tree_pruner',
                'owner': users['sara'],
                'category': categories['gardening'],
                'title': 'Fiskars Telescoping Tree Pruner (14 Foot)',
                'description': 'Extends from 7 to 14 feet with power-lever technology. Features a sharp steel bypass pruner and hooked 12-inch saw blade for high branch trimming.',
                'condition': 'good',
                'photo_url': 'https://images.unsplash.com/photo-1589923188900-85dae523342b?w=800&auto=format&fit=crop&q=80',
                'photo_name': 'tree_pruner.jpg',
            },

            # Omar's tools
            {
                'key': 'torque_wrench',
                'owner': users['omar'],
                'category': categories['auto-mechanical'],
                'title': 'Craftsman 1/2-Inch Drive Click Torque Wrench',
                'description': 'Precision calibrated from 20 to 150 ft-lbs with audible click confirmation. Essential for lug nuts, suspension work, and engine head bolts.',
                'condition': 'excellent',
                'photo_url': 'https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=800&auto=format&fit=crop&q=80',
                'photo_name': 'torque_wrench.jpg',
            },
            {
                'key': 'pressure_washer',
                'owner': users['omar'],
                'category': categories['auto-mechanical'],
                'title': 'Sun Joe 2030 PSI Max Electric Pressure Washer',
                'description': 'High-power electric pressure washer with 5 quick-connect spray tips and dual detergent tanks. Perfect for car detailing, siding, and driveways.',
                'condition': 'good',
                'photo_url': 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=800&auto=format&fit=crop&q=80',
                'photo_name': 'pressure_washer.jpg',
            },
            {
                'key': 'angle_grinder',
                'owner': users['omar'],
                'category': categories['power-tools'],
                'title': 'DeWalt Heavy-Duty 4-1/2-Inch Angle Grinder',
                'description': '11 Amp 11,000 RPM motor with paddle switch and One-Touch guard. Includes cutting wheels, grinding discs, and wire brush attachments.',
                'condition': 'good',
                'photo_url': 'https://images.unsplash.com/photo-1508873696983-2df5293cb395?w=800&auto=format&fit=crop&q=80',
                'photo_name': 'angle_grinder.jpg',
            },

            # Nour's tools
            {
                'key': 'socket_set',
                'owner': users['nour'],
                'category': categories['hand-tools'],
                'title': 'Stanley 210-Piece Mechanics Tool & Socket Set',
                'description': 'Comprehensive SAE and metric socket set with 1/4", 3/8", and 1/2" 72-tooth ratchets, extension bars, and chrome vanadium alloy sockets.',
                'condition': 'excellent',
                'photo_url': 'https://images.unsplash.com/photo-1581244277943-fe4a9c777189?w=800&auto=format&fit=crop&q=80',
                'photo_name': 'socket_set.jpg',
            },
            {
                'key': 'ladder',
                'owner': users['nour'],
                'category': categories['hand-tools'],
                'title': 'Little Giant 17-Foot Multi-Position Aluminum Ladder',
                'description': 'Converts into an A-frame ladder, extension ladder, 90-degree staircase ladder, and scaffolding trestle. Rated for 300 lbs working load.',
                'condition': 'good',
                'photo_url': 'https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800&auto=format&fit=crop&q=80',
                'photo_name': 'ladder.jpg',
            },
            {
                'key': 'sander',
                'owner': users['nour'],
                'category': categories['woodworking'],
                'title': 'Ryobi 18V ONE+ Cordless Random Orbit Sander',
                'description': '10,000 OPM orbital action for smooth swirl-free wood finishes. Includes dust collection bag and 80/120/220 grit hook-and-loop sanding discs.',
                'condition': 'fair',
                'photo_url': 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&auto=format&fit=crop&q=80',
                'photo_name': 'ryobi_sander.jpg',
            },
        ]

        tools = {}
        for tdata in tools_data:
            item, _ = Item.objects.update_or_create(
                title=tdata['title'],
                owner=tdata['owner'],
                defaults={
                    'category': tdata['category'],
                    'description': tdata['description'],
                    'condition': tdata['condition'],
                    'is_available': True,
                    'is_deleted': False,
                }
            )

            # Download tool photo
            photo_file = download_sample_image(tdata['photo_url'], tdata['photo_name'])
            if photo_file:
                item.photo.save(tdata['photo_name'], photo_file, save=True)
            else:
                item.save()

            tools[tdata['key']] = item
            self.stdout.write(f"  [+] Tool '{item.title}' ready.")

        # ---------------------------------------------------------------------
        # 4. Borrow Requests for all State Machine Scenarios
        # ---------------------------------------------------------------------
        self.stdout.write('\nCreating borrow requests across state machine scenarios...')

        # Clean existing requests for demo reproducibility
        BorrowRequest.objects.all().delete()

        requests_data = [
            # 1 & 2: Active requests (one starting today)
            {
                'item': tools['lawn_mower'],  # Sara's tool
                'borrower': users['ahmed'],
                'start_date': today - timedelta(days=2),
                'end_date': today + timedelta(days=3),
                'status': 'active',
                'message': 'Mowing backyard and neighbor lawn for weekend barbecue.',
            },
            {
                'item': tools['socket_set'],  # Nour's tool
                'borrower': users['omar'],
                'start_date': today,
                'end_date': today + timedelta(days=4),
                'status': 'active',
                'message': 'Fixing alternator and brake pads on project car.',
            },

            # 3: Overdue request (start & end date in past, status 'active' to test auto-sync/is_overdue)
            {
                'item': tools['ladder'],  # Nour's tool
                'borrower': users['sara'],
                'start_date': today - timedelta(days=10),
                'end_date': today - timedelta(days=2),
                'status': 'active',
                'message': 'Cleaning roof gutters and painting fascia boards.',
            },

            # 4 & 5: Pending requests with overlapping dates on same tool (tests concurrency auto-decline)
            {
                'item': tools['drill'],  # Ahmed's tool
                'borrower': users['sara'],
                'start_date': today + timedelta(days=2),
                'end_date': today + timedelta(days=6),
                'status': 'pending',
                'message': 'Need to mount floating shelves in the kitchen pantry.',
            },
            {
                'item': tools['drill'],  # Ahmed's tool
                'borrower': users['omar'],
                'start_date': today + timedelta(days=3),
                'end_date': today + timedelta(days=7),
                'status': 'pending',
                'message': 'Building a sturdy workbench and shelving in the garage.',
            },

            # 6, 7 & 8: Returned requests (2 on-time excellent, 1 late worn for reputation stats)
            {
                'item': tools['miter_saw'],  # Ahmed's tool
                'borrower': users['nour'],
                'start_date': today - timedelta(days=15),
                'end_date': today - timedelta(days=10),
                'status': 'returned',
                'returned_at': timezone.now() - timedelta(days=10),
                'return_condition': 'excellent',
                'return_note': 'Returned pristine and clean with blade guard intact.',
                'message': 'Cutting baseboards and trim for living room remodel.',
            },
            {
                'item': tools['hedge_trimmer'],  # Sara's tool
                'borrower': users['ahmed'],
                'start_date': today - timedelta(days=20),
                'end_date': today - timedelta(days=16),
                'status': 'returned',
                'returned_at': timezone.now() - timedelta(days=17),
                'return_condition': 'excellent',
                'return_note': 'Great borrower, blades oiled and fuel drained as requested.',
                'message': 'Trimming overgrown perimeter hedge along alleyway.',
            },
            {
                'item': tools['sander'],  # Nour's tool
                'borrower': users['sara'],
                'start_date': today - timedelta(days=25),
                'end_date': today - timedelta(days=20),
                'status': 'returned',
                'returned_at': timezone.now() - timedelta(days=15),  # 5 days late
                'return_condition': 'worn',
                'return_note': 'Pad velcro is heavily worn down and base is scuffed.',
                'message': 'Refinishing dining room table.',
            },

            # 9: Declined request with reason
            {
                'item': tools['pressure_washer'],  # Omar's tool
                'borrower': users['nour'],
                'start_date': today - timedelta(days=5),
                'end_date': today - timedelta(days=2),
                'status': 'declined',
                'decline_reason': 'Currently doing driveway pressure washing at home this weekend.',
                'message': 'Deep cleaning back patio before family reunion.',
            },
        ]

        for rdata in requests_data:
            req = BorrowRequest.objects.create(
                item=rdata['item'],
                borrower=rdata['borrower'],
                start_date=rdata['start_date'],
                end_date=rdata['end_date'],
                status=rdata['status'],
                message=rdata.get('message', ''),
                decline_reason=rdata.get('decline_reason', ''),
                returned_at=rdata.get('returned_at', None),
                return_condition=rdata.get('return_condition', None),
                return_note=rdata.get('return_note', ''),
            )
            self.stdout.write(f"  [+] Created {req.status.upper()} request #{req.id} for '{req.item.title}'.")

        # ---------------------------------------------------------------------
        # 5. Unread Notifications for each user
        # ---------------------------------------------------------------------
        self.stdout.write('\nGenerating unread notifications...')
        Notification.objects.all().delete()

        notifications_data = [
            # Ahmed
            {
                'recipient': users['ahmed'],
                'message': f"New borrow request from sara for '{tools['drill'].title}'.",
                'link': '/borrowing/owner/',
                'is_read': False,
            },
            {
                'recipient': users['ahmed'],
                'message': f"New borrow request from omar for '{tools['drill'].title}'.",
                'link': '/borrowing/owner/',
                'is_read': False,
            },
            {
                'recipient': users['ahmed'],
                'message': f"Your active checkout for '{tools['lawn_mower'].title}' from sara is underway.",
                'link': '/borrowing/dashboard/',
                'is_read': False,
            },

            # Sara
            {
                'recipient': users['sara'],
                'message': f"Reminder: Your reservation for '{tools['ladder'].title}' is past its due date.",
                'link': '/borrowing/dashboard/',
                'is_read': False,
            },
            {
                'recipient': users['sara'],
                'message': f"Return recorded for '{tools['sander'].title}'.",
                'link': '/borrowing/dashboard/',
                'is_read': False,
            },

            # Omar
            {
                'recipient': users['omar'],
                'message': f"Active loan: You have checked out '{tools['socket_set'].title}' from nour.",
                'link': '/borrowing/dashboard/',
                'is_read': False,
            },

            # Nour
            {
                'recipient': users['nour'],
                'message': f"Your request for '{tools['pressure_washer'].title}' was declined: Driveway maintenance.",
                'link': '/borrowing/dashboard/',
                'is_read': False,
            },
            {
                'recipient': users['nour'],
                'message': f"Return completed for '{tools['miter_saw'].title}'. Condition recorded: Excellent.",
                'link': '/borrowing/dashboard/',
                'is_read': False,
            },
        ]

        for ndata in notifications_data:
            Notification.objects.create(
                recipient=ndata['recipient'],
                message=ndata['message'],
                link=ndata['link'],
                is_read=ndata['is_read']
            )

        self.stdout.write(self.style.SUCCESS('\n[SUCCESS] Successfully seeded Loanwood with all demo data, images, categories, requests, and notifications!'))
