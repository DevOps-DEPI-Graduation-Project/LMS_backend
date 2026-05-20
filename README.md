# Commit Ma3ana Backend 

Backend system for the Commit Ma3ana Learning Management System built using Django and Django REST Framework.

The platform provides secure and scalable APIs for managing courses, quizzes, videos, enrollments, notifications, and student progress tracking.

---

# Features

## Student Features

- User authentication
- Course enrollment
- Progress tracking
- Watch course videos
- Access learning materials
- Submit quizzes
- Review quiz results
- Receive notifications
- Rate courses

---

## Admin Features

- Manage students and instructors
- Manage courses and packages
- Manage quizzes and questions
- Manage videos and materials
- View platform statistics
- Manage announcements

---

## Instructor Features

- Create and manage courses
- Upload videos and materials
- Create quizzes and questions
- Track student performance
- View enrolled students
- Publish announcements

---

# Tech Stack

- Backend Framework: Django
- API Framework: Django REST Framework
- Language: Python
- Database: MySQL
- Authentication: JWT Authentication

---

# Project Structure

```bash
backend/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── accounts/
│   ├── courses/
│   │   ├── course/
│   │   ├── package/
│   │   └── enrollment/
│   │
│   ├── quizzes/
│   ├── videos/
│   ├── materials/
│   └── notifications/
│       ├── notification/
│       └── announcements/
│
├── media/
│
├── requirements.txt
│
└── manage.py
```

---

# Main Applications

## Accounts App

Handles:

- Authentication
- JWT tokens
- User profiles
- Roles management

---

## Courses App

Handles:

- Courses
- Packages
- Enrollments
- Course ratings

---

## Quizzes App

Handles:

- Quizzes
- Questions
- Answers
- Quiz submissions
- Results

---

## Videos App

Handles:

- Course videos
- Video progress tracking

---

## Materials App

Handles:

- PDFs
- Downloadable resources
- Course files

---

## Notifications App

Handles:

- Real-time notifications
- Instructor announcements

---

# API Structure

All APIs are versioned.

Example:

```bash
/api/auth/
/api/courses/
/api/quizzes/
/api/videos/
```

---

# Authentication

The system uses JWT Authentication.

Features:

- Access token
- Refresh token
- Protected endpoints
- Role-based access

---

# Installation

## Clone Repository

```bash
git clone <repository_url>
cd backend
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

---

## Activate Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Migrations

```bash
python manage.py migrate
```

---

## Create Superuser

```bash
python manage.py createsuperuser
```

---

## Run Development Server

```bash
python manage.py runserver
```


# Objective

Build a scalable, maintainable, and secure backend system that provides high-performance APIs for the Commit Ma3ana learning platform.
---

## Development Team

### Front-End Team
- [Rawan Bahaa](https://github.com/Rawanbahaa142) 
- [Reham Ahmed](https://github.com/reham14-ahmed)
- [Mohamed Hofny](https://github.com/MohamedHofny)

### Flutter (Mobile) Team

- [Abdallah Alqiran](https://github.com/Abdallah-Alqiran) — Team Leader
- [Taha Saber](https://github.com/Taha-Saber)
- [Mayar Abdelrahim](https://github.com/Mayar-Abdelrahim)

### Back-End Team

- [Omnia Abdelnasser](https://github.com/Omnia-Abdelnasser)
- [Rana Ahmed](https://github.com/Rana-A-Badawy)
- [Taha Fawy](https://github.com/Taha-M-Fawy)
