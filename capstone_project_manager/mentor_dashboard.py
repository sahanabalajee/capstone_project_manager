import streamlit as st
from streamlit_option_menu import option_menu
def logout():
    # Set the session variables to simulate a logout
    st.session_state.is_logged_in = False
    st.session_state.user_role = None
    st.session_state.user_id = None
    st.session_state.page_reload = True 
# Mentor Dashboard Navbar
def mentor_navbar():
    # Define the navbar using option_menu
    selected = option_menu(
        menu_title=None,  # No title for the navbar
        options=["Allocate Tasks", "Provide Feedback", "Edit Marks", "View Feedback"],
        icons=["clipboard-check", "chat-dots", "pencil", "eye"],  # Icons for each option
        menu_icon="cast",  # Menu icon for the navbar
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
        },
    )
    
    return selected


# Function to display and allocate tasks to teams
import streamlit as st

def allocate_tasks(mycursor, db, mentor_id):
    st.header("Allocate Tasks to Teams")
    
    # Fetch teams mentored by the specific mentor
    mycursor.execute("""
        SELECT team_id 
        FROM Team 
        WHERE mentor_id = %s
    """, (mentor_id,))
    teams = mycursor.fetchall()
    
    if teams:
        for team in teams:
            team_id = team['team_id']
            st.subheader(f"Team {team_id}")
            
            # Display students in the team
            mycursor.execute("""
                SELECT s.name, s.srn 
                FROM Team_Members tm
                INNER JOIN students s ON tm.student_id = s.student_id
                WHERE tm.Team_ID = %s
            """, (team_id,))
            students = mycursor.fetchall()
            for student in students:
                st.write(f"Student: {student['name']} (ID: {student['srn']})")
            
            # Allocate task to the team
            task_title = st.text_area(f"Task for Team {team_id}")
            task_description = st.text_area(f"Task Description")
            if st.button(f"Assign Task to Team {team_id}"):
                mycursor.callproc('AssignTaskToTeam', [team_id, task_title, task_description])
                db.commit()
                st.success(f"Task assigned to Team {team_id}")
            
            # Display and edit task status if tasks exist
            mycursor.execute("""
                SELECT Task_ID, Description, Status 
                FROM Task 
                WHERE Team_ID = %s
            """, (team_id,))
            tasks = mycursor.fetchall()
            for task in tasks:
                task_id = task['Task_ID']
                st.write(f"Task: {task['Description']}, Status: {task['Status']}")
                status = st.selectbox(f"Update Status for Task {task_id}", ["Pending", "Completed"], index=0 if task['Status'] == "Pending" else 1)
                if st.button(f"Update Status for Task {task_id}"):
                    mycursor.execute("""
                        UPDATE Task 
                        SET Status = %s 
                        WHERE Task_ID = %s
                    """, (status, task_id))
                    db.commit()
                    st.success(f"Task {task_id} status updated to {status}")
    else:
        st.info("No teams available.")



# Function to provide feedback for students
def provide_feedback(mycursor, db, mentor_id):
    st.header("Provide Feedback for Students")
    mycursor.execute(f"""
        SELECT team_id 
        FROM Team 
        WHERE mentor_id = {mentor_id}
    """)
    teams = mycursor.fetchall()
    
    if teams:
        for team in teams:
            team_id = team['team_id']
            st.subheader(f"Team {team_id}")
            
            # Display students in the team
            mycursor.execute("""
                SELECT s.student_id, s.name, s.srn 
                FROM Team_Members tm
                INNER JOIN students s ON tm.student_id = s.student_id
                WHERE tm.Team_ID = %s
            """, (team_id,))
            students = mycursor.fetchall()
            for student in students:
                st.write(f"Student: {student['name']} (ID: {student['srn']})")
                feedback = st.text_area(f"Feedback for {student['name']}")
                score = st.number_input("Score", min_value=1, max_value=10, key=f"{student['srn']}")
                if st.button(f"Submit Feedback for {student['name']}"):
                    mycursor.execute("""
                        INSERT INTO Feedback (Sender_ID, Receiver_ID, Score, Message) 
                        VALUES (%s, %s, %s, %s)
                    """, (mentor_id, student['student_id'], score, feedback))
                    db.commit()
                    st.success(f"Feedback for {student['name']} submitted")


