import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import calendar

st.set_page_config(page_title="Operations Dashboard", page_icon="⚙️", layout="wide")

st.title("Operations and Staff Insights")


@st.cache_data
def load_data():
    try:
        operations_data = pd.read_csv('data/Operations_Data.csv')
        equipment_data = pd.read_csv('data/Equipment_Usage_Data.csv')
        staff_data = pd.read_csv('data/Staff_Hours_Data.csv')
        patient_data = pd.read_csv('data/Pat_App_Data.csv')
        
        
        # Convert date columns - try multiple formats
        date_cols = ['Date']
        for df in [operations_data, equipment_data, staff_data]:
            for col in date_cols:
                if col in df.columns:
                    # Try to parse with format awareness
                    try:
                        df[col] = pd.to_datetime(df[col], format='%Y-%m-%d', errors='coerce')
                    except:
                        try:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                        except Exception as e:
                            st.error(f"Error parsing dates: {e}")
        
        # Convert patient data date columns with similar robustness
        patient_date_cols = ['Date_of_Service', 'Treatment_Plan_Creation_Date', 'Treatment_Plan_Completion_Date',
                           'Insurance_Claim_Submission_Date', 'Insurance_Claim_Payment_Date']
        for col in patient_date_cols:
            if col in patient_data.columns:
                try:
                    patient_data[col] = pd.to_datetime(patient_data[col], format='%Y-%m-%d', errors='coerce')
                except:
                    try:
                        patient_data[col] = pd.to_datetime(patient_data[col], errors='coerce')
                    except Exception as e:
                        st.error(f"Error parsing dates for {col}: {e}")
        
        
        # Add day name and month name
        for df in [operations_data, equipment_data, staff_data]:
            if 'Date' in df.columns:
                df['Day_Name'] = df['Date'].dt.day_name()
                df['Month_Name'] = df['Date'].dt.month_name()
        
        if 'Date_of_Service' in patient_data.columns:
            patient_data['Day_Name'] = patient_data['Date_of_Service'].dt.day_name()
            patient_data['Month_Name'] = patient_data['Date_of_Service'].dt.month_name()
        
        return operations_data, equipment_data, staff_data, patient_data
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None, None

operations_data, equipment_data, staff_data, patient_data = load_data()


