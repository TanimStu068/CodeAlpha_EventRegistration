# CodeAlpha_EventRegistration

Event Registration System built with **Django** and **Django REST Framework**
for the CodeAlpha Backend Development Internship (Task 2).

## Features
- Models for **Event** and **Registration** (linked to Django users and events)
- Token authentication: sign up, log in
- Public endpoints to list events (with search) and view event details
- Registration form endpoint with validation, capacity limit and duplicate protection
- Users can view and cancel their own registrations (and re-register after cancelling)
- **Organizer features:** Django admin panel, staff-only event creation/editing, attendee list per event
- SQLite by default; PostgreSQL supported through environment variables
- 11 automated tests

## Project structure
```
CodeAlpha_EventRegistration/
├── manage.py
├── requirements.txt
├── config/              # settings, root urls, wsgi
└── events/
    ├── models.py        # Event, Registration
    ├── serializers.py
    ├── views.py         # API logic
    ├── urls.py
    ├── admin.py         # organizer admin panel
    ├── tests.py
    └── management/commands/seed_events.py
```

## Run locally
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # organizer account for /admin/
python manage.py seed_events      # optional sample data
python manage.py runserver
```
API root: http://127.0.0.1:8000/api/ | Admin: http://127.0.0.1:8000/admin/

Run tests: `python manage.py test`

### Use PostgreSQL (optional)
Set `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` before running `migrate`.

## API reference
Authenticated requests send the header `Authorization: Token <your-token>`.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /api/auth/signup/ | none | Create account, returns token |
| POST | /api/auth/login/ | none | Returns token |
| GET | /api/events/ | none | List events. Filters: ?search=django, ?upcoming=true |
| GET | /api/events/{id}/ | none | Event details with spots_left |
| POST | /api/events/{id}/register/ | user | Submit registration form |
| GET | /api/registrations/ | user | My registrations (?status=confirmed) |
| GET | /api/registrations/{id}/ | user | One of my registrations |
| DELETE | /api/registrations/{id}/ | user | Cancel my registration |
| POST | /api/events/ | staff | Create event |
| PUT/PATCH/DELETE | /api/events/{id}/ | staff | Edit or delete event |
| GET | /api/events/{id}/registrations/ | staff | Attendee list |

### Example
```bash
# sign up
curl -X POST http://127.0.0.1:8000/api/auth/signup/ \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"alice\", \"email\": \"a@x.com\", \"password\": \"strongpass123\"}"

# register for event 1
curl -X POST http://127.0.0.1:8000/api/events/1/register/ \
  -H "Authorization: Token YOUR_TOKEN" -H "Content-Type: application/json" \
  -d "{\"full_name\": \"Alice Rahman\", \"phone\": \"0123456789\"}"

# cancel registration 1
curl -X DELETE http://127.0.0.1:8000/api/registrations/1/ -H "Authorization: Token YOUR_TOKEN"
```

Error responses use `{"error": "..."}` with 400 (invalid or past event), 401 (not logged in),
403 (not allowed), 404 (not found) or 409 (already registered / event full).