# Function to edit marks of students
def edit_marks(mycursor, db, mentor_id):
    st.header("Edit Students' Marks")
    mycursor.execute(f"""
        SELECT team_id 
        FROM Team 
        WHERE mentor_id = {mentor_id}
    """)
    teams = mycursor.fetchall()
    
    if teams:
        for team in teams:
            team_id = team['team_id']
            st.subheader(f"Team {team_id}")
            
            # Display students in the team
            mycursor.execute("""
                SELECT s.student_id, s.name, s.srn, s.m1, s.m2, s.m3, s.m4 
                FROM Team_Members tm
                INNER JOIN students s ON tm.student_id = s.student_id
                WHERE tm.Team_ID = %s
            """, (team_id,))
            students = mycursor.fetchall()
            for student in students:
                student_id = student['student_id']
                st.write(f"Student: {student['name']} (ID: {student['srn']})")
                new_m1 = st.number_input(f"Edit Marks for {student['name']} (M1)", value=student['m1'], min_value=0, max_value=100)
                new_m2 = st.number_input(f"Edit Marks for {student['name']} (M2)", value=student['m2'], min_value=0, max_value=100)
                new_m3 = st.number_input(f"Edit Marks for {student['name']} (M3)", value=student['m3'], min_value=0, max_value=100)
                new_m4 = st.number_input(f"Edit Marks for {student['name']} (M4)", value=student['m4'], min_value=0, max_value=100)
                
                if st.button(f"Update Marks for {student['name']}"):
                    mycursor.execute("""
                        UPDATE students 
                        SET m1 = %s, m2 = %s, m3 = %s, m4 = %s 
                        WHERE student_id = %s
                    """, (new_m1, new_m2, new_m3, new_m4, student_id))
                    db.commit()
                    st.success(f"Marks updated for {student['name']}")


# Function for mentors to view feedback received from students
# Function for mentors to view feedback received from students
def view_feedback(mycursor, mentor_id):
    st.header("View Feedback from Students")
    
    # Query to retrieve feedback messages, individual scores, and calculate the average score using AVG and GROUP BY
    mycursor.execute("""
        SELECT f.Message, f.Score, s.name AS Student_Name 
        FROM Feedback f
        INNER JOIN students s ON f.Sender_ID = s.student_id
        WHERE f.Receiver_ID = %s
    """, (mentor_id,))
    
    feedbacks = mycursor.fetchall()
    mycursor.execute("""
        SELECT AVG(Score) AS avg_score 
        FROM Feedback f
        WHERE f.Receiver_ID = %s
        GROUP BY Receiver_ID
    """, (mentor_id,))
    average_score = mycursor.fetchone()
    if feedbacks:
        # Display each feedback message and individual score
        for feedback in feedbacks:
            st.markdown(f"#### Student: {feedback['Student_Name']}")
            st.markdown(f" ###### Feedback: {feedback['Message']}")
            st.markdown(f" ###### Score: {feedback['Score']}/10")
        
        # Display the calculated average score
        
        st.write(f"Average Score from Student Feedback: {average_score["avg_score"]}")
    else:
        st.info("No feedback available from students yet.")



# Main function for mentor dashboard
def mentor_dashboard_page(mycursor, db, mentor_id):
    if "page" not in st.session_state:
        st.session_state.page = "Allocate Tasks"
    
    selected_page = mentor_navbar()  # Get the selected navbar option
    
    # Render content based on selected page
    if selected_page == "Allocate Tasks":
        allocate_tasks(mycursor, db, mentor_id)
    elif selected_page == "Provide Feedback":
        provide_feedback(mycursor, db, mentor_id)
    elif selected_page == "Edit Marks":
        edit_marks(mycursor, db, mentor_id)
    elif selected_page == "View Feedback":
        view_feedback(mycursor, mentor_id)
    col1, col2,col3,col4,col5,col6,col7,col8,col9 = st.columns([1, 2,3,4,5,6,7,8,9])

    # Place the button in the second column
    with col9:
        if st.button("Logout"):
            logout()
            st.button("Click here to log out from the session")
