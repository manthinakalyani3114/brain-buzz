import streamlit as st
import json
import re
import time
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Quiz Application", layout="wide")

# ---------- LOAD USERS & SUBMISSIONS ----------
def load_users():
    try:
        with open("users.json","r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open("users.json","w") as f:
        json.dump(users,f)

def load_submissions():
    try:
        with open("submissions.json","r") as f:
            return json.load(f)
    except:
        return []

def save_submissions(data):
    with open("submissions.json","w") as f:
        json.dump(data,f)

users = load_users()
submissions = load_submissions()

# ---------- SESSION ----------
if "page" not in st.session_state:
    st.session_state.page="register"
if "user_email" not in st.session_state:
    st.session_state.user_email=""
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers={}
if "current_question" not in st.session_state:
    st.session_state.current_question=0
if "start_time" not in st.session_state:
    st.session_state.start_time=None

# ---------- VALIDATION ----------
def valid_email(email):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$",email)

def valid_password(password):
    return re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&]).+$',password)

# ---------- QUIZ ----------
quiz_questions=[
    {"question":"Capital of India?","options":["Mumbai","Delhi","Kolkata","Chennai"]},
    {"question":"ML language?","options":["Python","HTML","CSS","Excel"]},
    {"question":"Streamlit creator?","options":["Google","Streamlit Inc.","Microsoft","Meta"]}
]

correct_answers={
    0:"Delhi",
    1:"Python",
    2:"Streamlit Inc."
}

def calculate_score(ans):
    score=0
    for i,a in ans.items():
        if correct_answers[i]==a:
            score+=1
    return score

# ---------- SIDEBAR ----------
def show_sidebar():
    if st.session_state.user_email:
        st.sidebar.title("Profile")
        uname=users.get(st.session_state.user_email,{}).get("username","User")
        st.sidebar.write(uname)

        st.sidebar.markdown("---")
        st.sidebar.title("Leaderboard")

        leaderboard={}
        for sub in submissions:
            email=sub.get("email")
            answers={0:sub.get("q1"),1:sub.get("q2"),2:sub.get("q3")}
            score=calculate_score(answers)

            if email:
                leaderboard[email]=max(leaderboard.get(email,0),score)

        sorted_lb=sorted(leaderboard.items(),key=lambda x:x[1],reverse=True)

        for i,(email,score) in enumerate(sorted_lb[:5]):
            uname=users.get(email,{}).get("username","User")

            medal="🏅"
            if i==0: medal="🥇"
            elif i==1: medal="🥈"
            elif i==2: medal="🥉"

            st.sidebar.write(f"{medal} {uname} - {score}")

show_sidebar()

# ---------- CENTER ----------
col1,col2,col3=st.columns([1,2,1])
with col2:

    # REGISTER
    if st.session_state.page=="register":
        st.title("Register")
        email=st.text_input("Email")
        username=st.text_input("Username")
        password=st.text_input("Password",type="password")

        if st.button("Register"):
            if not email or not username or not password:
                st.error("Fill all fields")
            elif not valid_email(email):
                st.error("Invalid email")
            elif not valid_password(password):
                st.error("Weak password")
            elif email in users:
                st.warning("User exists")
            else:
                users[email]={"username":username,"password":password}
                save_users(users)
                st.success("Registered")

        if st.button("Go to Login"):
            st.session_state.page="login"

    # LOGIN
    elif st.session_state.page=="login":
        st.title("Login")
        email=st.text_input("Email")
        password=st.text_input("Password",type="password")

        if st.button("Login"):
            if email in users and users[email]["password"]==password:
                st.session_state.user_email=email
                st.session_state.page="ready"   # ← intermediate page
                st.session_state.current_question=0
                st.session_state.quiz_answers={}
                st.session_state.start_time=None
                st.success("Login success")
            else:
                st.error("Invalid credentials")

        if st.button("Go to Register"):
            st.session_state.page="register"

    # READY PAGE - after login
    elif st.session_state.page=="ready":
        st.title("Welcome, " + users.get(st.session_state.user_email,{}).get("username","User"))
        st.write("Press the button below to start the quiz!")

        if st.button("Start Quiz"):
            st.session_state.page="quiz"
            st.session_state.current_question=0
            st.session_state.quiz_answers={}
            st.session_state.start_time=time.time()

       
    # QUIZ
    elif st.session_state.page=="quiz":

        st_autorefresh(interval=1000,key="timer")

        q=st.session_state.current_question

        if q>=len(quiz_questions):
            st.session_state.page="description"
            st.session_state.start_time=None

        else:
            data=quiz_questions[q]
            st.title(f"Q{q+1}")
            ans=st.radio(data["question"],data["options"])

            if st.session_state.start_time is None:
                st.session_state.start_time=time.time()

            rem=20-int(time.time()-st.session_state.start_time)
            st.write(f"Time: {rem}")

            if rem<=0:
                st.session_state.quiz_answers[q]=ans
                st.session_state.current_question+=1
                st.session_state.start_time=time.time()

            if st.button("Next"):
                st.session_state.quiz_answers[q]=ans
                st.session_state.current_question+=1
                st.session_state.start_time=time.time()

            

    # DESCRIPTION
    elif st.session_state.page=="description":

        st_autorefresh(interval=1000,key="desc")

        st.title("Image Description")
        st.image("iphone_blue.jpeg",width=200)

        desc=st.text_area("Describe",max_chars=200)

        if st.session_state.start_time is None:
            st.session_state.start_time=time.time()

        rem=20-int(time.time()-st.session_state.start_time)
        st.write(f"Time: {rem}")

        def submit():
            submissions.append({
                "email":st.session_state.user_email,
                "q1":st.session_state.quiz_answers.get(0),
                "q2":st.session_state.quiz_answers.get(1),
                "q3":st.session_state.quiz_answers.get(2),
                "description":desc
            })
            save_submissions(submissions)

        if rem<=0:
            submit()
            st.session_state.page="result"

        if st.button("Submit"):
            submit()
            st.session_state.page="result"

    # RESULT
    elif st.session_state.page=="result":

        st.title("🎉 Result")

        uname=users.get(st.session_state.user_email,{}).get("username","User")
        score=calculate_score(st.session_state.quiz_answers)

        st.success(f"{uname}")
        st.success(f"Score: {score}/3")

        for i,q in enumerate(quiz_questions):
            user=st.session_state.quiz_answers.get(i)
            correct=correct_answers[i]

            if user==correct:
                st.write(f"✅ {q['question']} - {user}")
            else:
                st.write(f"❌ {q['question']} - Your:{user} | Correct:{correct}")

        # Chart
        if submissions:
            scores=[]
            for sub in submissions:
                ans={0:sub.get("q1"),1:sub.get("q2"),2:sub.get("q3")}
                scores.append(calculate_score(ans))

            df=pd.DataFrame({"Scores":scores})
            st.bar_chart(df)

        if st.button("Reattempt"):
            st.session_state.page="quiz"
            st.session_state.current_question=0
            st.session_state.quiz_answers={}
            st.session_state.start_time=None

        if st.button("Logout"):
            st.session_state.page="login"
            st.session_state.user_email=""