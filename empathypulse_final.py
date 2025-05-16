import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
import datetime
from transformers import pipeline
import time
import os
import base64
from typing import Dict, List, Optional, Union, Tuple, Any
import json
import requests
import uuid

# Initialize session state variables
if "data_cache" not in st.session_state:
    st.session_state.data_cache = {}
# Page configuration
st.set_page_config(
    page_title="EmpathyPulse - Employee Sentiment Analysis",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App styling
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600&display=swap" rel="stylesheet">

<style>
html,main, body, [class*="st-"], .stApp {
    font-family: 'Roboto',Gabriola !important;
    font-size: 16px !important;
    color: 	#2c3e50 !important;  
}
   @keyframes gradientShift {
    0% {
        background-position: 0% 50%;
    }
    50% {
        background-position: 100% 50%;
    }
    100% {
        background-position: 0% 50%;
    }
}

@keyframes pulseGlow {
    0% {
        text-shadow: 0 0 0, 0 0 0, 0 0 0;
        transform: scale(1);
    }
    50% {
        text-shadow: 0 0 0, 0 0 0, 0 0 0;
        transform: scale(1.05);
    }
    100% {
        text-shadow: 0 0 0 , 0 0 0, 0 0 0;
        transform: scale(1);
    }
}
.glow-text {
    font-family: 'Gabriola', sans-serif;
    
    animation: pulseGlow 2s infinite;
    text-align: center;
    font-size: 3em;
}
.stApp {
background: linear-gradient(135deg, #ffe0f7, #00f0ff, #FFD599);
    background-size: 600% 600%;
    animation: gradientShift 15s ease infinite;
    color: #f8f8f8 !important;
}
    .main {
        padding: 2rem;
        }

    .stButton button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: bold;
    }
    .feedback-box {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: #f9f9f9;
    }
    .sidebar .sidebar-content {
        background-color: #f5f5f5;
    }
     h2, h3 {
        color: #2c3e50;
    }
    .positive {
        color: #27ae60;
        font-weight: bold;
    }
    .negative {
        color: #e74c3c;
        font-weight: bold;
    }
    .neutral {
        color: #3498db;
        font-weight: bold;
    }
    .employee-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f9f9f9;
        display: flex;
        align-items: center;
    }
    .employee-info {
        margin-left: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .sidebar .sidebar-content {
        background-color: #f0f0f0;
        padding: 20px;
        border-radius: 10px;
    }
    .sidebar .stButton button {
        background-color: #3498db;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        padding: 10px;
    }
    .sidebar .stButton button:hover {
        background-color: #2980b9;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .stButton button {
        background-color: #27ae60;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        padding: 10px;
    }
    .stButton button:hover {
        background-color: #2ecc71;
    }
</style>
""", unsafe_allow_html=True)

# GitHub API Integration
class GitHubDataStore:
    """Class to handle data storage in GitHub repository"""
    
    def __init__(self):
        """Initialize GitHub data store with API token and repo details"""
        # Get GitHub credentials from Streamlit secrets
        self.token = st.secrets.get("github_token", "")
        self.repo_owner = st.secrets.get("github_username", "")
        self.repo_name = st.secrets.get("github_repo", "")
        
        # Base API URL
        self.base_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        
        # Define data file paths
        self.employees_file = "data/employees.json"
        self.admins_file = "data/admins.json"
        self.feedback_file = "data/feedback.json"
        self.password_reset_file = "data/password_reset.json"
        
        # Store data in session state for caching
        if "data_cache" not in st.session_state:
            st.session_state.data_cache = {}
        
        # Initialize data if not exists
        self._ensure_data_files_exist()
    
    def _get_headers(self):
        """Get headers for GitHub API requests"""
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def _ensure_data_files_exist(self):
        """Initialize data files if they don't exist in the repository"""
        files_to_check = [
            {"path": self.employees_file, "default": []},
            {"path": self.admins_file, "default": []},
            {"path": self.feedback_file, "default": []},
            {"path": self.password_reset_file, "default": []}
        ]
        
        for file_info in files_to_check:
            try:
                # Try to get file content
                self._get_file_content(file_info["path"])
            except Exception:
                # File doesn't exist, create it
                self._create_file(file_info["path"], json.dumps(file_info["default"]), "Initialize data file")
    
    def _get_file_content(self, path):
        """
        Get file content from GitHub repository
        
        Parameters:
        -----------
        path : str
            Path to the file in the repository
            
        Returns:
        --------
        dict or list
            Parsed JSON content of the file
        """
        # Check cache first
        cache_key = f"content_{path}"
        if cache_key in st.session_state.data_cache:
            return st.session_state.data_cache[cache_key]
        
        # Make API request
        url = f"{self.base_url}/contents/{path}"
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code != 200:
            raise Exception(f"Failed to get file content: {response.json().get('message', 'Unknown error')}")
        
        # Decode content
        content_data = response.json()
        content = base64.b64decode(content_data["content"]).decode("utf-8")
        parsed_content = json.loads(content)
        
        # Save SHA for future updates
        st.session_state.data_cache[f"sha_{path}"] = content_data["sha"]
        
        # Cache content
        st.session_state.data_cache[cache_key] = parsed_content
        
        return parsed_content
    
    def _update_file(self, path, content, commit_message):
        """
        Update file in GitHub repository
        """
        # Fetch the latest SHA
        url = f"{self.base_url}/contents/{path}"
        response = requests.get(url, headers=self._get_headers())
        if response.status_code == 200:
            sha = response.json()["sha"]
            st.session_state.data_cache[f"sha_{path}"] = sha
        else:
            st.error(f"Failed to fetch latest SHA for {path}: {response.json().get('message', 'Unknown error')}")
            return False

        # Prepare payload
        payload = {
            "message": commit_message,
            "content": base64.b64encode(content.encode()).decode(),
            "sha": sha
        }

        # Make API request to update
        response = requests.put(url, headers=self._get_headers(), json=payload)
        if response.status_code not in [200, 201]:
            st.error(f"Failed to update file: {response.json().get('message', 'Unknown error')}")
            return False

        # Update cache
        st.session_state.data_cache[f"sha_{path}"] = response.json()["content"]["sha"]
        return True
    
    def _create_file(self, path, content, commit_message):
        """
        Create new file in GitHub repository
        
        Parameters:
        -----------
        path : str
            Path to the file in the repository
        content : str
            Content of the file
        commit_message : str
            Commit message for the creation
            
        Returns:
        --------
        bool
            True if creation was successful, False otherwise
        """
        # Make API request to create
        url = f"{self.base_url}/contents/{path}"
        payload = {
            "message": commit_message,
            "content": base64.b64encode(content.encode()).decode()
        }
        
        response = requests.put(url, headers=self._get_headers(), json=payload)
        
        if response.status_code not in [200, 201]:
            st.error(f"Failed to create file: {response.json().get('message', 'Unknown error')}")
            return False
        
        # Update SHA and cache
        st.session_state.data_cache[f"sha_{path}"] = response.json()["content"]["sha"]
        return True
    
    # Employee operations
    def get_employees(self):
        """Get all employees from GitHub"""
        try:
            return self._get_file_content(self.employees_file)
        except Exception as e:
            st.error(f"Error getting employees: {e}")
            return []
    
    def get_employee(self,emp_id: str) -> Optional[dict]:
        employees = self._get_file_content("data/employees.json")
        for employee in employees:
            if employee.get("emp_id") == emp_id:
                return employee
        return None
    
    def add_employee(self, employee_data):
        """Add new employee to GitHub"""
        employees = self.get_employees()
        
        # Generate a unique ID if not provided
        if not employee_data.get("emp_id"):
            employee_data["emp_id"] = str(uuid.uuid4())
        
        # Add creation timestamp
        employee_data["created_at"] = datetime.datetime.now().isoformat()
        
        employees.append(employee_data)
        return self._update_file(
            self.employees_file, 
            json.dumps(employees), 
            f"Add employee {employee_data.get('name')}"
        )
    
    def update_employee(self, emp_id, updated_data):
        """Update employee data in GitHub"""
        employees = self.get_employees()
        
        for i, employee in enumerate(employees):
            if employee.get("emp_id") == emp_id:
                employees[i].update(updated_data)
                return self._update_file(
                    self.employees_file,
                    json.dumps(employees),
                    f"Update employee {employee.get('name')}"
                )
        
        return False
    
    def delete_employee(self, emp_id):
        """Delete an employee and all related data from GitHub"""
        # Remove employee from employees.json
        employees = self.get_employees()
        employees = [emp for emp in employees if emp.get("emp_id") != emp_id]
        emp_update_result = self._update_file(
            self.employees_file,
            json.dumps(employees),
            f"Delete employee {emp_id}"
        )
        # Remove all feedback for this employee from feedback.json
        feedback_list = self.get_feedback()
        feedback_list = [fb for fb in feedback_list if fb.get("emp_id") != emp_id]
        feedback_update_result = self._update_file(
            self.feedback_file,
            json.dumps(feedback_list),
            f"Delete feedback for employee {emp_id}"
        )
        return emp_update_result and feedback_update_result
    
    # Admin operations
    def get_admins(self):
        """Get all admins from GitHub"""
        try:
            return self._get_file_content(self.admins_file)
        except Exception:
            return []
    
    def get_admin(self, admin_id):
        """Get admin by ID from GitHub"""
        admins = self.get_admins()
        for admin in admins:
            if admin.get("admin_id") == admin_id:
                return admin
        return None
    
    def add_admin(self, admin_data):
        """Add new admin to GitHub"""
        admins = self.get_admins()
        
        # Add creation timestamp
        admin_data["created_at"] = datetime.datetime.now().isoformat()
        
        admins.append(admin_data)
        return self._update_file(
            self.admins_file,
            json.dumps(admins),
            f"Add admin {admin_data.get('admin_id')}"
        )
    
    # Feedback operations
    def get_feedback(self):
        """Get all feedback from GitHub"""
        try:
            return self._get_file_content(self.feedback_file)
        except Exception:
            return []
    
    def add_feedback(self, feedback_data):
        """Add new feedback to GitHub"""
        feedback_list = self.get_feedback()
        
        # Generate a unique ID if not provided
        if not feedback_data.get("id"):
            feedback_data["id"] = str(uuid.uuid4())
        
        # Add timestamp and default status
        if not feedback_data.get("timestamp"):
            feedback_data["timestamp"] = datetime.datetime.now().isoformat()
        feedback_data["status"] = "pending"  # Default status
        
        feedback_list.append(feedback_data)
        return self._update_file(
            self.feedback_file,
            json.dumps(feedback_list),
            f"Add feedback from {feedback_data.get('emp_id')}"
        )
    
    def update_feedback(self, feedback_id, updated_data):
        """Update feedback in GitHub"""
        feedback_list = self.get_feedback()
        
        for i, feedback in enumerate(feedback_list):
            if str(feedback.get("id")) == str(feedback_id):
                feedback_list[i].update(updated_data)
                return self._update_file(
                    self.feedback_file,
                    json.dumps(feedback_list),
                    f"Update feedback {feedback_id}"
                )
        
        return False
    
    # Password reset operations
    def get_password_resets(self):
        """Get all password reset tokens from GitHub"""
        try:
             resets = self._get_file_content(self.password_reset_file)
             return resets
        except Exception as e:
            st.error(f"Error retrieving password resets: {e}")
            return []
    
    def add_password_reset(self, reset_data):
        """Add new password reset token to GitHub"""
        resets = self.get_password_resets()
        
        # Add timestamps
        reset_data["created_at"] = datetime.datetime.now().isoformat()
        if "expires_at" not in reset_data:
            expires_at = datetime.datetime.now() + datetime.timedelta(hours=1)
            reset_data["expires_at"] = expires_at.isoformat()
        
        resets.append(reset_data)
        return self._update_file(
            self.password_reset_file,
            json.dumps(resets),
            f"Add password reset for {reset_data.get('emp_id')}"
        )
    
    def update_password_reset(self, token, updated_data):
        """Update password reset token in GitHub"""
        resets = self.get_password_resets()
        
        for i, reset in enumerate(resets):
            if reset.get("token") == token:
                resets[i].update(updated_data)
                return self._update_file(
                    self.password_reset_file,
                    json.dumps(resets),
                    f"Update password reset token"
                )
        
        return False
    
    def get_password_reset_by_token(self, token):
        """Get password reset by token from GitHub"""
        resets = self.get_password_resets()
        for reset in resets:
            if reset.get("token") == token:
                return reset
        return None

# Initialize GitHub data store
#@st.cache_resource
def get_github_store():
    """Get or create GitHub data store instance"""
    return GitHubDataStore()

github_store = get_github_store()
# Initialize the emotion model (with caching to improve performance)
@st.cache_resource
def load_classifiers():
    """Load and cache the emotion classification models"""
    try:
        emotion_classifier = pipeline("text-classification", 
                                    model="bhadresh-savani/distilbert-base-uncased-emotion")
        
        # Add a second model for more nuanced sentiment analysis
        sentiment_classifier = pipeline("sentiment-analysis", 
                                    model="distilbert-base-uncased-finetuned-sst-2-english")
        
        return emotion_classifier, sentiment_classifier
    except Exception as e:
        st.error(f"Failed to load emotion models: {e}")
        return None, None

emotion_classifier, sentiment_classifier = load_classifiers()

# Helper function to analyze feedback
def analyze_feedback(feedback_text: str) -> Dict[str, Union[str, float]]:
    """
    Analyze employee feedback to detect emotions and sentiment
    
    Parameters:
    -----------
    feedback_text : str
        The text to analyze
        
    Returns:
    --------
    Dict[str, Union[str, float]]
        Dictionary with emotion and sentiment analysis results
    """
    try:
        emotion_result = emotion_classifier(feedback_text)[0]
        sentiment_result = sentiment_classifier(feedback_text)[0]
        
        return {
            'emotion': emotion_result['label'],
            'emotion_confidence': emotion_result['score'],
            'sentiment': sentiment_result['label'],
            'sentiment_confidence': sentiment_result['score']
        }
    except Exception as e:
        st.error(f"Error analyzing feedback: {e}")
        return {
            'emotion': 'neutral',
            'emotion_confidence': 0.5,
            'sentiment': 'NEUTRAL',
            'sentiment_confidence': 0.5
        }

# Password security functions
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt for secure storage
    
    Parameters:
    -----------
    password : str
        The plain text password to hash
        
    Returns:
    --------
    str
        Hashed password
    """
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password.decode('utf-8')

def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Verify a password against a stored hash
    
    Parameters:
    -----------
    stored_password : str
        The hashed password from the database
    provided_password : str
        The password to verify
        
    Returns:
    --------
    bool
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(provided_password.encode(), stored_password.encode())
    except Exception:
        return False

# Session validation
def validate_session() -> bool:
    """
    Validate the current user session
    
    Returns:
    --------
    bool
        True if session is valid, False otherwise
    """
    if 'last_activity' in st.session_state:
        # Check if session is more than 30 minutes old
        if datetime.datetime.now() - st.session_state.last_activity > datetime.timedelta(minutes=30):
            # Session timeout
            logout()
            return False
    
    # Update last activity timestamp
    st.session_state.last_activity = datetime.datetime.now()
    return True

# Add sample departments for dropdown
DEPARTMENTS = ["Engineering", "Marketing", "Sales", "Finance", "Human Resources", "Customer Support", "Operations", "Research & Development"]

# Function to check if an admin exists
@st.cache_data(ttl=300)  # Cache for 5 minutes
def admin_exists() -> bool:
    """
    Check if any admin account exists
    
    Returns:
    --------
    bool
        True if at least one admin exists, False otherwise
    """
    admins = github_store.get_admins()
    return len(admins) > 0


# Admin setup function
def setup_admin():
    """Setup page for creating the initial admin account"""
    st.title("Admin Setup")
    
    # Check if admin exists
    if not admin_exists():  # No admin found, so setup is required
        st.info("No admin account found. Please set up an admin account.")
        
        with st.form("admin_setup_form"):
            admin_id = st.text_input("Admin ID")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Setup Admin")
            
            if submit:
                if not admin_id or not password:
                    st.error("Admin ID and Password are required.")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters long.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    # Add admin to GitHub
                    github_store.add_admin({
                        "admin_id": admin_id,
                        "password": hash_password(password)
                    })
                    st.success("Admin setup complete! You can now log in as Admin.")
                    time.sleep(2)  # Give user time to read the message
                    st.rerun()
    else:
        st.success("Admin is already set up. Please log in.")
        admin_login()

# Admin login
def admin_login():
    """Login page for admin users"""
    st.markdown("""<h1 class='glow-text' style = 'font-family:gabriola;font-size:50px;text-align:center;color:grey;'>Admin (HR) Dashboard Login</h1>""", unsafe_allow_html=True)
    
    with st.form("admin_login_form"):
        admin_id = st.text_input("Admin ID")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Log In")
        
        if submit:
            if not admin_id or not password:
                st.error("Please enter both Admin ID and Password.")
            else:
                admin = github_store.get_admin(admin_id)
                
                if admin and verify_password(admin['password'], password):
                    st.session_state.role = "admin"
                    st.session_state.admin_id = admin['admin_id']
                    st.session_state.last_activity = datetime.datetime.now()
                    st.success(f"Welcome back, Admin {admin_id}!")
                    time.sleep(1)
                    st.session_state.page = "admin_dashboard"  # Redirect to dashboard
                    st.rerun()
                else:
                    st.error("Invalid Admin ID or Password.")

# Employee Sign Up
def signup():
    """Signup page for new employees"""
    st.markdown("""<h1 class="glow-text" style = 'font-family:gabriola;font-size:50px;text-align:center;color:brown;'> Employee Signup</h1>""",unsafe_allow_html=True)

    # Clear the form if the flag is set
    if st.session_state.get("clear_signup_form_next", False):
        clear_signup_form()
        st.session_state["clear_signup_form_next"] = False

    with st.form("signup_form"):
        emp_id = st.text_input("💼 Employee ID", key="signup_emp_id")
        name = st.text_input("👤 Full Name", key="signup_name")
        dept = st.selectbox("🏢 Department", options=DEPARTMENTS, key="signup_dept")
        password = st.text_input("🔒 Password", type="password", key="signup_password")
        confirm_password = st.text_input("🔒 Confirm Password", type="password", key="signup_confirm_password")
        submit = st.form_submit_button("Create Account")
        
        if submit:
            if not emp_id or not name or not dept or not password:
                st.error("Employee ID, Name, Department, and Password are required.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                # Check if employee already exists
                existing_emp = github_store.get_employee(emp_id)
                
                if existing_emp:
                    st.error("Employee ID already exists. Please log in or use a different ID.")
                else:
                    # Create employee data
                    employee_data = {
                        "emp_id": emp_id,
                        "name": name,
                        "dept": dept,
                        "password": hash_password(password)
                    }
                    
                    # Add to GitHub
                    github_store.add_employee(employee_data)
                    
                    st.success("Account created successfully! Please log in.")
                    time.sleep(2)  # Give user time to read the message
                    st.session_state["clear_signup_form_next"] = True
                    st.rerun()

# Employee Login
def login():
    """Login page for employees"""
    st.markdown("""
                <h1 class='glow-text' style = '
                font-family : gabriola;
                color : red;
                text-align:center;'> Employee Login</h1>
                """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        emp_id = st.text_input("💼 Employee ID")
        password = st.text_input("🔒 Password", type="password")
        
        submit = st.form_submit_button("Log In")
        
        if submit:
            if not emp_id or not password:
                st.error("Please enter both Employee ID and Password.")
            else:
                employee = github_store.get_employee(emp_id)
                
                if employee and verify_password(employee['password'], password):
                    st.session_state.role = "employee"
                    st.session_state.employee_name = employee['name']
                    st.session_state.employee_id = employee['emp_id']
                    st.session_state.employee_dept = employee['dept']
                    st.session_state.last_activity = datetime.datetime.now()
                    st.success(f"Welcome back, {employee['name']}!")
                    time.sleep(1)
                    st.session_state.page = "employee_dashboard"  # Redirect to dashboard
                    st.rerun()
                else:
                    st.error("Invalid Employee ID or Password.")
    
    forgot_password = st.button("Forgot Password?")
    if forgot_password:
        st.session_state.page = "forgot_password"
        st.rerun()

# Password recovery
def forgot_password():
    """Password recovery page for employees"""
    st.markdown("""<h1 class="glow-text" style='text-align: center; color: red;font-family:Times new roman;font-size:50px'>Password Recovery</h1>""", unsafe_allow_html=True)
    with st.form("forgot_password_form"):
        emp_id = st.text_input("💼 Employee ID")
        submit = st.form_submit_button("Request Password Reset")
        
        if submit:
            if not emp_id:
                st.error("Please enter your Employee ID.")
            else:
                employee = github_store.get_employee(emp_id)
                
                if employee:
                    # Generate reset token
                    token = str(uuid.uuid4())
                    
                    # Save token to GitHub
                    expires_at = datetime.datetime.now() + datetime.timedelta(hours=1)
                    github_store.add_password_reset({
                        "emp_id": emp_id,
                        "token": token,
                        "used": False,
                        "expires_at": expires_at.isoformat()
                    })
                    
                    # In a real app, this would send an email
                    # For demo purposes, just show the reset link
                    st.success("Password reset link generated:")
                    st.code(f"http://localhost:8501/?reset_token={token}")
                    st.info("In a real application, this would be sent to your email.")
                else:
                    st.error("Employee ID not found.")
    
    back_button = st.button("Back to Login")
    if back_button:
        st.session_state.page = "login"
        st.rerun()

# Reset password page
def reset_password():
    """Reset password page for employees"""
    st.markdown("""<h1 class="glow-text" style = 'font-family:gabriola;font-size:50px;color:red;text-align:center;'>Reset Password<h1>""", unsafe_allow_html=True)
    
    # Get token from query params
    query_params = st.query_params
    token = query_params.get("reset_token")

    # Normalize token (in case it's a list or None)
    if isinstance(token, list):
        token = token[0]
    elif token is None:
        token = ""
    
    if not token:
        st.error("Invalid or missing reset token.")
        st.button("Back to Login", on_click=lambda: setattr(st.session_state, "page", "login"))
        return
    
    # Validate token
    reset_data = github_store.get_password_reset_by_token(token)
    st.write("✅ Matched Reset Data:", reset_data)
    
    if not reset_data:
        st.error("Invalid reset token.")
        st.button("Back to Login", on_click=lambda: setattr(st.session_state, "page", "login"))
        return
    
    # Check if token is expired or already used
    try:
        expires_at = datetime.datetime.fromisoformat(reset_data["expires_at"])
        if expires_at < datetime.datetime.now() or reset_data.get("used", False):
            st.error("Reset token has expired or already been used.")
            st.button("Back to Login", on_click=lambda: setattr(st.session_state, "page", "login"))
            return
    except Exception:
        st.error("Invalid token data.")
        st.button("Back to Login", on_click=lambda: setattr(st.session_state, "page", "login"))
        return
    
    # Show reset form
    with st.form("reset_password_form"):
        new_password = st.text_input("🔒 New Password", type="password")
        confirm_password = st.text_input("🔒 Confirm New Password", type="password")
        
        submit = st.form_submit_button("Reset Password")
        
        if submit:
            if not new_password:
                st.error("Please enter a new password.")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                # Update employee password
                employee = github_store.get_employee(reset_data["emp_id"])
                
                if employee:
                    github_store.update_employee(
                        employee["emp_id"],
                        {"password": hash_password(new_password)}
                    )
                    
                    github_store.update_password_reset(
                        token,
                        {"used": True}
                    )
                    
                    st.success("Password reset successfully! Please log in with your new password.")
                    time.sleep(2)
                    st.query_params={}
                    st.session_state.page = "login"
                    st.rerun()


def logout():
    """Log out the current user"""
    # Clear session state
    for key in list(st.session_state.keys()):
        if key != "page":  # Keep page state to redirect properly
            del st.session_state[key]
    
    st.session_state.page = "login"
    st.rerun()

# Employee dashboard page
def employee_dashboard():
    """Dashboard page for employees"""
    if not validate_session() or not st.session_state.get("employee_id"):
        logout()
        return

    # Animated jump-in per-letter, then gradient animation for welcome banner
    employee_name = st.session_state.employee_name
    welcome_text = f"Welcome, {employee_name}!"
    animated_html = "<div class='employee-gradient-text'>"
    for i, char in enumerate(welcome_text):
        delay = i * 0.07  # 70ms stagger per letter
        # Add a non-breaking space for spaces
        display_char = char if char != ' ' else '&nbsp;'
        animated_html += f"<span class='jump-in' style='animation-delay:{delay:.2f}s'>{display_char}</span>"
    animated_html += "</div>"

    st.markdown("""
<style>
.employee-gradient-text {
    font-family: 'Gabriola', cursive;
    font-size: 2.8em;
    font-weight: bold;
    text-align: center;
    margin-bottom: 20px;
    display: inline-block;
    width: 100%;
}
.employee-gradient-text .jump-in {
    display: inline-block;
    opacity: 0;
    transform: translateY(-60px) scale(0.7) rotate(-10deg);
    animation: jumpIn 0.6s cubic-bezier(.68,-0.55,.27,1.55) forwards;
}
@keyframes jumpIn {
    0% {
        opacity: 0;
        transform: translateY(-60px) scale(0.7) rotate(-10deg);
    }
    60% {
        opacity: 1;
        transform: translateY(10px) scale(1.1) rotate(2deg);
    }
    80% {
        transform: translateY(-5px) scale(0.98) rotate(-2deg);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1) rotate(0deg);
        /* After jump-in, enable gradient animation */
        background: linear-gradient(270deg, #ff6a00, #fa709a, #b721ff, #000000, #00ffb3, #ff00c8, #ffea00, #ff6a00, #fa709a, #b721ff, #000000, #00ffb3, #ff00c8, #ffea00, #ff6a00);
        background-size: 4000% 4000%;
        color: transparent;
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: flowing-gradient 15s linear infinite;
    }
}
@keyframes flowing-gradient {
    0% { background-position: 0% 50%; }
    100% { background-position: 100% 50%; }
}
</style>
""", unsafe_allow_html=True)
    st.markdown(animated_html, unsafe_allow_html=True)

    # User profile and info
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"<div style = 'font-family:gabriola;font-size:20px'><span style ='font-weight:bold;'>Employee Name:</span> {st.session_state.employee_name}</div>", unsafe_allow_html=True)
        st.markdown(f"**Employee ID:** {st.session_state.employee_id}")
        st.markdown(f"**Department:** {st.session_state.employee_dept}")
    st.divider()

    # Tabs for different sections
    tab1, tab2 = st.tabs(["Submit Feedback", "My Feedback History"])

    with tab1:
        st.subheader("Share Your Thoughts")

        # At the top of your feedback form section (before the form widgets)
        if st.session_state.get("clear_feedback_form_next", False):
            clear_feedback_form()
            st.session_state["clear_feedback_form_next"] = False

        with st.form("feedback_form"):
            mood = st.radio(
                "How are you feeling today?",
                options=["😄 Great", "🙂 Good", "😐 Neutral", "☹️ Not Good", "😫 Terrible"],
                horizontal=True,
                key="mood"
            )
            work_satisfaction = st.slider("Work Satisfaction", 1, 10, key="work_satisfaction")
            team_satisfaction = st.slider("Team Collaboration", 1, 10, key="team_satisfaction")
            management_satisfaction = st.slider("Management Support", 1, 10, key="management_satisfaction")
            feedback_text = st.text_area("Share your thoughts or concerns:", height=150, key="feedback_text")
            anonymous = st.checkbox("Submit anonymously", key="anonymous")

            submit = st.form_submit_button("Submit Feedback")

            if submit:
                if not feedback_text:
                    st.error("Please provide some feedback text.")
                else:
                    mood_mapping = {
                        "😄 Great": 5,
                        "🙂 Good": 4,
                        "😐 Neutral": 3,
                        "☹️ Not Good": 2,
                        "😫 Terrible": 1
                    }
                    mood_score = mood_mapping.get(mood, 3)
                    analysis_result = analyze_feedback(feedback_text)

                    feedback_data = {
                        "id": str(uuid.uuid4()),
                        "emp_id": "Anonymous" if anonymous else st.session_state.employee_id,
                        "dept": st.session_state.employee_dept,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "mood": mood,
                        "mood_score": mood_score,
                        "work_satisfaction": work_satisfaction,
                        "team_satisfaction": team_satisfaction,
                        "management_satisfaction": management_satisfaction,
                        "feedback_text": feedback_text,
                        "emotion": analysis_result.get("emotion"),
                        "emotion_confidence": analysis_result.get("emotion_confidence"),
                        "sentiment": analysis_result.get("sentiment"),
                        "sentiment_confidence": analysis_result.get("sentiment_confidence"),
                        "status": "pending"
                    }

                    if github_store.add_feedback(feedback_data):
                        st.success("Thank you for your feedback!")
                        time.sleep(2)
                        st.session_state["clear_feedback_form_next"] = True
                        st.rerun()
                    else:
                        st.error("Error saving feedback. Please try again.")

    with tab2:
        st.subheader("Your Feedback History")
        all_feedback = github_store.get_feedback()
        employee_feedback = [f for f in all_feedback if f.get("emp_id") == st.session_state.employee_id]

        if not employee_feedback:
             st.info("You haven't submitted any feedback yet.")
        else:
            employee_feedback.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            for feedback in employee_feedback:
                with st.expander(f"Feedback on {feedback.get('timestamp', 'Unknown date')[:10]}", expanded=False):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**Mood:** {feedback.get('mood', 'Unknown')}")
                        st.markdown(f"**Work Satisfaction:** {feedback.get('work_satisfaction', 0)}/10")
                        st.markdown(f"**Team Collaboration:** {feedback.get('team_satisfaction', 0)}/10")
                        st.markdown(f"**Management Support:** {feedback.get('management_satisfaction', 0)}/10")

                    with col2:
                        sentiment = feedback.get("sentiment", "NEUTRAL")
                        sentiment_class = "positive" if sentiment == "POSITIVE" else "negative" if sentiment == "NEGATIVE" else "neutral"
                        st.markdown(f"**Sentiment:** <span class='{sentiment_class}'>{sentiment}</span>", unsafe_allow_html=True)

                        emotion = feedback.get("emotion", "neutral")
                        st.markdown(f"**Detected Emotion:** {emotion.capitalize()}")

                    st.markdown("**Your Feedback:**")
                    st.markdown(f"> {feedback.get('feedback_text', 'No text provided')}")

# Clear the Add employee Form
def clear_employee_form():
    st.session_state["new_emp_id_page"] = ""
    st.session_state["new_name_page"] = ""
    st.session_state["new_dept_page"] = DEPARTMENTS[0]
    st.session_state["new_password_page"] = ""

#Clear the employee feedback form
def clear_feedback_form():
    st.session_state["mood"] = "😐 Neutral"
    st.session_state["work_satisfaction"] = 7
    st.session_state["team_satisfaction"] = 7
    st.session_state["management_satisfaction"] = 7
    st.session_state["feedback_text"] = ""
    st.session_state["anonymous"] = False

# Clear the signup form
def clear_signup_form():
    st.session_state["signup_emp_id"] = ""
    st.session_state["signup_name"] = ""
    st.session_state["signup_dept"] = DEPARTMENTS[0]
    st.session_state["signup_password"] = ""
    st.session_state["signup_confirm_password"] = ""

# Admin dashboard
def admin_dashboard():
    """Dashboard page for admin users"""
    if not validate_session() or not st.session_state.get("admin_id"):
        logout()
        return
    
    st.markdown("""<h1 class="glow-text" style='text-align: center; color: purple;font-family:Cambria;font-size:50px'>Admin Dashboard</h1>""", unsafe_allow_html=True)
    st.markdown(
    f"<div style='font-size:2em; color:#6c3483; font-family:Gabriola, cursive; text-align:center; font-weight:bold; margin-bottom:20px;'>Welcome, Admin {st.session_state.admin_id}</div>",
    unsafe_allow_html=True
)

    all_feedback = github_store.get_feedback()

    for feedback in all_feedback:
        notify_admin_if_priority_negative(feedback, send_to_hr_dashboard)
    
    # Tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["Sentiment Overview", "Employee Feedback", "Manage Employees"])
    
    with tab1:
        st.subheader("Employee Sentiment Overview")
        
        # Get all feedback
        all_feedback = github_store.get_feedback()
        
        if not all_feedback:
            st.info("No feedback data available yet.")
        else:
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(all_feedback)
            
            # Add date column
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            
            # Recent data - last 30 days
            today = datetime.datetime.now().date()
            thirty_days_ago = today - datetime.timedelta(days=30)
            recent_df = df[df['date'] >= thirty_days_ago]
            
            # Department filter
            unique_depts = list(df['dept'].unique())
            selected_dept = st.selectbox("Filter by Department", ["All"] + unique_depts)
            
            if selected_dept != "All":
                filtered_df = df[df['dept'] == selected_dept]
                recent_filtered_df = recent_df[recent_df['dept'] == selected_dept]
            else:
                filtered_df = df
                recent_filtered_df = recent_df
            
            # Display stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_feedback = len(filtered_df)
                st.metric("Total Feedback", total_feedback)
            
            with col2:
                avg_work_satisfaction = filtered_df['work_satisfaction'].mean() if 'work_satisfaction' in filtered_df else 0
                st.metric("Avg Work Satisfaction", f"{avg_work_satisfaction:.1f}/10")
            
            with col3:
                avg_team_satisfaction = filtered_df['team_satisfaction'].mean() if 'team_satisfaction' in filtered_df else 0
                st.metric("Avg Team Satisfaction", f"{avg_team_satisfaction:.1f}/10")
            
            with col4:
                avg_management_satisfaction = filtered_df['management_satisfaction'].mean() if 'management_satisfaction' in filtered_df else 0
                st.metric("Avg Management Rating", f"{avg_management_satisfaction:.1f}/10")
            
            # Sentiment trend over time
            st.subheader("Sentiment Trend Over Time")
            
            if 'date' in filtered_df and 'sentiment' in filtered_df:
                # Group by date and sentiment
                sentiment_by_date = filtered_df.groupby(['date', 'sentiment']).size().reset_index(name='count')
                
                # Pivot for plotting
                sentiment_pivot = sentiment_by_date.pivot(index='date', columns='sentiment', values='count').fillna(0)
                
                # Sort by date
                sentiment_pivot = sentiment_pivot.sort_index()
                
                # Plot
                fig = px.line(sentiment_pivot, x=sentiment_pivot.index, y=sentiment_pivot.columns,
                            title="Sentiment Trends Over Time",
                            labels={"value": "Count", "variable": "Sentiment", "date": "Date"})
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Emotion distribution
            st.subheader("Emotion Distribution")
            
            if 'emotion' in filtered_df:
                emotion_counts = filtered_df['emotion'].value_counts().reset_index()
                emotion_counts.columns = ['emotion', 'count']
                
                fig = px.pie(emotion_counts, values='count', names='emotion',
                            title="Distribution of Emotions in Feedback")
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Department comparison
            if selected_dept == "All" and 'dept' in df:
                st.subheader("Department Comparison")
                
                dept_satisfaction = df.groupby('dept')[['work_satisfaction', 'team_satisfaction', 'management_satisfaction']].mean().reset_index()
                
                fig = px.bar(dept_satisfaction, x='dept', y=['work_satisfaction', 'team_satisfaction', 'management_satisfaction'],
                            title="Average Satisfaction by Department",
                            labels={"value": "Average Rating (1-10)", "variable": "Metric", "dept": "Department"},
                            barmode='group')
                
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Employee Feedback")
        
        # Get all feedback
        all_feedback = github_store.get_feedback()
        
        if not all_feedback:
            st.info("No feedback data available yet.")
        else:
            # Convert to DataFrame for filtering
            df = pd.DataFrame(all_feedback)
            
            # Add date column
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            
            # Filters
            col1, col2, col3,col4 = st.columns(4)
            
            with col1:
                unique_depts = list(df['dept'].unique())
                selected_dept = st.selectbox("Department", ["All"] + unique_depts)
            
            with col2:
                date_range = st.date_input(
                    "Date Range",
                    value=(df['date'].min(), df['date'].max() if not df.empty else datetime.date.today()),
                    min_value=df['date'].min() if not df.empty else None,
                    max_value=datetime.date.today()
                )
            
            with col3:
                sentiment_options = ["All", "POSITIVE", "NEGATIVE", "NEUTRAL"]
                selected_sentiment = st.selectbox("Sentiment", sentiment_options)

            with col4:
                status_options = ["All", "Pending", "complete"]
                selected_status = st.selectbox("Status", status_options)
            
            # Apply filters
            filtered_df = df.copy()
            # Normalize the status column and dropdown values for consistent comparison
            if 'status' in filtered_df.columns:
                filtered_df['status'] = filtered_df['status'].fillna("").str.lower()  # Normalize to lowercase
                selected_status = selected_status.lower()  # Normalize dropdown value to lowercase

            if selected_status != "all":
                filtered_df = filtered_df[filtered_df['status'] == selected_status]

            if selected_dept != "All":
                filtered_df = filtered_df[filtered_df['dept'] == selected_dept]

            if len(date_range) == 2:
                start_date, end_date = date_range
                filtered_df = filtered_df[(filtered_df['date'] >= start_date) & (filtered_df['date'] <= end_date)]

            if selected_sentiment != "All":
                filtered_df = filtered_df[filtered_df['sentiment'] == selected_sentiment]

            if selected_status != "All":
                # Ensure 'status' column exists and handle missing values
                if 'status' in filtered_df.columns:
                    filtered_df['status'] = filtered_df['status'].fillna("").astype(str)
                    filtered_df = filtered_df[filtered_df['status'].str.lower() == selected_status.lower()]
                else:
                    st.error("The 'status' column is missing in the feedback data.")
                    return

            # Sort by timestamp (newest first)
            filtered_df = filtered_df.sort_values(by='timestamp', ascending=False)
            
            # Display feedback
            if filtered_df.empty:
                st.info("No feedback matches the selected filters.")
            else:
                for i, feedback in enumerate(filtered_df.to_dict(orient="records")):
                    feedback_id = str(feedback.get("id", f"unknown_{i}"))  # Ensure feedback_id is a string
                    emp_name = feedback.get("emp_id", "Anonymous")
                    department = feedback.get("dept", "Unknown Department")
                    date = feedback.get("timestamp", "Unknown Date")[:10]
                    sentiment = feedback.get("sentiment", "N/A")
                    sentiment_confidence = feedback.get("sentiment_confidence", 0.0)
                    emotion = feedback.get("emotion", "Neutral")
                    emotion_confidence = feedback.get("emotion_confidence", 0.0)
                    text = feedback.get("feedback_text", "No feedback provided")
                    status = feedback.get("status", "pending")
                    work_satisfaction = feedback.get("work_satisfaction", 0)
                    team_satisfaction = feedback.get("team_satisfaction", 0)
                    management_satisfaction = feedback.get("management_satisfaction", 0)

                    with st.expander(f"Feedback from {department} on {date}"):
                        col1, col2 = st.columns([1, 3])

                        with col1:
                            st.markdown(f"**Employee:** {emp_name}")
                            st.markdown(f"**Mood:** {feedback.get('mood', 'Unknown')}")
                            st.markdown(f"**Work Satisfaction:** {work_satisfaction}/10")
                            st.markdown(f"**Team Collaboration:** {team_satisfaction}/10")
                            st.markdown(f"**Management Support:** {management_satisfaction}/10")

                        with col2:
                            st.markdown(f"**Feedback Content:**")
                            st.markdown(f"> {text}")
                            st.markdown(f"**Sentiment Analysis:** {sentiment} ({sentiment_confidence:.2f})")
                            st.markdown(f"**Emotion Detection:** {emotion.capitalize()} ({emotion_confidence:.2f})")

                        # Only show "Mark Complete" button if status is pending
                        if status == "pending":
                            if st.button(f"Mark Complete (ID: {feedback_id})", key=f"mark_complete_{feedback_id}_{i}"):
                                success = github_store.update_feedback(feedback_id, {"status": "complete", "alert_shown": True})
                                if success:
                                    st.success(f"Feedback ID {feedback_id} marked as complete!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to mark Feedback ID {feedback_id} as complete.")
                        else:
                            st.markdown("**Status:** ✅ Completed")
    
    with tab3:
        st.subheader("Manage Employees")
        
        # Get all employees
        employees = github_store.get_employees()
        
        # Convert to DataFrame for display
        if employees:
            emp_df = pd.DataFrame(employees)
            
            # Add creation date if available
            if 'created_at' in emp_df:
                emp_df['created_date'] = pd.to_datetime(emp_df['created_at']).dt.date
            
            # Filter by department
            unique_depts = list(emp_df['dept'].unique()) if 'dept' in emp_df else []
            selected_dept = st.selectbox("Filter by Department", ["All"] + unique_depts, key="emp_dept_filter")
            
            if selected_dept != "All":
                emp_df = emp_df[emp_df['dept'] == selected_dept]
            
            # Sort by name
            if 'name' in emp_df:
                emp_df = emp_df.sort_values(by='name')
            
            # Display employees
            st.subheader("Employee Directory")
            
            for _, employee in emp_df.iterrows():
                with st.expander(f"{employee.get('name')} - {employee.get('dept')}", expanded=False):
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        st.markdown(f"### {employee.get('name')}")
                        st.markdown(f"**Employee ID:** {employee.get('emp_id')}")
                        st.markdown(f"**Department:** {employee.get('dept')}")
                        
                        if 'created_at' in employee:
                            created_date = datetime.datetime.fromisoformat(employee.get('created_at')).strftime("%Y-%m-%d")
                            st.markdown(f"**Joined:** {created_date}")
                        
                        # Count feedback submissions
                        all_feedback = github_store.get_feedback()
                        emp_feedback = [f for f in all_feedback if f.get('emp_id') == employee.get('emp_id')]
                        
                        st.markdown(f"**Feedback Submissions:** {len(emp_feedback)}")
                        
                        # Calculate average sentiment
                        if emp_feedback:
                            positive_count = sum(1 for f in emp_feedback if f.get('sentiment') == 'POSITIVE')
                            negative_count = sum(1 for f in emp_feedback if f.get('sentiment') == 'NEGATIVE')
                            
                            if positive_count > negative_count:
                                st.markdown("**Overall Sentiment:** <span class='positive'>Mostly Positive</span>", unsafe_allow_html=True)
                            elif negative_count > positive_count:
                                st.markdown("**Overall Sentiment:** <span class='negative'>Mostly Negative</span>", unsafe_allow_html=True)
                            else:
                                st.markdown("**Overall Sentiment:** <span class='neutral'>Mixed or Neutral</span>", unsafe_allow_html=True)
        else:
            st.info("No employees registered yet.")
        
        # Add Employee section moved to its own page. Use the sidebar navigation to add employees.
        # ...existing code...

# Admin delete employee page
def admin_delete_employee_page():
    """Admin page for deleting employees."""
    st.markdown("""<h1 style = "font-family : gabriola;color:Red;justify-content:center;text-align:center">Delete employee records only when the employee is no longer with the organization.</h1""", unsafe_allow_html=True)
    st.markdown("""<h6 class="glow-text" style = 'color:red;text-align:center;'>Remove an employee and all their feedback from the system.</h6>""",unsafe_allow_html=True)

    employees = github_store.get_employees()
    emp_df = pd.DataFrame(employees) if employees else pd.DataFrame()

    if not emp_df.empty:
        unique_depts = list(emp_df['dept'].unique())
        selected_dept = st.selectbox("Select Department", ["All"] + unique_depts, key="delete_emp_dept_filter_page")
        if selected_dept != "All":
            emp_df = emp_df[emp_df['dept'] == selected_dept]

        search_term = st.text_input("Search Employee by ID or Name", key="delete_emp_search_page")
        if search_term:
            emp_df = emp_df[
                emp_df['emp_id'].str.contains(search_term, case=False, na=False) |
                emp_df['name'].str.contains(search_term, case=False, na=False)
            ]

        emp_options = [
            f"{row['name']} ({row['emp_id']}) - {row['dept']}"
            for _, row in emp_df.iterrows()
        ]
        selected_emp = st.selectbox("Select Employee to Delete", emp_options, key="delete_emp_select_page") if emp_options else None

        if selected_emp:
            emp_id = selected_emp.split("(")[-1].split(")")[0]
            if st.button("Delete Employee", key="delete_emp_btn_page"):
                st.session_state["confirm_delete_emp_id_page"] = emp_id

        if st.session_state.get("confirm_delete_emp_id_page"):
            emp_id = st.session_state["confirm_delete_emp_id_page"]
            emp = next((e for e in employees if e["emp_id"] == emp_id), None)
            if emp:
                st.warning(f"Are you sure you want to delete employee record: {emp['name']} ({emp['emp_id']}) from {emp['dept']}?", icon="⚠️")
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    if st.button("Yes, Delete", key="confirm_delete_emp_btn_page"):
                        github_store.delete_employee(emp_id)
                        st.success(f"Employee {emp['name']} deleted.")
                        st.session_state.pop("data_cache", None)  # Clear cache to force fresh fetch
                        del st.session_state["confirm_delete_emp_id_page"]
                        st.rerun()
                with col_cancel:
                    if st.button("Cancel", key="cancel_delete_emp_btn_page"):
                        del st.session_state["confirm_delete_emp_id_page"]
    else:
        st.info("No employees available to delete.")

def admin_add_employee_page():
    """Admin page for adding new employees."""
    st.markdown("""<h1 class="glow-text" style = 'font-family:Gabriola;text-align:center;font-size:50px;color:grey;'>Add New Employee</h1>""", unsafe_allow_html=True)
    st.markdown("""<h6 style ='color:brown;text-align:center'>Register a new employee in the system.</h6>""", unsafe_allow_html=True)

    # At the top of your admin_add_employee_page() or before rendering the form:
    if st.session_state.get("clear_employee_form_next", False):
        clear_employee_form()
        st.session_state["clear_employee_form_next"] = False

    with st.form("add_employee_form_page"):
        new_emp_id = st.text_input("Employee ID", key="new_emp_id_page")
        new_name = st.text_input("Full Name", key="new_name_page")
        new_dept = st.selectbox("Department", options=DEPARTMENTS, key="new_dept_page")
        new_password = st.text_input("Initial Password", type="password", key="new_password_page")

        col_submit, col_clear = st.columns([2, 1])
        with col_submit:
            submit = st.form_submit_button("Add Employee")
        with col_clear:
            clear = st.form_submit_button("Clear Form", on_click=clear_employee_form)

        if submit:
            if not new_emp_id or not new_name or not new_dept or not new_password:
                st.error("All fields are required.")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long.")
            else:
                existing_emp = github_store.get_employee(new_emp_id)
                if existing_emp:
                    st.error("Employee ID already exists.")
                else:
                    employee_data = {
                        "emp_id": new_emp_id,
                        "name": new_name,
                        "dept": new_dept,
                        "password": hash_password(new_password)
                    }
                    github_store.add_employee(employee_data)
                    st.success(f"Employee {new_name} added successfully!")
                    time.sleep(2)
                    st.session_state["clear_employee_form_next"] = True
                    st.rerun()

# Landing page
def landing_page():
    """Main landing page for the application"""
    st.markdown("""<h1 style = "font-family : Gabriola;text-align:center">EmpathyPulse: Employee Sentiment Analysis</h1""", unsafe_allow_html=True)
    
    # Logo or branding
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 class="glow-text" style ="font-family : Gabriola">❤️ EmpathyPulse</h1>
        <p style="font-size: 1.2em;">Understand your team's emotional well-being</p>
    </div>
    """, unsafe_allow_html=True)
    
    # App description
    st.markdown("""
    EmpathyPulse is an innovative platform that helps organizations understand and improve employee well-being and satisfaction. 
    Our advanced sentiment analysis provides real-time insights into your team's emotional state and identifies areas for improvement.
    
    **Key Features:**
    - Anonymous feedback options for honest communication
    - Sentiment and emotion analysis powered by AI
    - Department-specific trends and insights
    - Interactive dashboards for HR and management
    """)
    
    # Login/Signup columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="border: 1px solid #ffffff; border-radius: 10px; padding: 20px; text-align: center;">
            <h3>Employees</h3>
            <p>Share your feedback and track your workplace experience.</p>
        </div>
        """, unsafe_allow_html=True)
        
        employee_login = st.button("Employee Login", key="emp_login_btn")
        employee_signup = st.button("New Employee? Sign Up", key="emp_signup_btn")
        
        if employee_login:
            st.session_state.page = "login"
            st.rerun()
        
        if employee_signup:
            st.session_state.page = "signup"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="border: 1px solid #ffffff; border-radius: 10px; padding: 20px; text-align: center;">
            <h3>HR & Management</h3>
            <p>Analyze sentiment trends and improve workplace satisfaction.</p>
        </div>
        """, unsafe_allow_html=True)
        
        admin_login = st.button("Admin Login", key="admin_login_btn")
        
        if admin_login:
            if admin_exists():
                st.session_state.page = "admin_login"
            else:
                st.session_state.page = "admin_setup"
            st.rerun()

