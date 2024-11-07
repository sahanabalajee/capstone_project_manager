import streamlit as st
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*experimental_set_query_params.*")
from streamlit_option_menu import option_menu
import pandas as pd
# Navbar for page navigation
def logout():
    # Set the session variables to simulate a logout
    st.session_state.is_logged_in = False
    st.session_state.user_role = None
    st.session_state.user_id = None
    st.session_state.page_reload = True 
    
def navbar():
    selected = option_menu(
        menu_title=None,  # Title of the menu
        options=["Map Teams to Mentors", "User Management", "View Mentor Feedback", "View Student Feedback & Marks","Visualise Student Marks"],  # Menu options
        icons=["person-plus", "people", "eye", "book",'graph'],  # Icons for each option (optional)
        menu_icon="cast",  # Icon for the entire menu
        default_index=0,  # Default selected item
        orientation="horizontal",  # Horizontal navbar
        styles={
            #"container": {"padding": "0!important", "background-color": "#2A2A2A"},
            "icon": {"color": "white", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "0px",
                "color": "white",
            },
            "nav-link-selected": {"background-color": "#4CAF50", "color": "white"},
        }
    )

    # Update session state based on the selected menu option
    if selected == "Map Teams to Mentors":
        st.session_state.page = "map_teams"
    elif selected == "User Management":
        st.session_state.page = "user_management"
    elif selected == "View Mentor Feedback":
        st.session_state.page = "view_mentor_feedback"
    elif selected == "View Student Feedback & Marks":
        st.session_state.page = "view_student_feedback_marks"
    elif selected == "Visualise Student Marks":
        st.session_state.page = "visualize_student_marks"

# Main function for handling navigation and rendering pages

def map_teams_to_mentors(mycursor, db):
    st.header("Map Teams Without Mentors to Available Faculties")

    # Fetch teams without mentors and mentors with availability
    mycursor.execute("SELECT * FROM Team WHERE Mentor_ID IS NULL")
    teams = mycursor.fetchall()

    mycursor.execute("SELECT * FROM Mentors WHERE Availability > 0")
    mentors = mycursor.fetchall()

    # Initialize session states for selected team and mentor
    if "selected_team" not in st.session_state:
        st.session_state.selected_team = None
    if "selected_mentor" not in st.session_state:
        st.session_state.selected_mentor = None

    # Step 1: Team Selection
    if teams:
        st.subheader("Step 1: Select a Team without a Mentor")
        team_options = {f"{team['team_id']} - {team['area_of_interest']}": team['team_id'] for team in teams}
        selected_team_option = st.selectbox("Choose a Team", options=list(team_options.keys()))

        if selected_team_option:
            st.session_state.selected_team = team_options[selected_team_option]
            st.success(f"Selected Team ID: {st.session_state.selected_team}")
    else:
        st.info("No teams available for mapping.")

    # Step 2: Mentor Selection
    if mentors and st.session_state.selected_team:
        st.subheader("Step 2: Select an Available Mentor")
        mentor_options = {f"{mentor['mentor_id']} - {mentor['name']} ({mentor['expertise']})": mentor['mentor_id'] for mentor in mentors}
        selected_mentor_option = st.selectbox("Choose a Mentor", options=list(mentor_options.keys()))

        if selected_mentor_option:
            st.session_state.selected_mentor = mentor_options[selected_mentor_option]
            st.success(f"Selected Mentor ID: {st.session_state.selected_mentor}")
    elif not st.session_state.selected_team:
        st.info("Please select a team first.")
    else:
        st.info("No mentors available for mapping.")

    # Step 3: Assignment Button
    if st.session_state.selected_team and st.session_state.selected_mentor:
        if st.button("Assign Mentor"):
            team_id = st.session_state.selected_team
            mentor_id = st.session_state.selected_mentor

            # Perform the assignment; the trigger will handle availability decrement
            mycursor.execute("UPDATE Team SET Mentor_ID = %s WHERE Team_ID = %s", (mentor_id, team_id))
            db.commit()

            st.success(f"Mentor {mentor_id} successfully assigned to Team {team_id}")

            # Reset selections
            st.session_state.selected_team = None
            st.session_state.selected_mentor = None

        
def user_management(mycursor,db):
    st.header("User Management")
    action = st.selectbox("Choose an Action", ["Add User", "Delete User"])
    if action == "Add User":
        add_user(mycursor,db)
    elif action == "Delete User":
        delete_user(mycursor,db)

