# Loanwood — Neighborhood Tool Lending Collective

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.0-092E20?logo=django)

**Loanwood** is a community-focused web platform designed for neighborhood equipment and tool lending. It enables neighbors to share household tools, power gear, and gardening equipment seamlessly—reducing individual consumption, saving money, and fostering stronger local bonds.

---

## Key Features

- **Tool Catalog & Taxonomy**: Browse items categorized by power tools, woodworking, garden & lawn, hand tools, painting, and plumbing.
- **Full-Text Search & Filtering**: Quickly find tools by name or description with real-time status indicators.
- **Complete Borrowing Lifecycle**:
  - Date-based reservation bookings.
  - Perforated ticket-style UI for tracking loan requests.
  - One-click owner approval or declination with customizable feedback.
  - Condition audit upon item return (Excellent, Good, Fair, Worn).
- **Member Notification System**: Unread notification counter in the global navigation bar notifying members of loan approvals, declines, or returns.
- **Reputation & Member Profiles**: Dedicated neighborhood member profile pages displaying listed gear, bio, and borrowing history.
- **Custom Tactile Workshop UI**: Crafted with a custom CSS design system featuring Polaroid-style photo cards, custom color palettes, and responsive layout without heavy frontend frameworks.

---

## Tech Stack

- **Backend**: Python 3, Django 5.0
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Frontend**: HTML5, Custom CSS3 Design System, Vanilla JavaScript
- **Static Assets**: WhiteNoise Static Storage
- **Deployment**: Configured for Render, Railway, or Heroku via Gunicorn & `Procfile`.

---

## Repository Structure

```
Loanwood/
├── config/             # Django settings, root URLs, WSGI/ASGI configuration
├── core/               # Landing page, homepage controllers, global context processors
├── accounts/           # User authentication, registration, profiles & reputation
├── items/              # Tool catalog models, search filters, detail & CRUD views
├── borrowing/          # Rental requests, loan ticket state machine & notifications
├── static/             # Custom CSS design system, logo assets & JavaScript
├── templates/          # Modular HTML templates (includes, cards, tickets)
├── requirements.txt    # Python dependencies
└── Procfile            # Web server deployment entry point
```

---

## Quick Start & Local Setup

Follow these steps to run Loanwood locally on your machine:

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/loanwood-tool-lending.git
cd loanwood-tool-lending
```

### 2. Create and Activate a Virtual Environment
```bash
# On Windows
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (Optional)
Create a `.env` file in the root directory:
```env
DEBUG=True
SECRET_KEY=django-insecure-loanwood-local-development-key
```

### 5. Apply Database Migrations
```bash
python manage.py migrate
```

### 6. Run the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to `http://127.0.0.1:8000/`.

---

## Deployment Instructions (Render.com)

1. **Build Command**:
   ```bash
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
   ```
2. **Start Command**:
   ```bash
   gunicorn config.wsgi:application
   ```
3. Set environment variables:
   - `DEBUG`: `True`
   - `SECRET_KEY`: `your-secret-key`
