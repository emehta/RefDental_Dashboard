import streamlit as st
import pandas as pd


# Set page configuration
st.set_page_config(
    page_title="Healthcare Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add a title to the app
st.title("Healthcare Analytics Dashboard")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('data/dental_healthcare_sample.csv')

try:
    # Load the data
    df = load_data()
    
    # Display a success message
    st.success("Data loaded successfully!")

     # Main page instructions
    st.markdown("""
    ## Welcome, to the Dental Analytics Dashboard
    
    Please use the sidebar (left) to navigate to different dashboards:
    
    - **Dashboard 1**: Patient Demographics & Appointment Analysis
    - **Dashboard 2**: Operations & Staff Anlysis
    - **Dashboard 3**: Finance, Sales & Revenue Analysis
    - **Dashboard 4**: ----
    
    Each dashboard provides different insights into your healthcare data.
    """)
    
    # Display sample data
    st.subheader("Sample Data: ")
    st.dataframe(df.head())
    
    # Display basic statistics
    st.subheader("Data Sample For Debugging")
    st.write(f"Total Records: {len(df)}")
    st.write(f"Columns: {', '.join(df.columns)}")
    

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Please make sure the data file exists at 'data/healthcare_data.csv'")