def add_user(mycursor,db):
    role = st.selectbox("Role", ["Student", "Mentor","Admin"])
    name = st.text_input("Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    password = st.text_input("Password",type = "password")
    if role == "Student":
        srn = st.text_input("SRN")
        age = st.number_input("Age", min_value=1)
        if st.button("Add Student"):
            # Insert student into Users table
            mycursor.execute(
                "INSERT INTO Users (Name, Email, Password, Role) VALUES (%s, %s, %s, 'Student')",
                (name, email, password)
            )
            
            # Get the user_id of the newly added student
            student_id = mycursor.lastrowid

            # Insert the student_id and additional details into the Students table
            try:
                mycursor.execute(
                    "INSERT INTO Students (Student_ID, Name, Email, phone, SRN, Age) VALUES (%s, %s, %s,%s, %s, %s )",
                    (student_id,name,email,phone, srn, age)
                )
                
                # Commit the transaction
                db.commit()

                st.success("Student added successfully")
            except:
                st.error("Unable to add student")
    elif role == "Mentor":
        expertise = st.text_input("Expertise")
        availability = st.number_input("Availability", max_value=3,min_value=0)
        if st.button("Add Mentor"):
            mycursor.execute("INSERT INTO Users (Name, Email, Password, Role) VALUES (%s, %s, %s, 'Mentor')", (name, email, password))
            db.commit()
            mentor_id = mycursor.lastrowid
            try:
                mycursor.execute(
                "INSERT INTO Mentors (mentor_id, name, email, phone, expertise,availability) VALUES (%s, %s, %s,%s, %s, %s )",
                (mentor_id,name,email,phone, expertise, availability)
            )
                db.commit()
                st.success("Mentor added successfully")
            except:
                st.error("Unable to add Mentor")

            
            # Commit the transaction
            
def delete_user(mycursor,db):
    user_id = st.text_input("Enter User ID to delete")
    if st.button("Delete User"):
        mycursor.execute( "SELECT * FROM USERS WHERE User_ID = %s", (user_id,))
        record = mycursor.fetchone()
        print(record)
        mycursor.execute("DELETE FROM Users WHERE User_ID = %s", (user_id,))
        db.commit()
        if record:
            st.success(f"User - { user_id} - {record["name"]} - {record["role"]} deleted.")

# Functionality for viewing mentor feedback
def view_mentor_feedback(mycursor,db):
    st.header("View Feedback for Mentors")
    mycursor.execute("SELECT * FROM Feedback WHERE Receiver_ID IN (SELECT Mentor_ID FROM Mentors)")
    feedbacks = mycursor.fetchall()
    for feedback in feedbacks:
        st.markdown(f" ### Mentor ID: {feedback['receiver_id']}")
        st.markdown(f" ##### Score: {feedback['score']}")
        st.markdown(f"##### Message: {feedback['message']}")

# Functionality for viewing student feedback and marks
def view_student_feedback_and_marks(mycursor,db):
    st.header("View Feedback and Marks of Students")
    mycursor.execute("SELECT * FROM Feedback WHERE Receiver_ID IN (SELECT Student_ID FROM Students)")
    feedbacks = mycursor.fetchall()
    for feedback in feedbacks:
        st.markdown(f" ### Student ID: {feedback['receiver_id']}")
        st.markdown(f" #####  Score: {feedback['score']}")
        st.markdown(f"##### Message: {feedback['message']}")
    mycursor.execute("SELECT * FROM Students")
    students = mycursor.fetchall()
    for student in students:
        st.markdown(f" #### Student: {student['name']}")
        st.markdown(f" ##### Marks: {student['m1']}, {student['m2']}, {student['m3']}, {student['m4']}")
def visualize_student_marks(mycursor):
    st.header("Student Marks Overview")

    # Fetch student marks from the database
    mycursor.execute("SELECT student_id,name, m1, m2, m3, m4 FROM Students")
    students_data = mycursor.fetchall()

    # Convert the data to a DataFrame
    marks_df = pd.DataFrame(students_data)

    if not marks_df.empty:
        marks_df.set_index("student_id", inplace=True)  # Set student names as index for easier plotting

        # Display bar chart for each student
        for mark in ["m1", "m2", "m3", "m4"]:
            st.subheader(f"Marks for {mark.upper()}")
            st.bar_chart(marks_df[mark], height=300, width=700)
    else:
        st.info("No student marks data available.")

# Main function for handling navigation and rendering pages
def admin_dashboard_page(mycursor, db):
    if "page" not in st.session_state:
        st.session_state.page = "map_teams"
    
    navbar()
    
    # Determine which page to display based on session state
    page = st.session_state.page

    if page == "map_teams":
        map_teams_to_mentors(mycursor, db)
    elif page == "user_management":
        user_management(mycursor, db)
    elif page == "view_mentor_feedback":
        view_mentor_feedback(mycursor, db)
    elif page == "view_student_feedback_marks":
        view_student_feedback_and_marks(mycursor, db)
    elif page == "visualize_student_marks":
        visualize_student_marks(mycursor)
    col1, col2,col3,col4,col5,col6,col7,col8,col9 = st.columns([1, 2,3,4,5,6,7,8,9])

    # Place the button in the second column
    with col9:
        if st.button("Logout"):
            logout()
            st.button("Click here to log out from the session")

