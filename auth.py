import streamlit as st
import database

def authenticate_user():
    """Handle user authentication"""
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_id = None
    
    # Show login form if not authenticated
    if not st.session_state.authenticated:
        st.sidebar.title("User Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        
        if st.sidebar.button("Login"):
            user = database.get_user(username)
            if user and user[1] == password:  # Simple password check
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.user_id = user[0]
                st.sidebar.success("Login successful!")
                st.rerun()  # FIXED: Changed to st.rerun()
            else:
                st.sidebar.error("Invalid credentials")
        
        # Registration form
        with st.sidebar.expander("Register New Account"):
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            
            if st.button("Create Account"):
                if new_user and new_pass:
                    user_id = database.add_user(new_user, new_pass)
                    if user_id:
                        st.success("Account created! Please login")
                    else:
                        st.error("Username already exists")
                else:
                    st.warning("Username and password required")
        
        return False
    
    # Show logout button if authenticated
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.rerun()  # FIXED: Changed to st.rerun()
    
    return True