# Main function
def main():
    """Main application entry point"""
    # Always check for reset_token in query params and force reset_password page if present
    query_params = st.query_params
    token = query_params.get("reset_token", "")
    if isinstance(token, list):
        token = token[0] if token else ""
    if token:
        st.session_state["reset_token"] = token
        reset_password()
        return  # Do not execute any other routing or sidebar code
    
    if "page" not in st.session_state:
        st.session_state.page = "landing"
    
    # Check if admin exists, if not, redirect to admin setup
    if not admin_exists() and st.session_state.page == "landing":
        st.session_state.page = "admin_setup"
    
    # Route to appropriate page based on session state
    if st.session_state.page == "landing":
        landing_page()
    elif st.session_state.page == "login":
        login()
    elif st.session_state.page == "signup":
        signup()
    elif st.session_state.page == "employee_dashboard":
        employee_dashboard()
    elif st.session_state.page == "admin_login":
        admin_login()
    elif st.session_state.page == "admin_setup":
        setup_admin()
    elif st.session_state.page == "admin_dashboard":
        admin_dashboard()
    elif st.session_state.page == "forgot_password":
        forgot_password()
    elif st.session_state.page == "reset_password":
        reset_password()
    elif st.session_state.page == "admin_export":
        admin_export_page()
    elif st.session_state.page == "admin_delete_employee":
        admin_delete_employee_page()
    elif st.session_state.page == "admin_add_employee":
        admin_add_employee_page()

    
    # Navigation in sidebar
    with st.sidebar:
        st.header("Navigation")
        
        if st.session_state.get("role") == "employee":
            st.markdown(
            f"<div style='font-size:20px; color:red; font-family:Gabriola, cursive; font-weight:bold; margin-bottom:20px;'>Logged in as:  {st.session_state.employee_name}</div>",
            unsafe_allow_html=True)

            
            if st.button("Dashboard", key="nav_emp_dash"):
                st.session_state.page = "employee_dashboard"
                st.rerun()
            
            if st.button("Logout", key="nav_emp_logout"):
                logout()
        
        elif st.session_state.get("role") == "admin":
            st.markdown(
    f"<div style='font-size:20px; color:red; font-family:Gabriola, cursive; font-weight:bold; margin-bottom:20px;'>Logged in as:  Admin {st.session_state.admin_id}</div>",
    unsafe_allow_html=True)
            if st.button("Home", key="nav_admin_home"):
                st.session_state.page = "landing"
                st.rerun()
            if st.button("Dashboard", key="nav_admin_dash"):
                st.session_state.page = "admin_dashboard"
                st.rerun()
            if st.button("Add Employee", key="nav_admin_add_employee"):
                st.session_state.page = "admin_add_employee"
                st.rerun()
            if st.button("Delete Employee", key="nav_admin_delete_employee"):
                st.session_state.page = "admin_delete_employee"
                st.rerun()
            if st.button("Data Export", key="nav_admin_export"):
                st.session_state.page = "admin_export"
                st.rerun()
            if st.button("Admin Logout", key="nav_admin_logout"):
                logout()
        else:
            if st.button("Home", key="nav_home"):
                st.session_state.page = "landing"
                st.rerun()
            
            if st.button("Employee Login", key="nav_emp_login"):
                st.session_state.page = "login"
                st.rerun()
            
            if st.button("Employee Signup", key="nav_emp_signup"):
                st.session_state.page = "signup"
                st.rerun()
            
            if st.button("Admin Login", key="nav_admin_login"):
                if admin_exists():
                    st.session_state.page = "admin_login"
                else:
                    st.session_state.page = "admin_setup"
                st.rerun()
            
        
        # Add app info
        st.markdown("---")
        st.markdown("### About EmpathyPulse")
        #st.write("Admins:", github_store.get_admins())
        st.markdown("Version 1.0.0")
        st.markdown("© 2025 EmpathyPulse")

    #st.write("Admin Exists:", admin_exists())

