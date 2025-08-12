# 📊 Net Salary Calculator

A comprehensive net salary calculator built with Flask and MongoDB, allowing users to calculate their earnings, manage calculation profiles, and simulate salary raises.

[**Live Demo**](https://your-deploy-url.com) ✨

---

## ✨ Key Features

* 🔐 **User Authentication**: A complete registration, login, and logout system to protect each user's data.
* 💰 **Accurate Calculation**: Performs INSS (Social Security) and IRPF (Income Tax) calculations based on the 2025 tax tables and considers various other earnings and deductions.
* 👥 **Profile Management**: Save and load multiple calculation profiles to compare scenarios and track your financial evolution.
* 📈 **Raise Simulation**: An interactive tool to apply a percentage increase and visualize the impact on the net salary, with the option to save the new scenario.
* 📱 **Responsive Interface**: A modern and adaptive design, ensuring a great experience on both desktops and mobile devices.
* 💾 **Data Persistence**: Uses MongoDB Atlas to securely store user information and their profiles.

---

## 🚀 Tech Stack

* **Backend**: Python 🐍
    * **Web Framework**: Flask
    * **Security**: `werkzeug.security` for password hashing.
    * **Database Driver**: `pymongo`
* **Database**: MongoDB Atlas
* **Frontend**: HTML, CSS, and JavaScript
    * **Styling**: Pure CSS for a clean and responsive design.
    * **Interactivity**: JavaScript for dynamic features.

---

## ⚙️ Local Environment Setup

Follow the steps below to set up and run the project on your machine.

### Prerequisites

* Python 3.x
* MongoDB Atlas account with a configured cluster
* `pip` (Python package manager)

### 1. Clone the Repository

```bash
git clone [https://github.com/your-username/your-project.git](https://github.com/your-username/your-project.git)
cd your-project
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root and add your MongoDB Atlas connection string:

```env
MONGODB_URI="mongodb+srv://<your-username>:<your-password>@<your-cluster>.mongodb.net/?retryWrites=true&w=majority"
```

**Important**: Replace `<your-username>`, `<your-password>`, and `<your-cluster>` with your credentials.

### 3. Install Dependencies

It's recommended to create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install Flask pymongo python-dotenv werkzeug
```

### 4. Run the Application

```bash
flask run
```

The application will be available at `http://127.0.0.1:5000`.

---

## 💡 How to Use

1.  **Access the Application**: Open your browser and go to `http://127.0.0.1:5000`.
2.  **Register and Log In**: Create an account and access the system.
3.  **Calculate Salary**: Fill in the earnings and deductions fields and click "Calculate".
4.  **Manage Profiles**:
    * **Save**: Give the profile a name and click "Save".
    * **Load**: Select a saved profile to automatically fill in the fields.
5.  **Simulate Raises**:
    * Use the "Adjust Salary" section to apply a percentage increase and recalculate.

---

## 🤝 Contributing

Contributions are very welcome! If you have suggestions, bug fixes, or new features, feel free to:

1.  Open an `issue` to discuss the change.
2.  `Fork` the project.
3.  Create a `branch` for your feature (`git checkout -b feature/MyNewFeature`).
4.  `Commit` your changes (`git commit -m 'feat: Add my new feature'`).
5.  `Push` to the branch (`git push origin feature/MyNewFeature`).
6.  Open a `Pull Request`.
