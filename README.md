# expense_diary

## Overview

The Expense Tracker System is a backend API designed to help users manage and track their expenses. Users can create, view, and analyze their expenses through API interactions.

### Components

- **Backend API:** Django backend providing RESTful APIs.
- **Database:** Sqllite3 database to store user and expense data.
- **Background Worker:** Celery for asynchronous tasks (e.g., sending email notifications).

## Class Structure

### 1. `User`

- **Attributes:**
  - `email` (EmailField): Email of the user (unique identifier).
  - `username` (CharField): Username of the user.
  - `is_active` (BooleanField): Indicates whether the user is active.
  - `is_staff` (BooleanField): Indicates whether the user has staff privileges.

- **Manager:**
  - `UserProfileManager`: Custom manager for creating regular and superuser accounts.

### 2. `Expense`

- **Attributes:**
  - `expense_name` (CharField): Name of the expense.
  - `payer_id` (ForeignKey): ID of the user who paid for the expense.
  - `amount` (DecimalField): Total amount of the expense.
  - `expense_type` (CharField): Type of the expense (EQUAL, EXACT, PERCENT).
  - `participants` (ManyToManyField): Participants in the expense.

- **Methods:**
  - `get_user_expense_details(user_id)`: Retrieves expenses specific to a user.

### 3. `Passbook`

- **Attributes:**
  - `expense_id` (ForeignKey): ID of the associated expense.
  - `creditor_id` (ForeignKey): ID of the creditor user.
  - `debtor_id` (ForeignKey): ID of the debtor user.
  - `amount` (DecimalField): Amount involved in the passbook entry.

### 4. Serializers

- `UserSerializer`: Serializes `User` model data.
- `LoginSerializer`: Serializes login credentials.
- `PassbookSerializer`: Serializes `Passbook` model data.
- `ExpenseSerializer`: Serializes `Expense` model data.
- `ExpenseAdditionalSerializer`: Serializes additional expense data.

## Views

### 1. `RegistrationView`

- **Permission Classes:**
  - `AllowAny`

- **Methods:**
  - `post(request, format=None)`: Handles user registration.

### 2. `UserLoginView`

- **Permission Classes:**
  - `AllowAny`

- **Methods:**
  - `post(request)`: Handles user login and generates JWT tokens.

### 3. `ExpenseCreate`

- **Authentication Classes:**
  - `JWTAuthentication`

- **Permission Classes:**
  - `IsAuthenticated`

- **Methods:**
  - `post(request, *args, **kwargs)`: Creates an expense and sends a notification email.

### 4. `UserExpenseView`

- **Authentication Classes:**
  - `JWTAuthentication`

- **Permission Classes:**
  - `IsAuthenticated`

- **Methods:**
  - `get(request)`: Retrieves expenses specific to the authenticated user.

### 5. `BalanceView`

- **Methods:**
  - `get(request)`: Retrieves balance information for all users.

### 6. `BalanceDetailView`

- **Authentication Classes:**
  - `JWTAuthentication`

- **Permission Classes:**
  - `IsAuthenticated`

- **Methods:**
  - `get(request)`: Retrieves detailed balance information for the authenticated user.

## Celery Tasks

### 1. `send_expense_notification_email`

- **Description:**
  - Sends an email notification to a participant when they are added to a new expense.

- **Parameters:**
  - `expense_id`: ID of the expense.
  - `participant_email`: Email of the participant.
  - `amount_owed`: Amount owed in the expense.

### 2. `send_weekly_summary_email`

- **Description:**
  - Sends a weekly summary email to users, indicating the total amount owed by each user.

- **Logic:**
  - Calculates the total amount owed per user.

- **Email Template:**
  - `weekly_summary_email.txt`

### 3. `send_summary_email`

- **Description:**
  - Sends an individual summary email to a user with the total amount owed.

- **Parameters:**
  - `recipient_email`: Email of the recipient user.
  - `total_amount_owed`: Total amount owed by the user.

- **Email Template:**
  - `weekly_summary_email.txt`

## Celery Beat Schedule

### 1. `send-weekly-summary-email`

- **Task:**
  - `splitwise_app.tasks.send_weekly_summary_email`

- **Schedule:**
  - Runs every Friday at 4:00 AM.

- **Description:**
  - Sends a weekly summary email to users, indicating the total amount owed by each user.

- **Logic:**
  - Calculates the total amount owed per user.

- **Email Template:**
  - `weekly_summary_email.txt`