def admin_export_page():
    """Admin data export page."""
    st.markdown("""<h1 class="glow-text" style = 'color:red;font-family:gabriola;font-size:50px;text-align:center;'>HR Dashboard - Employee Sentiment Monitoring</h1>""", unsafe_allow_html=True)
    st.markdown("""<h6 style = 'font-family:gabriola;font-size:30px'>Export Data</h6>""", unsafe_allow_html=True)

    export_type = st.radio("Select data to export", ["Employee Feedback", "Employee Directory", "Department Summary"])

    # Button label changes based on selected export
    button_label = f"Download {export_type} CSV"

    if st.button(button_label):
        if export_type == "Employee Feedback":
            data = github_store.get_feedback()
        elif export_type == "Employee Directory":
            data = github_store.get_employees()
        elif export_type == "Department Summary":
            # Summarize department stats
            feedback = github_store.get_feedback()
            df = pd.DataFrame(feedback)
            if df.empty:
                st.warning("No feedback data available for summary.")
                return
            summary = df.groupby("dept")[["work_satisfaction", "team_satisfaction", "management_satisfaction"]].mean().reset_index()
            summary.columns = ["Department", "Avg Work Satisfaction", "Avg Team Collaboration", "Avg Management Support"]
            data = summary.to_dict(orient="records")

        if data:
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(label=button_label, data=csv, file_name=f"{export_type.replace(' ', '_')}.csv", mime="text/csv")
        else:
            st.warning("No data available to export.")


