import mysql.connector
import streamlit as st
from admin_dashboard import admin_dashboard_page
import warnings
from mentor_dashboard import mentor_dashboard_page
from student_dashboard import student_dashboard_page
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*experimental_set_query_params.*")
# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="******",
    database="capstone_project"
)
mycursor = db.cursor(dictionary=True)

# Initialize session state
if "is_logged_in" not in st.session_state:
    st.session_state.is_logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

def login():
    st.title("Login Portal")
    role = st.selectbox("Select your role", ["Student", "Mentor", "Admin"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user_id = check_login(mycursor, email, password, role)
        if user_id:
            st.success("Login successful!")
            st.session_state.is_logged_in = True
            st.session_state.user_role = role
            st.session_state.user_id = user_id
            st.session_state.page_reload = True 
            print(st.session_state.user_id)
            st.button("Continue to Dashboard") # Refresh the page to display the dashboard
        else:
            st.error("Invalid email or password. Please try again.")

def check_login(mycursor, email, password, role):
    query = "SELECT user_id, role FROM USERS WHERE email = %s AND password = %s AND role = %s"
    values = (email, password, role)
    mycursor.execute(query, values)
    record = mycursor.fetchone()
    
    # If a matching record is found, return the user_id
    if record:
        return record["user_id"]
    return None

def main():
    if "page_reload" in st.session_state and st.session_state.page_reload:
        st.session_state.page_reload = False
          # Clears query params and refreshes

    if not st.session_state.is_logged_in:
        login()
    else:
        # Display dashboard based on user role
        #st.write(f"Welcome to the {st.session_state.user_role} dashboard!")
        if st.session_state.user_role == "Admin":
            admin_dashboard_page(mycursor, db)
        if st.session_state.user_role == "Mentor":
            print("in mentor")
            mentor_dashboard_page(mycursor, db,st.session_state.user_id)
        if st.session_state.user_role == "Student":
            student_dashboard_page(mycursor, db,st.session_state.user_id)


if __name__ == "__main__":
    main()
