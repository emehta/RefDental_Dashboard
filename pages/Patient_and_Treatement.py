import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Revenue Performance", page_icon="💰", layout="wide")

st.title("Patient & Treatment Insights")

# Load data
@st.cache_data
def load_data():
    try:
        return pd.read_csv('data/Pat_App_Data.csv')
    except Exception as e:
        st.error(f"Failed to load data from Pat_App_Data.csv: {e}")
        return None

df = load_data()

if df is not None:
    # Convert date column to datetime
    df['Date_of_Service'] = pd.to_datetime(df['Date_of_Service'], errors='coerce')
    
    # Convert treatment plan dates to datetime
    date_columns = ['Treatment_Plan_Creation_Date', 'Treatment_Plan_Completion_Date', 
                   'Insurance_Claim_Submission_Date', 'Insurance_Claim_Status_Date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Extract month and year
    df['Month_Year'] = df['Date_of_Service'].dt.strftime('%Y-%m')
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date range filter
    min_date = df['Date_of_Service'].min().date()
    max_date = df['Date_of_Service'].max().date()
    
    start_date = st.sidebar.date_input("Start Date", min_date)
    end_date = st.sidebar.date_input("End Date", max_date)
    
    # Location filter
    locations = ['All'] + sorted(df['Location_Name'].unique().tolist())
    selected_location = st.sidebar.selectbox("Select Location", locations)
    
    # Provider filter
    providers = ['All'] + sorted(df['Provider_ID'].unique().tolist())
    selected_provider = st.sidebar.selectbox("Select Provider", providers)
    
    # Insurance filter
    insurance_options = ['All'] + sorted(df['Insurance_Provider'].unique().tolist())
    selected_insurance = st.sidebar.selectbox("Select Insurance", insurance_options)
    
    
    # Apply filters
    filtered_df = df.copy()
    
    # Date filter
    filtered_df = filtered_df[(filtered_df['Date_of_Service'].dt.date >= start_date) & 
                             (filtered_df['Date_of_Service'].dt.date <= end_date)]
    
    # Location filter
    if selected_location != 'All':
        filtered_df = filtered_df[filtered_df['Location_Name'] == selected_location]
    
    # Provider filter
    if selected_provider != 'All':
        filtered_df = filtered_df[filtered_df['Provider_ID'] == selected_provider]
    
    # Insurance filter
    if selected_insurance != 'All':
        filtered_df = filtered_df[filtered_df['Insurance_Provider'] == selected_insurance]
    
    # Group data by Month and Procedure Type
    revenue_by_month_procedure = filtered_df.groupby(['Month_Year', 'Procedure_Description'])['Charged_Amount'].sum().reset_index()
    
    # Prepare data for profitability analysis
    filtered_df['Collected_Amount'] = filtered_df['Insurance_Covered_Amount'] + filtered_df['Out_of_Pocket'] - filtered_df['Discount_Applied']
    filtered_df['Collection_Rate'] = (filtered_df['Collected_Amount'] / filtered_df['Charged_Amount']).fillna(0) * 100
    
    # Calculate profitability by procedure
    profitability = filtered_df.groupby('Procedure_Description').agg({
        'Charged_Amount': 'sum',
        'Collected_Amount': 'sum'
    }).reset_index()
    
    profitability['Collection_Rate'] = (profitability['Collected_Amount'] / profitability['Charged_Amount']).fillna(0) * 100
    profitability = profitability.sort_values('Collected_Amount', ascending=False)
    
    # Calculate monthly totals for trend line
    monthly_revenue = filtered_df.groupby('Month_Year').agg({
        'Charged_Amount': 'sum',
        'Collected_Amount': 'sum'
    }).reset_index()
    
    # Sort by month-year
    monthly_revenue['Month_Year_dt'] = pd.to_datetime(monthly_revenue['Month_Year'] + '-01')
    monthly_revenue = monthly_revenue.sort_values('Month_Year_dt')
    
    # Calculate month-over-month growth
    if len(monthly_revenue) > 1:
        monthly_revenue['MoM_Growth'] = monthly_revenue['Collected_Amount'].pct_change() * 100
    else:
        monthly_revenue['MoM_Growth'] = 0
    
    # Key metrics
    total_revenue = filtered_df['Charged_Amount'].sum()
    total_collected = filtered_df['Collected_Amount'].sum()
    overall_collection_rate = (total_collected / total_revenue * 100) if total_revenue > 0 else 0
    
    # Get top procedures by revenue
    top_procedures = filtered_df.groupby('Procedure_Description')['Charged_Amount'].sum().sort_values(ascending=False).head(3)
    
    # Get latest month's growth rate
    latest_mom_growth = monthly_revenue['MoM_Growth'].iloc[-1] if len(monthly_revenue) > 1 else 0
    
    # Display metrics in three columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Billed Revenue", f"${total_revenue:,.2f}")
        
    with col2:
        st.metric("Total Collected Revenue", f"${total_collected:,.2f}")
        
    with col3:
        st.metric("Overall Collection Rate", f"{overall_collection_rate:.1f}%", 
                 delta=f"{latest_mom_growth:.1f}%" if not pd.isna(latest_mom_growth) else None)
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Appointments", 
        "Patient Mix Analysis",
        "Location Performance",
        "Insurance Performance",
        "Treatment Plan Analysis"
    ])
    
    with tab1:
        if not revenue_by_month_procedure.empty:
            # Appointments by Location Analysis
            st.subheader("Appointments by Location")
            
            # Calculate location statistics
            location_stats = filtered_df.groupby('Location_Name').agg({
                'Visit_ID': 'count',
                'Appointment_Status': lambda x: (x == 'Completed').mean() * 100,
                'Charged_Amount': 'sum',
                'Collected_Amount': 'sum'
            }).reset_index()
            
            location_stats.columns = ['Location_Name', 'Total_Appointments', 'Completion_Rate', 'Total_Charged', 'Total_Collected']
            location_stats['Collection_Rate'] = (location_stats['Total_Collected'] / location_stats['Total_Charged'] * 100)
            
            # Sort by total appointments
            location_stats = location_stats.sort_values('Total_Appointments', ascending=False)
            
            # Create two columns for metrics
            col1, col2 = st.columns(2)
            
            with col1:
                # Location with most appointments
                busiest_location = location_stats.iloc[0]
                st.metric(
                    "Busiest Location",
                    busiest_location['Location_Name'],
                    f"{busiest_location['Total_Appointments']:,} appointments"
                )
            
            with col2:
                # Location with best completion rate
                best_completion = location_stats.loc[location_stats['Completion_Rate'].idxmax()]
                st.metric(
                    "Best Completion Rate",
                    f"{best_completion['Completion_Rate']:.1f}%",
                    f"at {best_completion['Location_Name']}"
                )
            
            # Create bar chart for appointments by location
            fig_location = px.bar(
                location_stats,
                x='Location_Name',
                y=['Total_Appointments', 'Completion_Rate'],
                title="Appointments and Completion Rates by Location",
                labels={
                    'Location_Name': 'Location',
                    'value': 'Count/Rate',
                    'variable': 'Metric'
                },
                barmode='group',
                color_discrete_sequence=['#2196F3', '#4CAF50']
            )
            
            # Update layout
            fig_location.update_layout(
                yaxis=dict(
                    title="Count/Rate",
                    range=[0, max(location_stats['Total_Appointments'].max() * 1.1, 100)]
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig_location, use_container_width=True)
            
            # Create a detailed location summary table
            st.subheader("Location Performance Summary")
            
            # Format the data for display
            display_stats = location_stats.copy()
            display_stats['Completion_Rate'] = display_stats['Completion_Rate'].apply(lambda x: f"{x:.1f}%")
            display_stats['Collection_Rate'] = display_stats['Collection_Rate'].apply(lambda x: f"{x:.1f}%")
            display_stats['Total_Charged'] = display_stats['Total_Charged'].apply(lambda x: f"${x:,.2f}")
            display_stats['Total_Collected'] = display_stats['Total_Collected'].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(display_stats, use_container_width=True)
            
            fig = px.bar(
                revenue_by_month_procedure, 
                x='Month_Year', 
                y='Charged_Amount',
                color='Procedure_Description',
                title="Monthly Revenue Breakdown by Procedure",
                labels={'Month_Year': 'Month', 'Charged_Amount': 'Revenue ($)', 'Procedure_Description': 'Procedure'},
            )
            
            # Funnel chart: scheduled → checked‑in → completed → claims submitted → claims paid
            funnel_df = pd.DataFrame({
                'Stage': [
                    'Scheduled',
                    'Checked-In',
                    'Completed',
                    'Claims Submitted',
                    'Claims Paid'
                ],
                'Count': [
                    filtered_df['Visit_ID'].nunique(),
                    filtered_df[filtered_df['Appointment_Status'] != 'No-Show']['Visit_ID'].nunique(),
                    filtered_df[filtered_df['Appointment_Status'] == 'Completed']['Visit_ID'].nunique(),
                    filtered_df[filtered_df['Insurance_Claim_Submission_Date'].notna()]['Visit_ID'].nunique(),
                    filtered_df[filtered_df['Insurance_Claim_Status'] == 'Paid']['Visit_ID'].nunique()
                ]
            })
            funnel_fig = px.funnel(
                funnel_df,
                x='Count',
                y='Stage',
                title='Appointment → Claims Funnel'
            )
            st.plotly_chart(funnel_fig, use_container_width=True)
            
            # New Visualization 1: Appointment Distribution
            st.subheader("Appointment Distribution by Day and Hour")
            
            # Extract day of week and hour from Date_of_Service
            filtered_df['Day_of_Week'] = filtered_df['Date_of_Service'].dt.day_name()
            filtered_df['Hour'] = filtered_df['Date_of_Service'].dt.hour
            
            # Create distribution data
            dist_data = filtered_df.groupby(['Day_of_Week', 'Hour'])['Visit_ID'].count().reset_index()
            
            # Reorder days of week
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dist_data['Day_of_Week'] = pd.Categorical(dist_data['Day_of_Week'], categories=days_order, ordered=True)
            dist_data = dist_data.sort_values(['Day_of_Week', 'Hour'])
            
            # Create grouped bar chart
            fig_dist = px.bar(
                dist_data,
                x='Hour',
                y='Visit_ID',
                color='Day_of_Week',
                title="Appointment Distribution by Day and Hour",
                labels={
                    'Hour': 'Hour of Day',
                    'Visit_ID': 'Number of Appointments',
                    'Day_of_Week': 'Day of Week'
                },
                barmode='group',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            # Update layout for better readability
            fig_dist.update_layout(
                xaxis=dict(
                    title="Hour of Day",
                    tickmode='array',
                    ticktext=[f"{i:02d}:00" for i in range(24)],
                    tickvals=list(range(24))
                ),
                yaxis_title="Number of Appointments",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                showlegend=True
            )
            
            st.plotly_chart(fig_dist, use_container_width=True)
            
            # Add summary statistics
            col1, col2 = st.columns(2)
            with col1:
                peak_hour = dist_data.loc[dist_data['Visit_ID'].idxmax()]
                st.metric(
                    "Peak Appointment Time",
                    f"{peak_hour['Hour']:02d}:00",
                    f"on {peak_hour['Day_of_Week']} ({peak_hour['Visit_ID']} appointments)"
                )
            with col2:
                total_appointments = dist_data['Visit_ID'].sum()
                st.metric(
                    "Total Appointments",
                    f"{total_appointments:,}",
                    "in selected period"
                )
            
            # New Visualization 2: Procedure Completion Rates
            st.subheader("Procedure Completion Rates")
            
            # Calculate completion rates by procedure
            procedure_completion = filtered_df.groupby('Procedure_Description').agg({
                'Visit_ID': 'count',
                'Appointment_Status': lambda x: (x == 'Completed').mean() * 100
            }).reset_index()
            
            procedure_completion.columns = ['Procedure_Description', 'Total_Appointments', 'Completion_Rate']
            
            # Sort by completion rate
            procedure_completion = procedure_completion.sort_values('Completion_Rate', ascending=True)
            
            # Create horizontal bar chart
            fig_procedure = px.bar(
                procedure_completion,
                y='Procedure_Description',
                x='Completion_Rate',
                color='Total_Appointments',
                title="Appointment Completion Rates by Procedure",
                labels={
                    'Procedure_Description': 'Procedure',
                    'Completion_Rate': 'Completion Rate (%)',
                    'Total_Appointments': 'Total Appointments'
                },
                color_continuous_scale="Viridis",
                orientation='h'
            )
            
            # Update layout
            fig_procedure.update_layout(
                yaxis_title="",
                xaxis_title="Completion Rate (%)",
                xaxis=dict(range=[0, 100]),
                height=max(400, len(procedure_completion) * 25),  # Dynamic height based on number of procedures
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig_procedure, use_container_width=True)
            
            # Add summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                best_procedure = procedure_completion.iloc[-1]
                st.metric(
                    "Highest Completion Rate",
                    f"{best_procedure['Completion_Rate']:.1f}%",
                    f"{best_procedure['Procedure_Description']} ({best_procedure['Total_Appointments']} appointments)"
                )
            with col2:
                worst_procedure = procedure_completion.iloc[0]
                st.metric(
                    "Lowest Completion Rate",
                    f"{worst_procedure['Completion_Rate']:.1f}%",
                    f"{worst_procedure['Procedure_Description']} ({worst_procedure['Total_Appointments']} appointments)"
                )
            with col3:
                avg_completion = procedure_completion['Completion_Rate'].mean()
                st.metric(
                    "Average Completion Rate",
                    f"{avg_completion:.1f}%",
                    f"across {len(procedure_completion)} procedures"
                )
            
            # Original completion rate analysis remains unchanged
            st.subheader("Appointment Completion Rate")
            
            # Calculate completion rate by month
            filtered_df['Month'] = filtered_df['Date_of_Service'].dt.to_period('M')
            
            # Calculate scheduled appointments (Completed, Canceled, No-Show)
            sched = filtered_df[filtered_df['Appointment_Status'].isin(['Completed', 'Canceled', 'No-Show'])].groupby('Month')['Visit_ID'].nunique()
            
            # Calculate completed appointments
            comp = filtered_df[filtered_df['Appointment_Status'] == 'Completed'].groupby('Month')['Visit_ID'].nunique()
            
            # Calculate completion rate
            completion_rate = (comp / sched * 100).reset_index()
            completion_rate.columns = ['Month', 'Completion_Rate']
            
            # Convert Period to string for plotting
            completion_rate['Month'] = completion_rate['Month'].astype(str)
            
            # Create line chart
            completion_fig = px.line(
                completion_rate,
                x='Month',
                y='Completion_Rate',
                title="Monthly Appointment Completion Rate",
                labels={'Month': 'Month', 'Completion_Rate': 'Completion Rate (%)'},
                markers=True
            )
            
            # Set y-axis range from 0 to 100
            completion_fig.update_layout(
                yaxis=dict(range=[0, 100]),
                xaxis=dict(title="Month"),
                yaxis_title="Completion Rate (%)"
            )
            
            st.plotly_chart(completion_fig, use_container_width=True)
            
            # No-Show & Cancellation Rates Analysis
            st.subheader("No-Show & Cancellation Rates")
            
            # Calculate no-show and cancellation rates
            no_show = filtered_df[filtered_df['Appointment_Status'] == 'No-Show'].groupby('Month')['Visit_ID'].nunique() / sched * 100
            cancel = filtered_df[filtered_df['Appointment_Status'] == 'Canceled'].groupby('Month')['Visit_ID'].nunique() / sched * 100
            
            # Create a DataFrame for the stacked area chart
            rates_df = pd.DataFrame({
                'Month': no_show.index.astype(str),
                'No-Show Rate (%)': no_show.values,
                'Cancellation Rate (%)': cancel.values
            })
            
            # Create stacked area chart
            rates_fig = px.area(
                rates_df,
                x='Month',
                y=['No-Show Rate (%)', 'Cancellation Rate (%)'],
                title="Monthly No-Show & Cancellation Rates",
                labels={'value': 'Rate (%)', 'variable': 'Type'},
                color_discrete_sequence=['#FF9999', '#99CCFF']
            )
            
            # Update layout
            rates_fig.update_layout(
                yaxis=dict(range=[0, 100]),
                xaxis=dict(title="Month"),
                yaxis_title="Rate (%)",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(rates_fig, use_container_width=True)
            
            # No-Show Rate by Day-of-Week Analysis
            st.subheader("No-Show Rate by Day of Week")
            
            # Extract day of week from Date_of_Service
            filtered_df['Day_of_Week'] = filtered_df['Date_of_Service'].dt.day_name()
            
            # Calculate total appointments and no-shows by day of week
            day_stats = filtered_df.groupby('Day_of_Week').agg({
                'Visit_ID': 'count',
                'Appointment_Status': lambda x: (x == 'No-Show').sum()
            }).reset_index()
            
            # Rename columns
            day_stats.columns = ['Day_of_Week', 'Total_Appointments', 'No_Shows']
            
            # Calculate no-show rate
            day_stats['No_Show_Rate'] = (day_stats['No_Shows'] / day_stats['Total_Appointments'] * 100)
            
            # Reorder days of week
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_stats['Day_of_Week'] = pd.Categorical(day_stats['Day_of_Week'], categories=days_order, ordered=True)
            day_stats = day_stats.sort_values('Day_of_Week')
            
            # Create bar chart
            fig_day_noshow = px.bar(
                day_stats,
                x='Day_of_Week',
                y='No_Show_Rate',
                color='Total_Appointments',
                title="No-Show Rate by Day of Week",
                labels={
                    'Day_of_Week': 'Day of Week',
                    'No_Show_Rate': 'No-Show Rate (%)',
                    'Total_Appointments': 'Total Appointments'
                },
                color_continuous_scale="Reds"
            )
            
            # Update layout
            fig_day_noshow.update_layout(
                yaxis=dict(range=[0, 100]),
                yaxis_title="No-Show Rate (%)",
                xaxis_title="Day of Week"
            )
            
            st.plotly_chart(fig_day_noshow, use_container_width=True)
            
            # Display summary statistics
            col1, col2 = st.columns(2)
            with col1:
                worst_day = day_stats.loc[day_stats['No_Show_Rate'].idxmax()]
                st.metric(
                    "Highest No-Show Rate",
                    f"{worst_day['No_Show_Rate']:.1f}%",
                    f"on {worst_day['Day_of_Week']}"
                )
            with col2:
                best_day = day_stats.loc[day_stats['No_Show_Rate'].idxmin()]
                st.metric(
                    "Lowest No-Show Rate",
                    f"{best_day['No_Show_Rate']:.1f}%",
                    f"on {best_day['Day_of_Week']}"
                )
                
        else:
            st.warning("No data available for the selected filters")
    
    with tab2:
        st.subheader("Patient Mix Analysis")
        
        # New vs. Returning Patient Mix Analysis
        st.subheader("New vs. Returning Patient Mix")
        
        # Calculate new and returning patient counts by month
        new = filtered_df[filtered_df['Is_New_Patient']].groupby('Month')['Visit_ID'].nunique()
        ret = filtered_df[~filtered_df['Is_New_Patient']].groupby('Month')['Visit_ID'].nunique()
        
        # Get all months from the filtered data
        all_months = sorted(filtered_df['Month'].unique())
        
        # Reindex both Series to ensure they have the same index
        new = new.reindex(all_months, fill_value=0)
        ret = ret.reindex(all_months, fill_value=0)
        
        # Create a DataFrame for the grouped bar chart
        patient_mix_df = pd.DataFrame({
            'Month': [str(m) for m in all_months],
            'New Patients': new.values,
            'Returning Patients': ret.values
        })
        
        # Create grouped bar chart
        patient_mix_fig = px.bar(
            patient_mix_df,
            x='Month',
            y=['New Patients', 'Returning Patients'],
            title="Monthly New vs. Returning Patient Mix",
            labels={'value': 'Number of Patients', 'variable': 'Patient Type'},
            barmode='group',
            color_discrete_sequence=['#4CAF50', '#2196F3']
        )
        
        # Update layout
        patient_mix_fig.update_layout(
            xaxis=dict(title="Month"),
            yaxis=dict(title="Number of Patients"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(patient_mix_fig, use_container_width=True)
    
    # Location-Based Performance Analysis
    with tab3:
        st.subheader("Location-Based Performance Analysis")
        
        if 'Location_Name' in filtered_df.columns and 'Google_Rating' in filtered_df.columns:
            # Group by location to get key metrics
            location_performance = filtered_df.groupby('Location_Name').agg({
                'Charged_Amount': 'sum',
                'Collected_Amount': 'sum',
                'Google_Rating': 'first',
                'Visit_ID': 'nunique',
                'Appointment_Status': lambda x: (x == 'Completed').mean() * 100
            }).reset_index()
            
            # Calculate metrics
            location_performance['Collection_Rate'] = (location_performance['Collected_Amount'] / location_performance['Charged_Amount']).fillna(0) * 100
            location_performance['Revenue_Per_Visit'] = (location_performance['Collected_Amount'] / location_performance['Visit_ID']).fillna(0)
            location_performance['Completion_Rate'] = location_performance['Appointment_Status']
            
            # Rating Analysis Section
            st.subheader("Customer Rating Analysis")
            
            # Calculate rating statistics
            col1, col2 = st.columns(2)
            with col1:
                avg_rating = location_performance['Google_Rating'].mean()
                st.metric("Average Google Rating", f"{avg_rating:.1f} ⭐")
            
            with col2:
                best_rated = location_performance.loc[location_performance['Google_Rating'].idxmax()]
                st.metric("Highest Rated Location", f"{best_rated['Google_Rating']:.1f} ⭐", best_rated['Location_Name'])
            
            # Create scatter plot of Rating vs Revenue
            fig1 = px.scatter(
                location_performance,
                x='Google_Rating',
                y='Revenue_Per_Visit',
                size='Visit_ID',
                color='Completion_Rate',
                hover_name='Location_Name',
                title="Revenue Performance vs. Google Rating",
                labels={
                    'Google_Rating': 'Google Rating (⭐)',
                    'Revenue_Per_Visit': 'Avg. Revenue Per Visit ($)',
                    'Visit_ID': 'Number of Visits',
                    'Completion_Rate': 'Completion Rate (%)'
                }
            )
            
            st.plotly_chart(fig1, use_container_width=True)
            
            # Customer Experience Analysis
            st.subheader("Customer Experience Analysis")
            
            # Calculate customer experience metrics
            location_performance['No_Show_Rate'] = filtered_df.groupby('Location_Name')['Appointment_Status'].apply(
                lambda x: (x == 'No-Show').mean() * 100
            ).values
            
            # Calculate average appointment duration if the column exists
            if 'Appointment_Duration' in filtered_df.columns:
                location_performance['Avg_Appointment_Duration'] = filtered_df.groupby('Location_Name')['Appointment_Duration'].mean().values
            
            # Create a multi-metric comparison chart
            fig_experience = go.Figure()
            
            # Add traces for each metric
            fig_experience.add_trace(go.Bar(
                name='No-Show Rate (%)',
                x=location_performance['Location_Name'],
                y=location_performance['No_Show_Rate'],
                yaxis='y',
                marker_color='#FF9999'
            ))
            
            fig_experience.add_trace(go.Scatter(
                name='Google Rating',
                x=location_performance['Location_Name'],
                y=location_performance['Google_Rating'],
                yaxis='y2',
                    mode='lines+markers',
                line=dict(color='#4CAF50')
            ))
            
            # Update layout
            fig_experience.update_layout(
                title="Customer Experience Metrics by Location",
                xaxis=dict(title="Location"),
                yaxis=dict(
                    title="No-Show Rate (%)",
                    range=[0, 100]
                ),
                yaxis2=dict(
                    title="Google Rating (⭐)",
                    overlaying='y',
                    side='right',
                    range=[0, 5]
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig_experience, use_container_width=True)
            
            # Add key experience metrics
            col1, col2 = st.columns(2)
            with col1:
                best_experience = location_performance.loc[location_performance['No_Show_Rate'].idxmin()]
                st.metric(
                    "Best Attendance Rate",
                    f"{100 - best_experience['No_Show_Rate']:.1f}%",
                    f"at {best_experience['Location_Name']}"
                )
            
            with col2:
                worst_experience = location_performance.loc[location_performance['No_Show_Rate'].idxmax()]
                st.metric(
                    "Highest No-Show Rate",
                    f"{worst_experience['No_Show_Rate']:.1f}%",
                    f"at {worst_experience['Location_Name']}"
                )
            
            # Customer Loyalty Analysis
            st.subheader("Customer Loyalty Analysis")
            
            # Calculate repeat visit metrics
            repeat_visits = filtered_df.groupby(['Location_Name', 'Patient_ID']).size().reset_index(name='Visit_Count')
            loyalty_metrics = repeat_visits.groupby('Location_Name').agg({
                'Patient_ID': 'count',
                'Visit_Count': ['mean', 'max']
            }).reset_index()
            
            loyalty_metrics.columns = ['Location_Name', 'Unique_Patients', 'Avg_Visits', 'Max_Visits']
            loyalty_metrics['Repeat_Visit_Rate'] = (loyalty_metrics['Avg_Visits'] > 1).astype(int) * 100
            
            # Create loyalty metrics visualization
            fig_loyalty = px.bar(
                loyalty_metrics,
                x='Location_Name',
                y=['Unique_Patients', 'Avg_Visits'],
                title="Customer Loyalty Metrics by Location",
                labels={
                    'Location_Name': 'Location',
                    'value': 'Count',
                    'variable': 'Metric'
                },
                barmode='group',
                color_discrete_sequence=['#2196F3', '#4CAF50']
            )
            
            st.plotly_chart(fig_loyalty, use_container_width=True)
            
            # Display key loyalty metrics
            col1, col2 = st.columns(2)
            with col1:
                most_loyal = loyalty_metrics.loc[loyalty_metrics['Avg_Visits'].idxmax()]
                st.metric(
                    "Most Loyal Customer Base",
                    most_loyal['Location_Name'],
                    f"Avg. {most_loyal['Avg_Visits']:.1f} visits per patient"
                )
            
            with col2:
                highest_retention = loyalty_metrics.loc[loyalty_metrics['Repeat_Visit_Rate'].idxmax()]
                st.metric(
                    "Highest Retention Rate",
                    f"{highest_retention['Repeat_Visit_Rate']:.1f}%",
                    f"at {highest_retention['Location_Name']}"
                )
            
            # Create a detailed rating summary table
            st.subheader("Location Rating Summary")
            
            # Format the data for display
            rating_summary = location_performance.copy()
            rating_summary['Google_Rating'] = rating_summary['Google_Rating'].apply(lambda x: f"{x:.1f} ⭐")
            rating_summary['Completion_Rate'] = rating_summary['Completion_Rate'].apply(lambda x: f"{x:.1f}%")
            rating_summary['Collection_Rate'] = rating_summary['Collection_Rate'].apply(lambda x: f"{x:.1f}%")
            rating_summary['Revenue_Per_Visit'] = rating_summary['Revenue_Per_Visit'].apply(lambda x: f"${x:,.2f}")
            
            # Sort by Google Rating
            rating_summary = rating_summary.sort_values('Google_Rating', ascending=False)
            
            st.dataframe(rating_summary[['Location_Name', 'Google_Rating', 'Visit_ID', 'Completion_Rate', 'Collection_Rate', 'Revenue_Per_Visit']], 
                        use_container_width=True)
            
            # Original location performance table continues below
            st.subheader("Location Performance Metrics")
            
            # Create scatter plot of Google Rating vs Revenue
            fig1 = px.scatter(
                location_performance,
                x='Google_Rating',
                y='Revenue_Per_Visit',
                size='Visit_ID',
                color='Collection_Rate',
                hover_name='Location_Name',
                title="Revenue Performance vs. Google Rating",
                labels={
                    'Google_Rating': 'Google Rating (⭐)',
                    'Revenue_Per_Visit': 'Avg. Revenue Per Visit ($)',
                    'Visit_ID': 'Number of Visits',
                    'Collection_Rate': 'Collection Rate (%)'
                }
            )
            
            st.plotly_chart(fig1, use_container_width=True)
            
            # Location performance table
            st.subheader("Location Performance Metrics")
            
            # Format for display
            display_df = location_performance.copy()
            display_df['Collection_Rate'] = display_df['Collection_Rate'].apply(lambda x: f"{x:.1f}%")
            display_df['Charged_Amount'] = display_df['Charged_Amount'].apply(lambda x: f"${x:,.2f}")
            display_df['Collected_Amount'] = display_df['Collected_Amount'].apply(lambda x: f"${x:,.2f}")
            display_df['Revenue_Per_Visit'] = display_df['Revenue_Per_Visit'].apply(lambda x: f"${x:,.2f}")
            
            # Rename columns for better readability
            display_df = display_df.rename(columns={
                'Location_Name': 'Location',
                'Charged_Amount': 'Billed Revenue',
                'Collected_Amount': 'Collected Revenue',
                'Visit_ID': 'Number of Visits',
                'Google_Rating': 'Google Rating',
                'Revenue_Per_Visit': 'Avg. Revenue/Visit',
                'Collection_Rate': 'Collection Rate'
            })
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("Location data not available in the dataset")
    
    # Insurance Analysis
    with tab4:
        st.subheader("Procedure Profitability by Insurance Provider")
        
        if 'Insurance_Provider' in filtered_df.columns and 'Procedure_Description' in filtered_df.columns:
            # Group data by insurance provider and procedure
            insurance_procedure = filtered_df.groupby(['Insurance_Provider', 'Procedure_Description']).agg({
                'Charged_Amount': 'sum',
                'Insurance_Covered_Amount': 'sum',
                'Collected_Amount': 'sum',
                'Visit_ID': 'nunique'
            }).reset_index()
            
            # Calculate reimbursement rate
            insurance_procedure['Reimbursement_Rate'] = (insurance_procedure['Insurance_Covered_Amount'] / 
                                                        insurance_procedure['Charged_Amount']).fillna(0) * 100
            
            # Calculate total collection rate (including patient portion)
            insurance_procedure['Collection_Rate'] = (insurance_procedure['Collected_Amount'] / 
                                                    insurance_procedure['Charged_Amount']).fillna(0) * 100
            
            # Get list of top 10 procedures by volume
            top_procedures = filtered_df['Procedure_Description'].value_counts().head(10).index.tolist()
            
            # Let user select a procedure to analyze
            selected_procedure = st.selectbox(
                "Select Procedure to Analyze",
                options=top_procedures,
                index=0
            )
            
            # Filter data for selected procedure
            procedure_data = insurance_procedure[insurance_procedure['Procedure_Description'] == selected_procedure]
            
            if not procedure_data.empty:
                # Sort by reimbursement rate
                procedure_data = procedure_data.sort_values('Reimbursement_Rate', ascending=False)
                
                # Create horizontal bar chart comparing insurance providers
                fig = px.bar(
                    procedure_data,
                    y='Insurance_Provider',
                    x='Reimbursement_Rate',
                    title=f"Insurance Reimbursement Rates for {selected_procedure}",
                    labels={
                        'Insurance_Provider': 'Insurance Provider',
                        'Reimbursement_Rate': 'Reimbursement Rate (%)'
                    },
                    orientation='h',
                    color='Reimbursement_Rate',
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                
                fig.update_layout(xaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
                
                # Create a comparison table
                st.subheader("Detailed Insurance Comparison")
                
                # Format for display
                display_df = procedure_data.copy()
                display_df['Reimbursement_Rate'] = display_df['Reimbursement_Rate'].apply(lambda x: f"{x:.1f}%")
                display_df['Collection_Rate'] = display_df['Collection_Rate'].apply(lambda x: f"{x:.1f}%")
                display_df['Charged_Amount'] = display_df['Charged_Amount'].apply(lambda x: f"${x:,.2f}")
                display_df['Insurance_Covered_Amount'] = display_df['Insurance_Covered_Amount'].apply(lambda x: f"${x:,.2f}")
                display_df['Collected_Amount'] = display_df['Collected_Amount'].apply(lambda x: f"${x:,.2f}")
                
                # Rename columns for better readability
                display_df = display_df.rename(columns={
                    'Insurance_Provider': 'Insurance Provider',
                    'Charged_Amount': 'Billed Amount',
                    'Insurance_Covered_Amount': 'Insurance Covered',
                    'Collected_Amount': 'Total Collected',
                    'Visit_ID': 'Number of Procedures',
                    'Reimbursement_Rate': 'Insurance Reimbursement %',
                    'Collection_Rate': 'Total Collection %'
                })
                
                st.dataframe(display_df, use_container_width=True)
                
                # Get the best and worst insurance providers for this procedure
                if len(procedure_data) > 1:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Best Reimbursement")
                        best_provider = procedure_data.iloc[0]
                        st.write(f"**{best_provider['Insurance_Provider']}**")
                        st.write(f"Reimbursement Rate: {best_provider['Reimbursement_Rate']:.1f}%")
                        st.write(f"Average Insurance Payment: ${best_provider['Insurance_Covered_Amount']/best_provider['Visit_ID']:,.2f}")
                    
                    with col2:
                        st.subheader("Lowest Reimbursement")
                        worst_provider = procedure_data.iloc[-1]
                        st.write(f"**{worst_provider['Insurance_Provider']}**")
                        st.write(f"Reimbursement Rate: {worst_provider['Reimbursement_Rate']:.1f}%")
                        st.write(f"Average Insurance Payment: ${worst_provider['Insurance_Covered_Amount']/worst_provider['Visit_ID']:,.2f}")
            else:
                st.info(f"No data available for {selected_procedure}")
            
            # Compare top procedures across insurance providers
            st.subheader("Top Procedures by Insurance Provider")
            
            # Get all insurance providers
            insurance_providers = filtered_df['Insurance_Provider'].unique()
            
            # Let user select an insurance provider to analyze
            selected_insurance_provider = st.selectbox(
                "Select Insurance Provider",
                options=insurance_providers,
                index=0
            )
            
            # Filter data for selected insurance provider
            provider_data = insurance_procedure[insurance_procedure['Insurance_Provider'] == selected_insurance_provider]
            
            if not provider_data.empty:
                # Sort by reimbursement rate and get top 10
                provider_data = provider_data.sort_values('Reimbursement_Rate', ascending=False).head(10)
                
                # Create horizontal bar chart
                fig = px.bar(
                    provider_data,
                    y='Procedure_Description',
                    x='Reimbursement_Rate',
                    title=f"Best Reimbursed Procedures for {selected_insurance_provider}",
                    labels={
                        'Procedure_Description': 'Procedure',
                        'Reimbursement_Rate': 'Reimbursement Rate (%)'
                    },
                    orientation='h',
                    color='Reimbursement_Rate',
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                
                fig.update_layout(xaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No data available for {selected_insurance_provider}")
        else:
            st.warning("Insurance provider data not available in the dataset")
        
        # Advanced Insurance Analytics
        st.subheader("Advanced Insurance Analytics")
        
        # Create tabs for different insurance analytics
        insurance_tab1, insurance_tab2 = st.tabs([
            "Insurance Claim Processing Analysis",
            "Insurance Denial Patterns"
        ])
        
        with insurance_tab1:
            # Insurance Claim Processing Analysis
            st.subheader("Insurance Claim Processing Analysis")
            
            # Check if we have the necessary columns
            required_columns = ['Insurance_Claim_Submission_Date', 'Insurance_Claim_Status_Date', 
                              'Insurance_Claim_Status', 'Insurance_Provider', 'Charged_Amount']
            
            if all(col in filtered_df.columns for col in required_columns):
                # Calculate processing time for claims
                filtered_df['Claim_Processing_Days'] = (
                    filtered_df['Insurance_Claim_Status_Date'] - filtered_df['Insurance_Claim_Submission_Date']
                ).dt.days
                
                # Filter out claims with invalid processing times
                valid_claims = filtered_df[
                    (filtered_df['Claim_Processing_Days'].notna()) & 
                    (filtered_df['Claim_Processing_Days'] >= 0)
                ]
                
                if not valid_claims.empty:
                    # Calculate average processing time by insurance provider
                    processing_by_provider = valid_claims.groupby('Insurance_Provider').agg({
                        'Claim_Processing_Days': ['mean', 'median', 'count'],
                        'Insurance_Claim_Status': lambda x: (x == 'Paid').mean() * 100
                    }).reset_index()
                    
                    # Flatten column names
                    processing_by_provider.columns = ['Insurance_Provider', 'Avg_Processing_Days', 
                                                    'Median_Processing_Days', 'Claim_Count', 'Paid_Rate']
                    
                    # Sort by average processing time
                    processing_by_provider = processing_by_provider.sort_values('Avg_Processing_Days')
                    
                    # Create a bar chart of average processing time by insurance provider
                    fig_processing = px.bar(
                        processing_by_provider,
                        x='Insurance_Provider',
                        y='Avg_Processing_Days',
                        color='Paid_Rate',
                        title="Average Claim Processing Time by Insurance Provider",
                        labels={
                            'Insurance_Provider': 'Insurance Provider',
                            'Avg_Processing_Days': 'Average Processing Time (Days)',
                            'Paid_Rate': 'Paid Rate (%)'
                        },
                        color_continuous_scale=px.colors.sequential.Viridis
                    )
                    
                    st.plotly_chart(fig_processing, use_container_width=True)
                    
                    # Create a histogram of processing time distribution
                    fig_hist = px.histogram(
                        valid_claims,
                        x='Claim_Processing_Days',
                        title="Distribution of Insurance Claim Processing Times",
                        labels={'Claim_Processing_Days': 'Processing Time (Days)'},
                        marginal='box'
                    )
                    
                    st.plotly_chart(fig_hist, use_container_width=True)
                    
                    # Calculate and display key metrics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        avg_processing = valid_claims['Claim_Processing_Days'].mean()
                        st.metric("Average Processing Time", f"{avg_processing:.1f} days")
                    
                    with col2:
                        median_processing = valid_claims['Claim_Processing_Days'].median()
                        st.metric("Median Processing Time", f"{median_processing:.1f} days")
                    
                    with col3:
                        paid_rate = (valid_claims['Insurance_Claim_Status'] == 'Paid').mean() * 100
                        st.metric("Overall Paid Rate", f"{paid_rate:.1f}%")
                    
                    # Create a scatter plot of processing time vs. claim amount
                    fig_scatter = px.scatter(
                        valid_claims,
                        x='Claim_Processing_Days',
                        y='Charged_Amount',
                        color='Insurance_Claim_Status',
                        size='Collected_Amount',
                        hover_name='Insurance_Provider',
                        title="Claim Processing Time vs. Claim Amount",
                        labels={
                            'Claim_Processing_Days': 'Processing Time (Days)',
                            'Charged_Amount': 'Claim Amount ($)',
                            'Insurance_Claim_Status': 'Claim Status',
                            'Collected_Amount': 'Collected Amount ($)'
                        }
                    )
                    
                    st.plotly_chart(fig_scatter, use_container_width=True)
                    
                    # Create a table of insurance providers with slowest processing times
                    st.subheader("Insurance Providers with Slowest Processing Times")
                    
                    slow_providers = processing_by_provider.sort_values('Avg_Processing_Days', ascending=False).head(10)
                    slow_providers['Avg_Processing_Days'] = slow_providers['Avg_Processing_Days'].apply(lambda x: f"{x:.1f} days")
                    slow_providers['Median_Processing_Days'] = slow_providers['Median_Processing_Days'].apply(lambda x: f"{x:.1f} days")
                    slow_providers['Paid_Rate'] = slow_providers['Paid_Rate'].apply(lambda x: f"{x:.1f}%")
                    
                    st.dataframe(slow_providers, use_container_width=True)
                else:
                    st.info("No valid claim processing time data available")
            else:
                st.warning("Required insurance claim data columns not available in the dataset")
        
        with insurance_tab2:
            # Insurance Denial Patterns Analysis
            st.subheader("Insurance Denial Patterns Analysis")
            
            # Check if we have denial data
            if 'Insurance_Claim_Status' in filtered_df.columns:
                # Filter for denied claims
                denied_claims = filtered_df[filtered_df['Insurance_Claim_Status'] == 'Denied']
                
                if not denied_claims.empty:
                    # Calculate denial rate by insurance provider
                    denial_by_provider = filtered_df.groupby('Insurance_Provider').agg({
                        'Insurance_Claim_Status': lambda x: (x == 'Denied').mean() * 100,
                        'Charged_Amount': 'sum',
                        'Visit_ID': 'count'
                    }).reset_index()
                    
                    denial_by_provider.columns = ['Insurance_Provider', 'Denial_Rate', 'Total_Charged', 'Claim_Count']
                    
                    # Sort by denial rate
                    denial_by_provider = denial_by_provider.sort_values('Denial_Rate', ascending=False)
                    
                    # Calculate and display key metrics
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        overall_denial_rate = (filtered_df['Insurance_Claim_Status'] == 'Denied').mean() * 100
                        st.metric("Overall Denial Rate", f"{overall_denial_rate:.1f}%")
                    
                    with col2:
                        total_denied_amount = denied_claims['Charged_Amount'].sum()
                        st.metric("Total Denied Amount", f"${total_denied_amount:,.2f}")
                    
                    # Create a bar chart of denial rates by insurance provider
                    fig_denial = px.bar(
                        denial_by_provider,
                        x='Insurance_Provider',
                        y='Denial_Rate',
                        title="Insurance Claim Denial Rates by Provider",
                        labels={
                            'Insurance_Provider': 'Insurance Provider',
                            'Denial_Rate': 'Denial Rate (%)'
                        },
                        color='Denial_Rate',
                        color_continuous_scale=px.colors.sequential.Reds
                    )
                    
                    st.plotly_chart(fig_denial, use_container_width=True)
                    
                    # Analyze denial patterns by procedure
                    if 'Procedure_Description' in denied_claims.columns:
                        denial_by_procedure = denied_claims.groupby('Procedure_Description').agg({
                            'Visit_ID': 'count',
                            'Charged_Amount': 'sum'
                        }).reset_index()
                        
                        denial_by_procedure.columns = ['Procedure_Description', 'Denial_Count', 'Denied_Amount']
                        
                        # Calculate denial rate for each procedure
                        procedure_counts = filtered_df.groupby('Procedure_Description')['Visit_ID'].count().reset_index()
                        procedure_counts.columns = ['Procedure_Description', 'Total_Count']
                        
                        denial_by_procedure = denial_by_procedure.merge(procedure_counts, on='Procedure_Description')
                        denial_by_procedure['Denial_Rate'] = (denial_by_procedure['Denial_Count'] / denial_by_procedure['Total_Count']) * 100
                        
                        # Sort by denial rate
                        denial_by_procedure = denial_by_procedure.sort_values('Denial_Rate', ascending=False)
                        
                        # Create a bar chart of top procedures with highest denial rates
                        fig_procedure_denial = px.bar(
                            denial_by_procedure.head(10),
                            x='Procedure_Description',
                            y='Denial_Rate',
                            title="Top 10 Procedures with Highest Denial Rates",
                            labels={
                                'Procedure_Description': 'Procedure',
                                'Denial_Rate': 'Denial Rate (%)'
                            },
                            color='Denied_Amount',
                            color_continuous_scale=px.colors.sequential.Reds
                        )
                        
                        st.plotly_chart(fig_procedure_denial, use_container_width=True)
                        
                        # Create a table of procedures with highest denial rates
                        st.subheader("Procedures with Highest Denial Rates")
                        
                        display_df = denial_by_procedure.head(10).copy()
                        display_df['Denial_Rate'] = display_df['Denial_Rate'].apply(lambda x: f"{x:.1f}%")
                        display_df['Denied_Amount'] = display_df['Denied_Amount'].apply(lambda x: f"${x:,.2f}")
                        
                        st.dataframe(display_df, use_container_width=True)
                    
                    # Analyze denial patterns by month (if date data is available)
                    if 'Insurance_Claim_Submission_Date' in denied_claims.columns:
                        # Check if the column is datetime type
                        if pd.api.types.is_datetime64_any_dtype(denied_claims['Insurance_Claim_Submission_Date']):
                            denied_claims['Month'] = denied_claims['Insurance_Claim_Submission_Date'].dt.to_period('M')
                            
                            denial_by_month = denied_claims.groupby('Month').agg({
                                'Visit_ID': 'count',
                                'Charged_Amount': 'sum'
                            }).reset_index()
                            
                            denial_by_month.columns = ['Month', 'Denial_Count', 'Denied_Amount']
                            denial_by_month['Month'] = denial_by_month['Month'].astype(str)
                            
                            # Calculate total claims by month
                            if pd.api.types.is_datetime64_any_dtype(filtered_df['Insurance_Claim_Submission_Date']):
                                filtered_df['Month'] = filtered_df['Insurance_Claim_Submission_Date'].dt.to_period('M')
                                total_by_month = filtered_df.groupby('Month')['Visit_ID'].count().reset_index()
                                total_by_month.columns = ['Month', 'Total_Count']
                                total_by_month['Month'] = total_by_month['Month'].astype(str)
                                
                                # Merge and calculate denial rate
                                denial_by_month = denial_by_month.merge(total_by_month, on='Month')
                                denial_by_month['Denial_Rate'] = (denial_by_month['Denial_Count'] / denial_by_month['Total_Count']) * 100
                                
                                # Create a line chart of denial rates over time
                                fig_denial_trend = px.line(
                                    denial_by_month,
                                    x='Month',
                                    y='Denial_Rate',
                                    title="Insurance Claim Denial Rate Trend",
                                    labels={
                                        'Month': 'Month',
                                        'Denial_Rate': 'Denial Rate (%)'
                                    },
                                    markers=True
                                )
                                
                                st.plotly_chart(fig_denial_trend, use_container_width=True)
                            else:
                                st.warning("Insurance claim submission date is not in datetime format")
                        else:
                            st.warning("Insurance claim submission date is not in datetime format")
                else:
                    st.info("No denied claims data available")
            else:
                st.warning("Insurance claim status data not available in the dataset")
    
    # Treatment Plan Analysis
    with tab5:
        st.subheader("Treatment Plan Completion Analysis")
        
        if ('Treatment_Plan_ID' in filtered_df.columns and 
            'Treatment_Plan_Completion_Rate' in filtered_df.columns and 
            'Estimated_Total_Cost' in filtered_df.columns):
            
            # Filter out rows without treatment plan data
            treatment_df = filtered_df[filtered_df['Treatment_Plan_ID'].notna()]
            
            if not treatment_df.empty:
                # Calculate metrics
                treatment_df['Forecasting_Accuracy'] = (treatment_df['Collected_Amount'] / 
                                                     treatment_df['Estimated_Total_Cost']).fillna(0) * 100
                
                # Calculate treatment plan duration where completion date exists
                treatment_df['Plan_Duration_Days'] = None
                mask = (treatment_df['Treatment_Plan_Creation_Date'].notna() & 
                       treatment_df['Treatment_Plan_Completion_Date'].notna())
                
                if any(mask):
                    treatment_df.loc[mask, 'Plan_Duration_Days'] = (
                        treatment_df.loc[mask, 'Treatment_Plan_Completion_Date'] - 
                        treatment_df.loc[mask, 'Treatment_Plan_Creation_Date']
                    ).dt.days
                
                # Create scatter plot of completion rate vs revenue
                st.subheader("Treatment Plan Completion vs. Revenue")
                
                fig1 = px.scatter(
                    treatment_df,
                    x='Treatment_Plan_Completion_Rate',
                    y='Collected_Amount',
                    size='Estimated_Total_Cost',
                    hover_name='Treatment_Plan_ID',
                    title="Revenue vs. Treatment Plan Completion Rate",
                    labels={
                        'Treatment_Plan_Completion_Rate': 'Plan Completion Rate (%)',
                        'Collected_Amount': 'Collected Revenue ($)',
                        'Estimated_Total_Cost': 'Estimated Cost ($)'
                    }
                )
                
                st.plotly_chart(fig1, use_container_width=True)
                
                # Forecasting accuracy analysis
                st.subheader("Treatment Plan Forecasting Accuracy")
                
                # Group by treatment plan ID
                forecasting_df = treatment_df.groupby('Treatment_Plan_ID').agg({
                    'Estimated_Total_Cost': 'first',
                    'Collected_Amount': 'sum',
                    'Treatment_Plan_Completion_Rate': 'first'
                }).reset_index()
                
                # Calculate forecasting accuracy
                forecasting_df['Forecasting_Accuracy'] = (forecasting_df['Collected_Amount'] / 
                                                       forecasting_df['Estimated_Total_Cost']).fillna(0) * 100
                
                # Create bar chart comparing estimated vs actual revenue
                fig2 = px.bar(
                    forecasting_df.head(10),
                    x='Treatment_Plan_ID',
                    y=['Estimated_Total_Cost', 'Collected_Amount'],
                    barmode='group',
                    title="Estimated vs. Actual Revenue",
                    labels={
                        'Treatment_Plan_ID': 'Treatment Plan',
                        'value': 'Amount ($)',
                        'variable': 'Revenue Type'
                    }
                )
                
                # Add completion rate as a line
                fig2.add_trace(
                    go.Scatter(
                        x=forecasting_df.head(10)['Treatment_Plan_ID'],
                        y=forecasting_df.head(10)['Treatment_Plan_Completion_Rate'],
                        mode='lines+markers',
                        name='Completion Rate (%)',
                        yaxis='y2'
                    )
                )
                
                # Set up secondary y-axis
                fig2.update_layout(
                    yaxis2=dict(
                        title='Completion Rate (%)',
                        overlaying='y',
                        side='right',
                        range=[0, 100]
                    ),
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='right',
                        x=1
                    )
                )
                
                st.plotly_chart(fig2, use_container_width=True)
                
                # Treatment plan duration analysis
                st.subheader("Treatment Plan Duration Analysis")
                
                # Filter for completed plans with duration data
                completed_plans = treatment_df[treatment_df['Plan_Duration_Days'].notna()]
                
                if not completed_plans.empty:
                    # Create histogram of plan durations
                    fig3 = px.histogram(
                        completed_plans,
                        x='Plan_Duration_Days',
                        title="Distribution of Treatment Plan Durations",
                        labels={'Plan_Duration_Days': 'Duration (Days)'},
                        marginal='box'
                    )
                    
                    st.plotly_chart(fig3, use_container_width=True)
                    
                    # Create a scatter plot of duration vs completion rate
                    fig4 = px.scatter(
                        completed_plans,
                        x='Plan_Duration_Days',
                        y='Treatment_Plan_Completion_Rate',
                        color='Collected_Amount',
                        size='Estimated_Total_Cost',
                        hover_name='Treatment_Plan_ID',
                        title="Plan Duration vs. Completion Rate",
                        labels={
                            'Plan_Duration_Days': 'Duration (Days)',
                            'Treatment_Plan_Completion_Rate': 'Completion Rate (%)',
                            'Collected_Amount': 'Collected Amount ($)',
                            'Estimated_Total_Cost': 'Estimated Cost ($)'
                        }
                    )
                    
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.info("No completed treatment plan data available")
                
                # Summary statistics in columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    avg_completion = treatment_df['Treatment_Plan_Completion_Rate'].mean()
                    st.metric("Average Completion Rate", f"{avg_completion:.1f}%")
                
                with col2:
                    avg_forecasting = treatment_df['Forecasting_Accuracy'].mean()
                    st.metric("Average Forecasting Accuracy", f"{avg_forecasting:.1f}%")
                
                with col3:
                    if not completed_plans.empty:
                        avg_duration = completed_plans['Plan_Duration_Days'].mean()
                        st.metric("Average Treatment Duration", f"{avg_duration:.1f} days")
                    else:
                        st.metric("Average Treatment Duration", "N/A")
                
                # Treatment Plan Analytics Dashboard
                st.subheader("Treatment Plan Analytics Dashboard")
                
                # Create tabs for different treatment plan analytics
                treatment_tab1, treatment_tab2, treatment_tab3 = st.tabs([
                    "Treatment Success Metrics", 
                    "Treatment Value Analysis",
                    "Treatment Trends"
                ])
                
                with treatment_tab1:
                    # Treatment Success Metrics
                    st.subheader("Treatment Success Metrics")
                    
                    # Calculate success metrics
                    treatment_df['Is_Successful'] = treatment_df['Treatment_Plan_Completion_Rate'] >= 80
                    treatment_df['Is_High_Value'] = treatment_df['Collected_Amount'] > treatment_df['Collected_Amount'].median()
                    
                    # Group by treatment type if available
                    if 'Treatment_Type' in treatment_df.columns:
                        success_by_type = treatment_df.groupby('Treatment_Type').agg({
                    'Treatment_Plan_ID': 'count',
                            'Is_Successful': 'mean',
                            'Collected_Amount': 'sum',
                            'Treatment_Plan_Completion_Rate': 'mean'
                }).reset_index()
                
                        success_by_type['Success_Rate'] = success_by_type['Is_Successful'] * 100
                        success_by_type['Avg_Completion_Rate'] = success_by_type['Treatment_Plan_Completion_Rate']
                        
                        # Create a scatter plot of success rate vs. revenue
                        fig_success = px.scatter(
                            success_by_type,
                            x='Success_Rate',
                            y='Collected_Amount',
                            size='Treatment_Plan_ID',
                            color='Avg_Completion_Rate',
                            hover_name='Treatment_Type',
                            title="Treatment Success Rate vs. Revenue by Treatment Type",
                    labels={
                                'Success_Rate': 'Success Rate (%)',
                                'Collected_Amount': 'Total Revenue ($)',
                                'Treatment_Plan_ID': 'Number of Plans',
                                'Avg_Completion_Rate': 'Avg. Completion Rate (%)'
                            }
                        )
                        
                        st.plotly_chart(fig_success, use_container_width=True)
                    else:
                        # If treatment type is not available, show overall success metrics
                        success_rate = treatment_df['Is_Successful'].mean() * 100
                        high_value_rate = treatment_df['Is_High_Value'].mean() * 100
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Treatment Success Rate", f"{success_rate:.1f}%")
                        
                        with col2:
                            st.metric("High-Value Treatment Rate", f"{high_value_rate:.1f}%")
                        
                        # Create a gauge chart for overall success rate
                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=success_rate,
                            title={'text': "Overall Treatment Success Rate"},
                            gauge={
                                'axis': {'range': [0, 100]},
                                'bar': {'color': "#4CAF50"},
                                'steps': [
                                    {'range': [0, 50], 'color': "#FF9999"},
                                    {'range': [50, 75], 'color': "#FFCC99"},
                                    {'range': [75, 100], 'color': "#99FF99"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': 80
                                }
                            }
                        ))
                        
                        st.plotly_chart(fig_gauge, use_container_width=True)
                
                with treatment_tab2:
                    # Treatment Value Analysis
                    st.subheader("Treatment Value Analysis")
                    
                    # Calculate ROI for treatments
                    treatment_df['ROI'] = (treatment_df['Collected_Amount'] / treatment_df['Estimated_Total_Cost']).fillna(0) * 100
                    
                    # Create a scatter plot of ROI vs. completion rate
                    fig_roi = px.scatter(
                        treatment_df,
                        x='Treatment_Plan_Completion_Rate',
                        y='ROI',
                        color='Collected_Amount',
                        size='Estimated_Total_Cost',
                        hover_name='Treatment_Plan_ID',
                        title="Treatment ROI vs. Completion Rate",
                        labels={
                            'Treatment_Plan_Completion_Rate': 'Completion Rate (%)',
                            'ROI': 'Return on Investment (%)',
                            'Collected_Amount': 'Collected Amount ($)',
                            'Estimated_Total_Cost': 'Estimated Cost ($)'
                        }
                    )
                    
                    # Add a reference line at ROI = 100%
                    fig_roi.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Break-even ROI")
                    
                    st.plotly_chart(fig_roi, use_container_width=True)
                    
                    # Identify high-value treatments
                    high_value_treatments = treatment_df[treatment_df['ROI'] > 150].sort_values('ROI', ascending=False)
                    
                    if not high_value_treatments.empty:
                        st.subheader("High-Value Treatments (ROI > 150%)")
                        
                        # Create a table of high-value treatments
                        high_value_display = high_value_treatments[['Treatment_Plan_ID', 'Treatment_Plan_Completion_Rate', 'ROI', 'Collected_Amount', 'Estimated_Total_Cost']].head(10)
                        high_value_display['Treatment_Plan_Completion_Rate'] = high_value_display['Treatment_Plan_Completion_Rate'].apply(lambda x: f"{x:.1f}%")
                        high_value_display['ROI'] = high_value_display['ROI'].apply(lambda x: f"{x:.1f}%")
                        high_value_display['Collected_Amount'] = high_value_display['Collected_Amount'].apply(lambda x: f"${x:,.2f}")
                        high_value_display['Estimated_Total_Cost'] = high_value_display['Estimated_Total_Cost'].apply(lambda x: f"${x:,.2f}")
                        
                        st.dataframe(high_value_display, use_container_width=True)
                    else:
                        st.info("No treatments with ROI > 150% found")
                
                with treatment_tab3:
                    # Treatment Trends
                    st.subheader("Treatment Trends")
                    
                    # Calculate monthly treatment metrics
                    treatment_df['Month'] = treatment_df['Treatment_Plan_Creation_Date'].dt.to_period('M')
                    
                    monthly_treatments = treatment_df.groupby('Month').agg({
                        'Treatment_Plan_ID': 'count',
                        'Treatment_Plan_Completion_Rate': 'mean',
                        'Collected_Amount': 'sum',
                        'Estimated_Total_Cost': 'sum'
                    }).reset_index()
                    
                    monthly_treatments['Month'] = monthly_treatments['Month'].astype(str)
                    monthly_treatments['ROI'] = (monthly_treatments['Collected_Amount'] / monthly_treatments['Estimated_Total_Cost']).fillna(0) * 100
                    
                    # Create a line chart of treatment volume over time
                    fig_volume = px.line(
                        monthly_treatments,
                        x='Month',
                        y='Treatment_Plan_ID',
                        title="Monthly Treatment Plan Volume",
                        labels={'Treatment_Plan_ID': 'Number of Treatment Plans', 'Month': 'Month'}
                    )
                    
                    st.plotly_chart(fig_volume, use_container_width=True)
                    
                    # Create a multi-line chart of completion rate and ROI over time
                    fig_trends = go.Figure()
                    
                    fig_trends.add_trace(go.Scatter(
                        x=monthly_treatments['Month'],
                        y=monthly_treatments['Treatment_Plan_Completion_Rate'],
                        mode='lines+markers',
                        name='Completion Rate (%)',
                        line=dict(color='#4CAF50')
                    ))
                    
                    fig_trends.add_trace(go.Scatter(
                        x=monthly_treatments['Month'],
                        y=monthly_treatments['ROI'],
                        mode='lines+markers',
                        name='ROI (%)',
                        line=dict(color='#2196F3'),
                        yaxis='y2'
                    ))
                    
                    fig_trends.update_layout(
                        title="Treatment Completion Rate and ROI Trends",
                        xaxis=dict(title="Month"),
                        yaxis=dict(title="Completion Rate (%)", range=[0, 100]),
                        yaxis2=dict(
                            title="ROI (%)",
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
                    
                    st.plotly_chart(fig_trends, use_container_width=True)
                    
                    # Treatment plan aging analysis
                    st.subheader("Treatment Plan Aging Analysis")
                    
                    # Calculate days since creation for each treatment plan
                    treatment_df['Days_Since_Creation'] = (pd.Timestamp.now() - treatment_df['Treatment_Plan_Creation_Date']).dt.days
                    
                    # Create age segments
                    treatment_df['Age_Segment'] = pd.cut(
                        treatment_df['Days_Since_Creation'],
                        bins=[0, 30, 60, 90, 120, float('inf')],
                        labels=['0-30 days', '31-60 days', '61-90 days', '91-120 days', '120+ days']
                    )
                    
                    # Group by age segment
                    aging_data = treatment_df.groupby('Age_Segment').agg({
                        'Treatment_Plan_ID': 'count',
                        'Treatment_Plan_Completion_Rate': 'mean',
                        'Collected_Amount': 'sum'
                    }).reset_index()
                    
                    # Create a bar chart of treatment plans by age
                    fig_aging = px.bar(
                        aging_data,
                        x='Age_Segment',
                        y='Treatment_Plan_ID',
                        color='Treatment_Plan_Completion_Rate',
                        title="Treatment Plans by Age",
                        labels={
                            'Age_Segment': 'Age of Treatment Plan',
                            'Treatment_Plan_ID': 'Number of Plans',
                            'Treatment_Plan_Completion_Rate': 'Avg. Completion Rate (%)'
                        },
                        color_continuous_scale=px.colors.sequential.Viridis
                    )
                    
                    st.plotly_chart(fig_aging, use_container_width=True)
            else:
                st.info("No treatment plan data available in the selected date range")
        else:
            st.warning("Treatment plan data not available in the dataset")
    
    # Show filtered data
    with st.expander("View Filtered Data"):
        st.dataframe(filtered_df)

else:
    st.error("No data available. Please check your data files.")