def send_to_hr_dashboard(alert_info):
    """Display alert in the HR dashboard UI using Streamlit."""
    with st.container():
        st.error(f"🚨 {alert_info['title']}")
        st.markdown(alert_info['message'])


def notify_admin_if_priority_negative(feedback_data, admin_notifier, threshold=0.7):
    """
    Notify HR admin if an employee gives a negative sentiment review with high priority.
    Marks feedback with 'alert_shown': True after notification.
    """
    if feedback_data.get('sentiment', '').lower() != 'negative':
        return

    if feedback_data.get('alert_shown') or feedback_data.get('status') == 'complete':
        return

    base_priority = feedback_data.get('sentiment_confidence', 0.5)

    department_weights = {
        "HR": 0.1,
        "Engineering": 0.4,
        "Sales": 0.3,
        "Support": 0.2,
        "Marketing": 0.3,
        "Finance": 0.2,
        "Operations": 0.2,
        "Research": 0.3,
    }

    dept_weight = department_weights.get(feedback_data.get('dept', ''), 0.2)
    priority_score = base_priority + dept_weight

    if priority_score >= threshold:
        emp_id = feedback_data.get('emp_id')
        name = "Anonymous"
        if emp_id:
            employee = github_store.get_employee(emp_id)
            name = employee.get('name', emp_id) if employee else emp_id

        # Show alert with dismiss option
        with st.container():
            st.error(f"🚨 High Priority Alert: {name}")
            st.markdown(f"""
            **{name}** from **{feedback_data.get('dept', 'Unknown')}** has shown **negative sentiment**.

            **Priority Score:** {priority_score:.2f}
            """)

            if st.button(f"Dismiss Alert (ID: {feedback_data.get('id')})", key=f"dismiss_{feedback_data.get('id')}"):
                github_store.update_feedback(feedback_data.get('id'), {"alert_shown": True})
                st.success("Alert dismissed.")
                st.rerun()


# Run the application
if __name__ == "__main__":
    main()