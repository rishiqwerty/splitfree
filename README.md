# SplitFree Backend

SplitFree is a backend service designed to manage expense splitting among groups of people. It provides APIs to handle user accounts, groups, expenses, and settlements.

## 📌 Why I Built This

I got fed up with using the ad-heavy Splitwise app and wanted a clean, simple, ad-free alternative to split expenses with friends. So I built **SplitFree** to scratch my own itch — and it turned out way too fun to stop.

# Live URLS:
- Backend: [splitfree(onrender)](https://splitfree-backend.onrender.com/)
- Frontend: [splitfree(Vercel)](https://split-free-frontend.vercel.app/)

Note: Both backend and frontend is deployed in free tier service, so it may take time to load
## Features

- Seamlessly log in using your Google account for a secure and hassle-free authentication experience.
- Create groups, share invite URLs, and let others join easily through a shared link.
- Add, track, and manage shared expenses within groups — automatically calculate individual shares.
- Maintain a chronological log of all activities and changes made within each group for complete transparency.
- Automatically compute who owes whom and optimize settlements to minimize the number of transactions required.
- Get smart overviews, spending summaries, and detailed expense breakdowns powered by AI.
- Enhance group and expense entries with AI-detected icons for quick visual context.
- Clean, consistent, and well-structured API endpoints designed following REST best practices.

## Tech Stack

- **Backend Framework**: [Django](https://www.djangoproject.com/)
- **Database**: PostgreSQL / sqllite
- **Authentication**: Google OAuth2 (Firebase)
- **Hosting**: Render

## Pre-requisites
- Python 3.13(Preferred)
- [Poetry](https://python-poetry.org/)
- [direnv](https://direnv.net/)
- [ollama](https://ollama.com/)(Optional)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/rishiqwerty/splitfree_backend.git
    cd splitfree_backend
    ```

2. Create a virtual environment and activate it:
    ```
    direnv allow
    ```
    It will create new env and activates it


3. Install dependencies:
    ```
        poetry install
    ```

4. Set up the database:
    ```
    python manage.py migrate
    ```

5. Run the development server:
    ```
    python manage.py runserver
    ```
6. [Optional] If using a local LLM, download the model and run it:
   ```
    ollama pull codellama
   ```  
Note: To enable Google login, you’ll need to configure it in the Firebase Console. Follow the official guide here:
👉 Firebase Google Sign-In Setup

## Environment Variables

Create a `.envrc.local`(if using direnv) file in the project root and add the following:

```
    export USE_SQLITE=true                          # Use SQLite for local development
    export DATABASE_URL=<url>                       # Database connection string
    export FIREBASE_CREDENTIALS=xx-xx-xxx.json      # Path to Firebase credentials JSON file (if using file-based creds)
    export FIREBASE_CREDENTIALS_B64='xxxxxx-xxxx'   # Base64-encoded Firebase credentials (if using inline creds)

    export GEMINI_API_KEY=<API_KEY>                 # API key for AI overviews and group/expense icon detection

    # Local LLM config
    export USE_LOCAL_LLM=false                      # Set to true to use a local LLM instance
    export LOCAL_LLM_URL=http://localhost:11434/api/generate  # URL for local LLM endpoint
    export LLM_MODEL=codellama                      # Name of the local model to use
```
Note:
- Make sure to run direnv allow, if there is any changes in this file
- I am using ollama for local llm so make sure it is up and running, and the said model is downloaded

## API Endpoints

| Endpoint                | Method | Description                  |
|-------------------------|--------|------------------------------|
| `/api/v1/groups/<group_id>`           | GET   | Get Group details members, creation date etc. |
| `/api/v1/groups/`           | GET   | List all groups associated with logged in user. |
| `/api/v1/groups/create`           | POST   | Create new group. |
| `/api/v1/groups/<uuid>/add-user`           | POST   | Add new user to group. |
| `/api/v1/groups/<uuid>/activities/`           | GET   | List down all the activities in group. |
| `/api/v1/expenses/expenses`         | POST   | Add a new expense            |
| `/api/v1/expenses/expenses/<group_id>`        | GET   | Get list of expenses associated with group  |
| `/api/v1/expenses/expenses/<group_id>/summary`    | GET   | Get summary of expenses who needs to pay whom? |
| `/api/v1/expenses/expense/delete/<expense_id>`    | DELETE  | Delete expense based on provided id  |
| `/api/v1/expenses/expense/update/<expense_id>`    | UPDATE   | Update an expense based on id   |
| `/api/v1/transactions/`   | POST   | Create a new transaction          |
| `/auth/google-login/`   | POST   | Login via Google             |


## Known Issues / Limitations

- Free-tier hosting may cause slow initial load times.
- Currently, authentication token is stored in local storage (moving to HTTP-only cookie soon).
- Tests

## Upcoming changes
- Payment QR/links for individual for easy payments
- User profile
- Not just for groups — track and manage your personal expenses within the same platform.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

The frontend for SplitFree is built using React.
It’s currently hosted in a private repository. If you’re interested in contributing, feel free to connect with me directly!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
