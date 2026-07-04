#  E-Shop Management System

A full-stack E-Shop Management System built with Django. It helps manage products, billing, customer invoices, and service requests.

##  Features

- User Authentication
- Product Management
- Billing & Invoice Generation
- Service Request Management
- Customer Management
- Dashboard
- PDF Invoice Generation
- Responsive UI
- Docker Support

## Tech Stack

- Python
- Django
- HTML
- CSS
- JavaScript
- PostgreSQL / SQLite
- Docker
- Git & GitHub

## Project Structure

```
eshop/
├── core/
├── templates/
├── static/
├── media/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── manage.py
```

##  Installation

### Clone the repository

```bash
git clone https://github.com/pdk15/eshop.git
cd eshop
```

### Create virtual environment

```bash
python -m venv venv
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run migrations

```bash
python manage.py migrate
```

### Start the server

```bash
python manage.py runserver
```

##  Run with Docker

Build the project

```bash
docker compose build
```

Run the project

```bash
docker compose up
```

Visit:

```
http://localhost:8000
```


##  Future Improvements

- Online Payment Gateway
- Email Notifications
- Sales Analytics Dashboard
- Inventory Reports
- Role-Based Access Control

##  Author

**Pranav Khanolkar**

GitHub: https://github.com/pdk15
