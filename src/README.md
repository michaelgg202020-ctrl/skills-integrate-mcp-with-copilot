# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Register and log in as a student
- Sign up for activities with authenticated accounts

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| POST   | `/auth/register`                                                  | Create a student account                                             |
| POST   | `/auth/login`                                                     | Log in and receive a bearer token                                    |
| GET    | `/auth/me`                                                        | Get the current user and role                                        |
| PATCH  | `/users/me`                                                       | Update the current user's profile                                   |

Protected endpoints require `Authorization: Bearer <access_token>`. Set
`ADMIN_EMAIL` and `ADMIN_PASSWORD` when starting the server to provision an
administrator account without storing a password in the source code.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
