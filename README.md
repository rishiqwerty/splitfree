# SplitFree Backend

SplitFree is a backend service designed to manage expense splitting among groups of people. It provides APIs to handle user accounts, groups, expenses, and settlements.

## Features

- User authentication and management
- Group creation and management
- Expense tracking and splitting
- Settlement calculations
- RESTful API design

## Tech Stack

- **Backend Framework**: [Django](https://www.djangoproject.com/)
- **Database**: PostgreSQL / MySQL
- **Authentication**: JWT / OAuth2
- **Hosting**: AWS / Heroku / Docker

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/rishiqwerty/splitfree_backend.git
    cd splitfree_backend
    ```

2. Create a virtual environment and activate it:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up the database:
    ```bash
    python manage.py migrate
    ```

5. Run the development server:
    ```bash
    python manage.py runserver
    ```

## API Endpoints

| Endpoint                | Method | Description                  |
|-------------------------|--------|------------------------------|
| `/api/users`            | POST   | Create a new user            |
| `/api/groups`           | POST   | Create a new group           |
| `/api/expenses`         | POST   | Add a new expense            |
| `/api/settlements`      | GET    | Get settlement details       |

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.