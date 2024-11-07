import streamlit as st
from streamlit_option_menu import option_menu
def logout():
    # Set the session variables to simulate a logout
    st.session_state.is_logged_in = False
    st.session_state.user_role = None
    st.session_state.user_id = None
    st.session_state.page_reload = True 
def student_navbar():
    selected = option_menu(
        menu_title=None,  # Title of the menu
        options=["Team Details", "Task Info", "Provide Feedback", "View Feedback"],  # Menu options
        icons=["info", "tasks", "chat-dots", "eye"],  # Icons for each option
        menu_icon="cast",  # Icon for the entire menu
        default_index=0,  # Default selected item
        orientation="horizontal",  # Horizontal navbar
        styles={
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
    if selected == "Team Details":
        st.session_state.page = "form_team"
    elif selected == "Task Info":
        st.session_state.page = "task_info"
    elif selected == "Provide Feedback":
        st.session_state.page = "provide_feedback"
    elif selected == "View Feedback":
        st.session_state.page = "view_feedback"


def form_team(mycursor, db, student_id):
    st.header("Team Details")
    
    # Check if the student is already in a team
    mycursor.execute("SELECT Team_ID FROM Team_Members WHERE Student_ID = %s", (student_id,))
    record = mycursor.fetchone()
    if record:
        mycursor.execute("""
        SELECT Students.name, Students.srn 
        FROM Team_Members 
        JOIN Students ON Team_Members.Student_ID = Students.Student_ID 
        WHERE Team_Members.Team_ID = %s
        """, (record["Team_ID"],))
        students = mycursor.fetchall()

        # Display team members
        st.write("Team members")
        for student in students:
            st.write(f"{student['name']} {student['srn']}")
        
        mycursor.execute("""
            SELECT Mentors.name 
            FROM Team
            JOIN Mentors ON Team.Mentor_ID = Mentors.Mentor_ID 
            WHERE Team.Team_ID = %s
        """, (record["Team_ID"],))
        mentor = mycursor.fetchone()

        # Display the mentor's name
        if mentor:
            st.write(f"Mentor: {mentor['name']}")
        else:
            st.write("No mentor assigned to this team.")

    else:
        # Select students not in any team
        mycursor.execute("""
            SELECT User_ID, Name FROM Users 
            WHERE Role = 'Student' AND User_ID NOT IN (SELECT Student_ID FROM Team_Members)
        """)
        available_students = mycursor.fetchall()
        
        # Form a team by selecting members
        selected_members = st.multiselect("Select team members", [student['Name'] for student in available_students],max_selections=4)
        area_of_interest = st.text_area("Type your area of interest")
        if st.button("Create Team"):
            # Create a new team and add selected members
            mycursor.execute("INSERT INTO Team (mentor_id,  area_of_interest) VALUES (NULL, %s)",(area_of_interest,))
            team_id = mycursor.lastrowid
            for member in selected_members:
                student_id = next(s['User_ID'] for s in available_students if s['Name'] == member)
                mycursor.execute("INSERT INTO Team_Members (Team_ID, Student_ID) VALUES (%s, %s)", (team_id, student_id))
            db.commit()
            st.success("Team created successfully!")

def task_info(mycursor, student_id):
    st.header("Task Information")
    
    # Fetch student's team ID
    mycursor.execute("SELECT Team_ID FROM Team_Members WHERE Student_ID = %s", (student_id,))
    team_id = mycursor.fetchone()
    
    if team_id:
        team_id = team_id['Team_ID']
        mycursor.execute("SELECT Title, Description, Status FROM task WHERE Team_ID = %s", (team_id,))
        tasks = mycursor.fetchall()
        for task in tasks:
            st.write(f"Title: {task['Title']}")
            st.write(f"Description: {task['Description']}")
            st.write(f"Status: {task['Status']}")
    else:
        st.info("You are not part of any team.")

def feedback_for_mentor(mycursor, db, student_id):
    st.header("Feedback for Mentor")
    
    # Get mentor ID for the student's team
    mycursor.execute("""
        SELECT Mentor_ID FROM Team
        WHERE Team_ID = (SELECT Team_ID FROM Team_Members WHERE Student_ID = %s)
    """, (student_id,))
    mentor_id = mycursor.fetchone()
    
    if mentor_id:
        mentor_id = mentor_id['Mentor_ID']
        mycursor.execute("SELECT name FROM Mentors WHERE Mentor_ID = %s", (mentor_id,))
        mentor_name = mycursor.fetchone()
        feedback_text = st.text_area(f"Enter feedback for your mentor Prof {mentor_name["name"]} ")
        score = st.number_input("Score", min_value=1, max_value=10)
        if st.button("Submit Feedback"):
            mycursor.execute("INSERT INTO Feedback (Sender_ID, Receiver_ID, Message,score) VALUES (%s, %s, %s,%s)", (student_id, mentor_id, feedback_text,score))
            db.commit()
            st.success("Feedback submitted successfully.")
    else:
        st.info("You do not have a mentor assigned yet.")

def view_feedback(mycursor, student_id):
    st.header("Feedback from Mentor")
    
    # Get the student's team and mentor ID
    mycursor.execute("""
        SELECT Mentor_ID FROM Team
        WHERE Team_ID = (SELECT Team_ID FROM Team_Members WHERE Student_ID = %s)
    """, (student_id,))
    mentor_id = mycursor.fetchone()
    mycursor.execute("""
        SELECT AVG(Score) AS avg_score 
        FROM Feedback f
        WHERE f.Receiver_ID = %s
        GROUP BY Receiver_ID
    """, (student_id,))
    average_score = mycursor.fetchone()
    
    if mentor_id:
        mentor_id = mentor_id['Mentor_ID']
        
        # Fetch feedback given by the mentor to the student
        mycursor.execute("""
            SELECT Message, Score FROM Feedback 
            WHERE Sender_ID = %s AND Receiver_ID = %s
        """, (mentor_id, student_id))
        feedbacks = mycursor.fetchall()
        
        if feedbacks:
            for feedback in feedbacks:
                st.write(f"Feedback: {feedback['Message']}")
                st.write(f"Score: {feedback['Score']}/10")
            st.write(f"Average Score from Student Feedback: {average_score["avg_score"]}")
        else:
            st.info("No feedback available from your mentor yet.")
    else:
        st.info("You do not have a mentor assigned yet.")

import streamlit as st

def student_dashboard_page(mycursor, db, student_id):
    if "page" not in st.session_state:
        st.session_state.page = "task_info"
        
    student_navbar()
    
    # Load the selected page
    page = st.session_state.page
    if page == "form_team":
        form_team(mycursor, db, student_id)
    elif page == "task_info":
        task_info(mycursor, student_id)
    elif page == "provide_feedback":
        feedback_for_mentor(mycursor, db, student_id)
    elif page == "view_feedback":
        view_feedback(mycursor, student_id)
    col1, col2,col3,col4,col5,col6,col7,col8,col9 = st.columns([1, 2,3,4,5,6,7,8,9])

    # Place the button in the second column
    with col9:
        if st.button("Logout"):
            logout()
            st.button("Click here to log out from the session")