if operations_data is not None and equipment_data is not None and staff_data is not None and patient_data is not None:
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date range filter
    min_date = min(operations_data['Date'].min(), equipment_data['Date'].min(), staff_data['Date'].min())
    max_date = max(operations_data['Date'].max(), equipment_data['Date'].max(), staff_data['Date'].max())
    
    start_date = st.sidebar.date_input("Start Date", min_date.date(), min_value=min_date.date(), max_value=max_date.date())
    end_date = st.sidebar.date_input("End Date", max_date.date(), min_value=min_date.date(), max_value=max_date.date())

    
    
    # Location filter
    locations = ['All'] + sorted(operations_data['Location_Name'].unique().tolist())
    selected_location = st.sidebar.selectbox("Select Location", locations)
    
    # Day of week filter
    day_options = ['All'] + list(calendar.day_name)
    selected_day = st.sidebar.selectbox("Day of Week", day_options)
    
    # Staff role filter
    staff_roles = ['All'] + sorted(staff_data['Staff_Role'].unique().tolist())
    selected_staff_role = st.sidebar.selectbox("Staff Role", staff_roles)
    
    # Apply filters to operations data
    filtered_operations = operations_data.copy()
    
    # Date filter
    filtered_operations = filtered_operations[(filtered_operations['Date'].dt.date >= start_date) & 
                                             (filtered_operations['Date'].dt.date <= end_date)]
    
    # Location filter
    if selected_location != 'All':
        filtered_operations = filtered_operations[filtered_operations['Location_Name'] == selected_location]
    
    # Day filter
    if selected_day != 'All':
        filtered_operations = filtered_operations[filtered_operations['Day_of_Week'] == selected_day]
    
    # Apply filters to equipment data
    filtered_equipment = equipment_data.copy()
    filtered_equipment = filtered_equipment[(filtered_equipment['Date'].dt.date >= start_date) & 
                                           (filtered_equipment['Date'].dt.date <= end_date)]
    
    if selected_location != 'All':
        filtered_equipment = filtered_equipment[filtered_equipment['Location_ID'].isin(
            filtered_operations['Location_ID'].unique())]
    
    # Apply filters to staff data
    filtered_staff = staff_data.copy()
    filtered_staff = filtered_staff[(filtered_staff['Date'].dt.date >= start_date) & 
                                   (filtered_staff['Date'].dt.date <= end_date)]
    
    if selected_location != 'All':
        filtered_staff = filtered_staff[filtered_staff['Location_ID'].isin(
            filtered_operations['Location_ID'].unique())]
    
    if selected_staff_role != 'All':
        filtered_staff = filtered_staff[filtered_staff['Staff_Role'] == selected_staff_role]
    
    # Apply filters to patient data
    filtered_patients = patient_data.copy()
    filtered_patients = filtered_patients[(filtered_patients['Date_of_Service'].dt.date >= start_date) & 
                                         (filtered_patients['Date_of_Service'].dt.date <= end_date)]
    
    if selected_location != 'All':
        filtered_patients = filtered_patients[filtered_patients['Location_ID'].isin(
            filtered_operations['Location_ID'].unique())]
        
    # Add this after your date range filter, before creating visualizations
    # Sample data if date range is too large (optional, for performance)
    if (end_date - start_date).days > 180:  # If more than 6 months of data

        # Sample data for large date ranges to maintain performance
        date_diff = (end_date - start_date).days
        sample_rate = max(1, date_diff // 180)  # Sample to get about 180 days of data
    
        # Get unique dates and sample them
        unique_dates = filtered_operations['Date'].dt.date.unique()
        sampled_dates = sorted(unique_dates)[::sample_rate]
    
        # Filter to only use sampled dates
        filtered_operations = filtered_operations[filtered_operations['Date'].dt.date.isin(sampled_dates)]
        filtered_equipment = filtered_equipment[filtered_equipment['Date'].dt.date.isin(sampled_dates)]
        filtered_staff = filtered_staff[filtered_staff['Date'].dt.date.isin(sampled_dates)]
        filtered_patients = filtered_patients[filtered_patients['Date_of_Service'].dt.date.isin(sampled_dates)]

    
    # Add after applying all filters but before calculating metrics
    st.sidebar.markdown("### Debug Information")
    with st.sidebar.expander("Data Status"):
        st.write(f"Operations data shape: {filtered_operations.shape}")
        if not filtered_operations.empty:
            st.write("Sample metrics in filtered data:")
            st.write(f"Chair Utilization: {filtered_operations['Chair_Utilization'].mean():.2f}%")
            st.write(f"Cancellation Rate: {filtered_operations['Cancellation_Rate'].mean():.2f}%")
            st.write(f"No-Show Rate: {filtered_operations['No_Show_Rate'].mean():.2f}%")
            
            # Check for NaN values or zeros
            st.write(f"NaN in Chair Utilization: {filtered_operations['Chair_Utilization'].isna().sum()}")
            st.write(f"NaN in Cancellation Rate: {filtered_operations['Cancellation_Rate'].isna().sum()}")
            st.write(f"NaN in No-Show Rate: {filtered_operations['No_Show_Rate'].isna().sum()}")
            
            # Check min/max values
            st.write(f"Chair Utilization range: {filtered_operations['Chair_Utilization'].min():.2f}% - {filtered_operations['Chair_Utilization'].max():.2f}%")
            st.write(f"Cancellation Rate range: {filtered_operations['Cancellation_Rate'].min():.2f}% - {filtered_operations['Cancellation_Rate'].max():.2f}%")
            st.write(f"No-Show Rate range: {filtered_operations['No_Show_Rate'].min():.2f}% - {filtered_operations['No_Show_Rate'].max():.2f}%")
        else:
            st.write("Operations data is empty after filtering!")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if not filtered_operations.empty and 'Chair_Utilization' in filtered_operations.columns:
            avg_chair_util = filtered_operations['Chair_Utilization'].mean()
            target_chair_util = filtered_operations['Target_Chair_Utilization'].mean()
            chair_util_diff = avg_chair_util - target_chair_util
            
            st.metric(
                "Avg. Chair Utilization", 
                f"{avg_chair_util:.1f}%", 
                delta=f"{chair_util_diff:.1f}%" if not pd.isna(chair_util_diff) else None,
                delta_color="normal" if chair_util_diff >= 0 else "inverse"
            )
        else:
            st.metric("Avg. Chair Utilization", "N/A")

    with col2:
        if not filtered_operations.empty and 'Cancellation_Rate' in filtered_operations.columns:
            avg_cancellation = filtered_operations['Cancellation_Rate'].mean()
            st.metric("Cancellation Rate", f"{avg_cancellation:.1f}%")
        else:
            st.metric("Cancellation Rate", "N/A")

    with col3:
        if not filtered_operations.empty and 'No_Show_Rate' in filtered_operations.columns:
            avg_no_show = filtered_operations['No_Show_Rate'].mean()
            st.metric("No-Show Rate", f"{avg_no_show:.1f}%")
        else:
            st.metric("No-Show Rate", "N/A")

    with col4:
        if not filtered_operations.empty and 'Actual_Collection_Rate' in filtered_operations.columns:
            avg_collection = filtered_operations['Actual_Collection_Rate'].mean()
            target_collection = filtered_operations['Target_Collection_Rate'].mean()
            collection_diff = avg_collection - target_collection
            
            st.metric(
                "Collection Rate", 
                f"{avg_collection:.1f}%", 
                delta=f"{collection_diff:.1f}%" if not pd.isna(collection_diff) else None,
                delta_color="normal" if collection_diff >= 0 else "inverse"
            )
        else:
            st.metric("Collection Rate", "N/A")
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Capacity & Utilization",
        "Staff Productivity",
        "Patient Flow",
        "Treatment Plans",
        "Insurance & Revenue Cycle"
    ])
    
    # Tab 1: Capacity & Utilization
    with tab1:
        st.subheader("Capacity & Utilization Analysis")
        
        # Chair utilization over time
        st.markdown("### Chair Utilization Trends")
        
        # Group operations data by date
        chair_util_trend = filtered_operations.groupby('Date').agg({
            'Chair_Utilization': 'mean',
            'Target_Chair_Utilization': 'mean'
        }).reset_index()
        
        if not chair_util_trend.empty:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=chair_util_trend['Date'],
                y=chair_util_trend['Chair_Utilization'],
                mode='lines',
                name='Actual Utilization',
                line=dict(color='blue')
            ))
            
            fig.add_trace(go.Scatter(
                x=chair_util_trend['Date'],
                y=chair_util_trend['Target_Chair_Utilization'],
                mode='lines',
                name='Target Utilization',
                line=dict(color='red', dash='dash')
            ))
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Utilization Rate (%)",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No chair utilization data available for the selected filters.")
        
        # Equipment utilization
        st.markdown("### Equipment Utilization by Type")
        
        # Group equipment data by equipment type
        equipment_util = filtered_equipment.groupby('Equipment_Type').agg({
            'Utilization_Rate': 'mean',
            'Usage_Count': 'sum',
            'Usage_Time_Minutes': 'sum'
        }).reset_index()
        
        if not equipment_util.empty:
            fig = px.bar(
                equipment_util.sort_values('Utilization_Rate', ascending=False),
                x='Equipment_Type',
                y='Utilization_Rate',
                color='Utilization_Rate',
                labels={
                    'Equipment_Type': 'Equipment Type',
                    'Utilization_Rate': 'Utilization Rate (%)'
                },
                color_continuous_scale=px.colors.sequential.Blues
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Equipment usage details
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Equipment Usage Count")
                
                fig = px.pie(
                    equipment_util,
                    values='Usage_Count',
                    names='Equipment_Type',
                    title="Usage Count by Equipment Type"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### Equipment Usage Time")
                
                fig = px.pie(
                    equipment_util,
                    values='Usage_Time_Minutes',
                    names='Equipment_Type',
                    title="Usage Time by Equipment Type (minutes)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No equipment utilization data available for the selected filters.")
        
        # Appointment capacity
        st.markdown("### Appointment Capacity Utilization")
        
        # Group by date for appointment capacity trends
        appointment_capacity = filtered_operations.groupby('Date').agg({
            'Appointment_Capacity': 'sum',
            'Scheduled_Appointments': 'sum',
            'Actual_Appointments': 'sum'
        }).reset_index()
        
        if not appointment_capacity.empty:
            # Calculate utilization percentages
            appointment_capacity['Scheduled_Utilization'] = (appointment_capacity['Scheduled_Appointments'] / 
                                                         appointment_capacity['Appointment_Capacity'] * 100)
            appointment_capacity['Actual_Utilization'] = (appointment_capacity['Actual_Appointments'] / 
                                                     appointment_capacity['Appointment_Capacity'] * 100)
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=appointment_capacity['Date'],
                y=appointment_capacity['Appointment_Capacity'],
                name='Total Capacity',
                marker_color='lightgray'
            ))
            
            fig.add_trace(go.Bar(
                x=appointment_capacity['Date'],
                y=appointment_capacity['Scheduled_Appointments'],
                name='Scheduled',
                marker_color='rgba(0, 123, 255, 0.7)'
            ))
            
            fig.add_trace(go.Bar(
                x=appointment_capacity['Date'],
                y=appointment_capacity['Actual_Appointments'],
                name='Actual',
                marker_color='rgba(40, 167, 69, 0.9)'
            ))
            
            fig.update_layout(
                barmode='overlay',
                xaxis_title="Date",
                yaxis_title="Number of Appointments",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Overall utilization metrics
            avg_scheduled_util = appointment_capacity['Scheduled_Utilization'].mean()
            avg_actual_util = appointment_capacity['Actual_Utilization'].mean()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Avg. Scheduled Utilization", f"{avg_scheduled_util:.1f}%")
            
            with col2:
                st.metric("Avg. Actual Utilization", f"{avg_actual_util:.1f}%")
        else:
            st.info("No appointment capacity data available for the selected filters.")
    
    # Tab 2: Staff Productivity
    with tab2:
        st.subheader("Staff Productivity Analysis")
        
        # Staff hours by role
        st.markdown("### Staff Hours by Role")
        
        # Group staff data by role
        staff_hours_by_role = filtered_staff.groupby('Staff_Role').agg({
            'Hours_Worked': 'sum',
            'Labor_Cost': 'sum',
            'Staff_ID': 'nunique'
        }).reset_index()
        
        if not staff_hours_by_role.empty:
            # Sort by hours worked
            staff_hours_by_role = staff_hours_by_role.sort_values('Hours_Worked', ascending=False)
            
            fig = px.bar(
                staff_hours_by_role,
                x='Staff_Role',
                y='Hours_Worked',
                color='Staff_Role',
                labels={
                    'Staff_Role': 'Staff Role',
                    'Hours_Worked': 'Total Hours Worked'
                },
                text='Hours_Worked'
            )
            
            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            
            fig.update_layout(
                xaxis_title="Staff Role",
                yaxis_title="Total Hours Worked",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Labor cost by role
            st.markdown("### Labor Cost by Role")
            
            fig = px.pie(
                staff_hours_by_role,
                values='Labor_Cost',
                names='Staff_Role',
                title="Labor Cost Distribution by Staff Role",
                hole=0.4
            )
            
            # Add cost labels
            fig.update_traces(textinfo='percent+label')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate cost per hour
            staff_hours_by_role['Cost_Per_Hour'] = staff_hours_by_role['Labor_Cost'] / staff_hours_by_role['Hours_Worked']
            
            # Staff cost efficiency
            st.markdown("### Staff Cost Efficiency")
            
            fig = px.bar(
                staff_hours_by_role.sort_values('Cost_Per_Hour'),
                x='Staff_Role',
                y='Cost_Per_Hour',
                color='Staff_Role',
                labels={
                    'Staff_Role': 'Staff Role',
                    'Cost_Per_Hour': 'Cost per Hour ($)'
                },
                text='Cost_Per_Hour'
            )
            
            fig.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
            
            fig.update_layout(
                xaxis_title="Staff Role",
                yaxis_title="Cost per Hour ($)",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No staff data available for the selected filters.")
        
        # Staff productivity over time
        st.markdown("### Staff Productivity Over Time")
        
        # Combine operations and staff data
        operations_staff = filtered_operations.groupby('Date').agg({
            'Total_Patients_Seen': 'sum',
            'Total_Labor_Hours': 'sum',
            'Total_Labor_Cost': 'sum',
            'Revenue_Per_Hour': 'mean'
        }).reset_index()
        
        if not operations_staff.empty and len(operations_staff) > 1:
            # Calculate patients per labor hour
            operations_staff['Patients_Per_Labor_Hour'] = operations_staff['Total_Patients_Seen'] / operations_staff['Total_Labor_Hours']
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=operations_staff['Date'],
                y=operations_staff['Revenue_Per_Hour'],
                mode='lines',
                name='Revenue Per Hour ($)',
                line=dict(color='green')
            ))
            
            fig.add_trace(go.Scatter(
                x=operations_staff['Date'],
                y=operations_staff['Patients_Per_Labor_Hour'],
                mode='lines',
                name='Patients Per Labor Hour',
                line=dict(color='blue'),
                yaxis='y2'
            ))
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Revenue Per Hour ($)",
                yaxis2=dict(
                    title="Patients Per Labor Hour",
                    overlaying='y',
                    side='right'
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Staff productivity metrics
            avg_revenue_per_hour = operations_staff['Revenue_Per_Hour'].mean()
            avg_patients_per_hour = operations_staff['Patients_Per_Labor_Hour'].mean()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Avg. Revenue Per Hour", f"${avg_revenue_per_hour:.2f}")
            
            with col2:
                st.metric("Avg. Patients Per Labor Hour", f"{avg_patients_per_hour:.2f}")
        else:
            st.info("Insufficient data for staff productivity trends with the selected filters.")
    
    # Tab 3: Patient Flow
    with tab3:
        st.subheader("Patient Flow Analysis")
        
        # New vs. returning patients over time
        st.markdown("### New vs. Returning Patients")
        
        # Group operations data by date for patient trends
        patient_trends = filtered_operations.groupby('Date').agg({
            'New_Patient_Count': 'sum',
            'Returning_Patient_Count': 'sum',
            'Total_Patients_Seen': 'sum'
        }).reset_index()
        
        if not patient_trends.empty:
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=patient_trends['Date'],
                y=patient_trends['New_Patient_Count'],
                name='New Patients',
                marker_color='rgba(0, 123, 255, 0.7)'
            ))
            
            fig.add_trace(go.Bar(
                x=patient_trends['Date'],
                y=patient_trends['Returning_Patient_Count'],
                name='Returning Patients',
                marker_color='rgba(40, 167, 69, 0.7)'
            ))
            
            # Add new patient target line if available
            if 'Target_New_Patients' in filtered_operations.columns:
                new_patient_target = filtered_operations.groupby('Date')['Target_New_Patients'].sum().reset_index()
                
                fig.add_trace(go.Scatter(
                    x=new_patient_target['Date'],
                    y=new_patient_target['Target_New_Patients'],
                    mode='lines',
                    name='New Patient Target',
                    line=dict(color='red', dash='dash')
                ))
            
            fig.update_layout(
                barmode='stack',
                xaxis_title="Date",
                yaxis_title="Number of Patients",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # New patient acquisition metrics
            total_new_patients = patient_trends['New_Patient_Count'].sum()
            total_returning_patients = patient_trends['Returning_Patient_Count'].sum()
            new_patient_percentage = (total_new_patients / (total_new_patients + total_returning_patients) * 100) if (total_new_patients + total_returning_patients) > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total New Patients", f"{total_new_patients}")
            
            with col2:
                st.metric("Total Returning Patients", f"{total_returning_patients}")
            
            with col3:
                st.metric("New Patient Percentage", f"{new_patient_percentage:.1f}%")
        else:
            st.info("No patient trend data available for the selected filters.")
        
        # Cancellation and no-show analysis
        st.markdown("### Cancellation & No-Show Analysis")
        
        # Group by day of week
        cancellation_by_day = filtered_operations.groupby('Day_of_Week').agg({
            'Cancellation_Rate': 'mean',
            'No_Show_Rate': 'mean',
            'Cancellation_Count': 'sum',
            'No_Show_Count': 'sum'
        }).reset_index()
        
        # Define day of week order
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        cancellation_by_day['Day_Order'] = cancellation_by_day['Day_of_Week'].apply(lambda x: day_order.index(x))
        cancellation_by_day = cancellation_by_day.sort_values('Day_Order')
        
        if not cancellation_by_day.empty:
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=cancellation_by_day['Day_of_Week'],
                y=cancellation_by_day['Cancellation_Rate'],
                name='Cancellation Rate',
                marker_color='rgba(255, 99, 132, 0.7)'
            ))
            
            fig.add_trace(go.Bar(
                x=cancellation_by_day['Day_of_Week'],
                y=cancellation_by_day['No_Show_Rate'],
                name='No-Show Rate',
                marker_color='rgba(255, 205, 86, 0.7)'
            ))
            
            fig.update_layout(
                barmode='group',
                xaxis_title="Day of Week",
                yaxis_title="Rate (%)",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Count by day
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=cancellation_by_day['Day_of_Week'],
                y=cancellation_by_day['Cancellation_Count'],
                name='Cancellations',
                marker_color='rgba(255, 99, 132, 0.7)'
            ))
            
            fig.add_trace(go.Bar(
                x=cancellation_by_day['Day_of_Week'],
                y=cancellation_by_day['No_Show_Count'],
                name='No-Shows',
                marker_color='rgba(255, 205, 86, 0.7)'
            ))
            
            fig.update_layout(
                barmode='group',
                xaxis_title="Day of Week",
                yaxis_title="Count",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No cancellation data available for the selected filters.")
        
        # Wait time analysis
        if 'Avg_Wait_Time' in filtered_operations.columns:
            st.markdown("### Patient Wait Time Analysis")
            
            # Group by date
            wait_time = filtered_operations.groupby('Date')['Avg_Wait_Time'].mean().reset_index()
            
            if not wait_time.empty:
                fig = px.line(
                    wait_time,
                    x='Date',
                    y='Avg_Wait_Time',
                    labels={
                        'Date': 'Date',
                        'Avg_Wait_Time': 'Average Wait Time (minutes)'
                    },
                    markers=True
                )
                
                # Add a trend line
                fig.add_trace(
                    go.Scatter(
                        x=wait_time['Date'],
                        y=wait_time['Avg_Wait_Time'].rolling(window=7, min_periods=1).mean(),
                        mode='lines',
                        name='7-Day Moving Average',
                        line=dict(color='red', dash='dash')
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Wait time metrics
                avg_wait_time = wait_time['Avg_Wait_Time'].mean()
                max_wait_time = wait_time['Avg_Wait_Time'].max()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Average Wait Time", f"{avg_wait_time:.1f} minutes")
                
                with col2:
                    st.metric("Maximum Average Wait Time", f"{max_wait_time:.1f} minutes")
            else:
                st.info("No wait time data available for the selected filters.")
    
    # Tab 4: Treatment Plans
    with tab4:
        st.subheader("Treatment Plan Management")
        
        # Treatment plan completion rate over time
        st.markdown("### Treatment Plan Completion Rate")
        
        # Group by date
        treatment_plan_trend = filtered_operations.groupby('Date')['Treatment_Plan_Completion_Rate'].mean().reset_index()
        
        if not treatment_plan_trend.empty:
            fig = px.line(
                treatment_plan_trend,
                x='Date',
                y='Treatment_Plan_Completion_Rate',
                labels={
                    'Date': 'Date',
                    'Treatment_Plan_Completion_Rate': 'Completion Rate (%)'
                },
                markers=True
            )
            
            # Add a target line at 100%
            fig.add_shape(
                type="line",
                x0=treatment_plan_trend['Date'].min(),
                y0=100,
                x1=treatment_plan_trend['Date'].max(),
                y1=100,
                line=dict(color="green", width=2, dash="dash"),
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Completion rate metrics
            avg_completion_rate = treatment_plan_trend['Treatment_Plan_Completion_Rate'].mean()
            
            st.metric("Average Completion Rate", f"{avg_completion_rate:.1f}%")
        else:
            st.info("No treatment plan completion rate data available for the selected filters.")
        
        # Treatment plan status breakdown
        st.markdown("### Treatment Plan Status Breakdown")
        
        # Aggregate treatment plan statuses
        treatment_plan_status = filtered_operations.agg({
            'Treatment_Plans_Not_Started': 'sum',
            'Treatment_Plans_In_Progress': 'sum',
            'Treatment_Plans_Completed': 'sum',
            'Treatment_Plans_Delayed': 'sum'
        })
        
        if not treatment_plan_status.empty:
            # Create a DataFrame for plotting
            status_df = pd.DataFrame({
                'Status': ['Not Started', 'In Progress', 'Completed', 'Delayed'],
                'Count': [
                    treatment_plan_status['Treatment_Plans_Not_Started'],
                    treatment_plan_status['Treatment_Plans_In_Progress'],
                    treatment_plan_status['Treatment_Plans_Completed'],
                    treatment_plan_status['Treatment_Plans_Delayed']
                ]
            })
            
            # Create a pie chart
            fig = px.pie(
                status_df,
                values='Count',
                names='Status',
                title="Treatment Plan Status Distribution",
                color='Status',
                color_discrete_map={
                    'Not Started': 'lightblue',
                    'In Progress': 'yellow',
                    'Completed': 'green',
                    'Delayed': 'red'
                }
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a funnel chart for treatment plan progression
            fig = go.Figure(go.Funnel(
                y=['Not Started', 'In Progress', 'Completed'],
                x=[
                    treatment_plan_status['Treatment_Plans_Not_Started'],
                    treatment_plan_status['Treatment_Plans_In_Progress'],
                    treatment_plan_status['Treatment_Plans_Completed']
                ],
                textinfo="value+percent initial"
            ))
            
            fig.update_layout(title_text="Treatment Plan Progression Funnel")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Treatment plan conversion metrics
            total_plans = status_df['Count'].sum()
            conversion_rate = (treatment_plan_status['Treatment_Plans_Completed'] / 
                             (treatment_plan_status['Treatment_Plans_Not_Started'] + 
                              treatment_plan_status['Treatment_Plans_In_Progress'] + 
                              treatment_plan_status['Treatment_Plans_Completed'] + 
                              treatment_plan_status['Treatment_Plans_Delayed']) * 100) if total_plans > 0 else 0
            
            st.metric("Treatment Plan Conversion Rate", f"{conversion_rate:.1f}%")
        else:
            st.info("No treatment plan status data available for the selected filters.")
    
    # Tab 5: Insurance & Revenue Cycle
    with tab5:
        st.subheader("Insurance & Revenue Cycle Management")
        
        # Insurance claim processing trends
        st.markdown("### Insurance Claim Processing")
        
        # Group by date
        claim_trends = filtered_operations.groupby('Date').agg({
            'Insurance_Claims_Submitted': 'sum',
            'Insurance_Claims_Processed': 'sum',
            'Insurance_Claims_Paid': 'sum',
            'Insurance_Claims_Denied': 'sum'
        }).reset_index()
        
        if not claim_trends.empty:
            # Create a stacked bar chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=claim_trends['Date'],
                y=claim_trends['Insurance_Claims_Paid'],
                name='Paid',
                marker_color='rgba(40, 167, 69, 0.7)'
            ))
            
            fig.add_trace(go.Bar(
                x=claim_trends['Date'],
                y=claim_trends['Insurance_Claims_Denied'],
                name='Denied',
                marker_color='rgba(220, 53, 69, 0.7)'
            ))
            
            fig.add_trace(go.Bar(
                x=claim_trends['Date'],
                y=claim_trends['Insurance_Claims_Processed'] - claim_trends['Insurance_Claims_Paid'] - claim_trends['Insurance_Claims_Denied'],
                name='Processed (Not Paid/Denied)',
                marker_color='rgba(255, 193, 7, 0.7)'
            ))
            
            fig.add_trace(go.Bar(
                x=claim_trends['Date'],
                y=claim_trends['Insurance_Claims_Submitted'] - claim_trends['Insurance_Claims_Processed'],
                name='Submitted (Not Processed)',
                marker_color='rgba(108, 117, 125, 0.7)'
            ))
            
            fig.update_layout(
                barmode='stack',
                xaxis_title="Date",
                yaxis_title="Number of Claims",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True, key="tab5_insurance_claims")
            
            # Insurance claim metrics
            total_submitted = claim_trends['Insurance_Claims_Submitted'].sum()
            total_processed = claim_trends['Insurance_Claims_Processed'].sum()
            total_paid = claim_trends['Insurance_Claims_Paid'].sum()
            total_denied = claim_trends['Insurance_Claims_Denied'].sum()
            
            processing_rate = (total_processed / total_submitted * 100) if total_submitted > 0 else 0
            approval_rate = (total_paid / total_processed * 100) if total_processed > 0 else 0
            denial_rate = (total_denied / total_processed * 100) if total_processed > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Claim Processing Rate", f"{processing_rate:.1f}%")
            
            with col2:
                st.metric("Claim Approval Rate", f"{approval_rate:.1f}%")
            
            with col3:
                st.metric("Claim Denial Rate", f"{denial_rate:.1f}%")
        else:
            st.info("No insurance claim data available for the selected filters.")
        
        # Claim aging analysis
        st.markdown("### Claim Aging Analysis")
        
        # Aggregate claim aging data
        claim_aging = filtered_operations.agg({
            'Claims_Aging_0_30': 'sum',
            'Claims_Aging_31_60': 'sum',
            'Claims_Aging_61_90': 'sum',
            'Claims_Aging_90_Plus': 'sum'
        })
        
        if not claim_aging.empty:
            # Create a DataFrame for plotting
            aging_df = pd.DataFrame({
                'Age Range': ['0-30 Days', '31-60 Days', '61-90 Days', '90+ Days'],
                'Count': [
                    claim_aging['Claims_Aging_0_30'],
                    claim_aging['Claims_Aging_31_60'],
                    claim_aging['Claims_Aging_61_90'],
                    claim_aging['Claims_Aging_90_Plus']
                ]
            })
            
            # Create a pie chart
            fig = px.pie(
                aging_df,
                values='Count',
                names='Age Range',
                title="Claim Aging Distribution",
                color='Age Range',
                color_discrete_map={
                    '0-30 Days': 'green',
                    '31-60 Days': 'gold',
                    '61-90 Days': 'orange',
                    '90+ Days': 'red'
                }
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            
            st.plotly_chart(fig, use_container_width=True, key="tab5_claim_aging_pie")
            
            # Create a bar chart
            fig = px.bar(
                aging_df,
                x='Age Range',
                y='Count',
                labels={
                    'Age Range': 'Claim Age',
                    'Count': 'Number of Claims'
                },
                color='Age Range',
                color_discrete_map={
                    '0-30 Days': 'green',
                    '31-60 Days': 'gold',
                    '61-90 Days': 'orange',
                    '90+ Days': 'red'
                }
            )
            
            st.plotly_chart(fig, use_container_width=True, key="tab5_claim_aging_bar")
            
            # Calculate % of claims over 60 days
            total_claims = aging_df['Count'].sum()
            claims_over_60 = claim_aging['Claims_Aging_61_90'] + claim_aging['Claims_Aging_90_Plus']
            percent_over_60 = (claims_over_60 / total_claims * 100) if total_claims > 0 else 0
            
            st.metric("Percentage of Claims Over 60 Days", f"{percent_over_60:.1f}%")
        else:
            st.info("No claim aging data available for the selected filters.")
        
        # Days to payment analysis
        st.markdown("### Days to Payment Analysis")
        
        if 'Avg_Days_To_Payment' in filtered_operations.columns:
            # Group by date
            days_to_payment = filtered_operations.groupby('Date')['Avg_Days_To_Payment'].mean().reset_index()
            
            if not days_to_payment.empty:
                fig = px.line(
                    days_to_payment,
                    x='Date',
                    y='Avg_Days_To_Payment',
                    labels={
                        'Date': 'Date',
                        'Avg_Days_To_Payment': 'Average Days to Payment'
                    },
                    markers=True
                )
                
                # Add a trend line
                fig.add_trace(
                    go.Scatter(
                        x=days_to_payment['Date'],
                        y=days_to_payment['Avg_Days_To_Payment'].rolling(window=7, min_periods=1).mean(),
                        mode='lines',
                        name='7-Day Moving Average',
                        line=dict(color='red', dash='dash')
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True, key="tab5_days_to_payment")
                
                # Days to payment metrics
                avg_days = days_to_payment['Avg_Days_To_Payment'].mean()
                
                st.metric("Average Days to Payment", f"{avg_days:.1f} days")
            else:
                st.info("No days to payment data available for the selected filters.")
        else:
            st.info("Days to payment data not available in the dataset.")
        
        # Collection rate analysis
        st.markdown("### Collection Rate Analysis")
        
        # Group by date
        collection_rate = filtered_operations.groupby('Date').agg({
            'Actual_Collection_Rate': 'mean',
            'Target_Collection_Rate': 'mean'
        }).reset_index()
        
        if not collection_rate.empty:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=collection_rate['Date'],
                y=collection_rate['Actual_Collection_Rate'],
                mode='lines+markers',
                name='Actual Collection Rate',
                line=dict(color='blue')
            ))
            
            fig.add_trace(go.Scatter(
                x=collection_rate['Date'],
                y=collection_rate['Target_Collection_Rate'],
                mode='lines',
                name='Target Collection Rate',
                line=dict(color='red', dash='dash')
            ))
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Collection Rate (%)",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True, key="tab5_collection_rate")
            
            # Collection rate metrics
            avg_actual_rate = collection_rate['Actual_Collection_Rate'].mean()
            avg_target_rate = collection_rate['Target_Collection_Rate'].mean()
            rate_difference = avg_actual_rate - avg_target_rate
            
            st.metric(
                "Average Collection Rate", 
                f"{avg_actual_rate:.1f}%", 
                delta=f"{rate_difference:.1f}%" if not pd.isna(rate_difference) else None,
                delta_color="normal" if rate_difference >= 0 else "inverse"
            )
        else:
            st.info("No collection rate data available for the selected filters.")
    
    # Footer with download option
    st.subheader("Data Download")
    
    # Allow the user to download filtered data
    tab1, tab2, tab3, tab4 = st.tabs(["Operations Data", "Equipment Data", "Staff Data", "Patient Data"])
    
    with tab1:
        st.dataframe(filtered_operations, height=300)
        csv_operations = filtered_operations.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Operations Data as CSV",
            data=csv_operations,
            file_name="filtered_operations_data.csv",
            mime="text/csv"
        )
    
    with tab2:
        st.dataframe(filtered_equipment, height=300)
        csv_equipment = filtered_equipment.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Equipment Data as CSV",
            data=csv_equipment,
            file_name="filtered_equipment_data.csv",
            mime="text/csv"
        )
    
    with tab3:
        st.dataframe(filtered_staff, height=300)
        csv_staff = filtered_staff.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Staff Data as CSV",
            data=csv_staff,
            file_name="filtered_staff_data.csv",
            mime="text/csv"
        )
    
    with tab4:
        st.dataframe(filtered_patients, height=300)
        csv_patients = filtered_patients.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Patient Data as CSV",
            data=csv_patients,
            file_name="filtered_patient_data.csv",
            mime="text/csv"
        )

else:
    st.error("Failed to load data. Please check your data files and paths.")
