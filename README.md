# 📊 Net Salary Calculator

This project is a **Net Salary Calculator** built with Flask, Python, and MongoDB Atlas. It allows authenticated users to calculate their net salary, considering various earnings and deductions, and offers features to manage and save different calculation profiles.

## ✨ Main Features

- **User Authentication**: Full registration, login, and logout system to protect user data.
- **Accurate Calculation**: Calculates INSS and IRPF based on 2025 tax tables, and also considers other earnings (e.g., bonuses) and deductions (e.g., food vouchers, health plans, private pension, dental).
- **Profile Management**: Allows saving and loading multiple calculation profiles, making it easier to compare and monitor different financial scenarios.
- **Salary Raise Simulation**: Interactive tool to apply a percentage raise to the base salary and visualize the impact on net salary, with the option to save the new scenario as a profile.
- **Responsive Interface**: Modern and adaptable design for a great experience on both mobile and desktop devices.
- **Data Persistence**: Uses MongoDB Atlas to securely store user and profile information.

## 🚀 Technologies Used

- **Backend**: Python 🐍
  - **Web Framework**: Flask
  - **Security**: `werkzeug.security` for password hashing.
  - **Database Driver**: `pymongo` (MongoDB Driver)
- **Database**: MongoDB Atlas
- **Frontend**: HTML, CSS, and JavaScript
  - **Styling**: Pure CSS for a clean and responsive design.
  - **Interactivity**: JavaScript for features like collapsible sections and percentage raise application.

## ⚙️ Environment Setup

Follow the steps below to set up and run the project locally.

### Prerequisites

- Python 3.x
- MongoDB Atlas account with a configured cluster
- `pip` (Python package manager)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-project.git
cd your-project
```

### 2. Configure Environment Variables

Create a `.env` file at the project root (same directory as `app.py`) and add your MongoDB Atlas connection URI:

```env
MONGODB_URI="mongodb+srv://<your-username>:<your-password>@<your-cluster>.mongodb.net/?retryWrites=true&w=majority"
```

**Important**: Replace `<your-username>`, `<your-password>`, and `<your-cluster>` with your MongoDB Atlas credentials.

### 3. Install Dependencies

Create a virtual environment (recommended) and install the required libraries:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install Flask pymongo python-dotenv werkzeug
```

### 4. Initialize the Database

The application will attempt to connect to the database and create the required indexes on startup. Ensure your `MONGODB_URI` is correct and that your IP is added to the allowed list in your MongoDB Atlas cluster.

### 5. Run the Application

```bash
flask run
```

Or, to run the script directly:

```bash
python app.py
```

The app will be available at `http://127.0.0.1:5000` (or the configured port, usually 5000).

## 💡 How to Use

1. **Access the App**: Open your browser and go to `http://127.0.0.1:5000`.
2. **Register/Login**:
   - If it's your first time, click "Register here" to create an account.
   - After registering, log in with your credentials.
3. **Calculate Net Salary**:
   - Fill in the fields under the "Earnings" and "Deductions" panels.
   - Click the "Calculate" button to see the estimated net salary.
4. **Manage Profiles**:
   - Expand the "Manage Profiles" section.
   - **Save**: Enter a name in the "Profile Name to Save" field and click "Save Profile".
   - **Load**: Select a saved profile from the "Load Profile" dropdown list.
5. **Simulate Salary Raise**:
   - Expand the "Adjust Salary by Raise (%)" section.
   - Enter the raise percentage and click "Apply Raise" to update the "Base Salary" field.
   - Click "Save as New Profile" to create a new profile with the updated salary.

## 🤝 Contributing

Contributions are welcome! If you have suggestions for improvements, bug fixes, or new features, feel free to:

1. Open an `issue` to discuss the proposed change.
2. Fork the project.
3. Create a `branch` for your feature (`git checkout -b feature/MyNewFeature`).
4. Make your changes and commit (`git commit -m 'feat: My new feature'`).
5. Push to the branch (`git push origin feature/MyNewFeature`).
6. Open a `Pull Request`.
