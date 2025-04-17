import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import calendar
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt

st.set_page_config(page_title="CFO Financial Dashboard", page_icon="💲", layout="wide")

st.title("Finance & Revenue Insights")

# Load data
@st.cache_data
def load_data():
    try:
        financial_data = pd.read_csv('data/Financial_Data.csv')
        operations_data = pd.read_csv('data/Operations_Data.csv')
        patient_data = pd.read_csv('data/Pat_App_Data.csv')
        staff_data = pd.read_csv('data/Staff_Hours_Data.csv')
        equipment_data = pd.read_csv('data/Equipment_Usage_Data.csv')
        
        # Convert date column in financial data
        if 'Date' in financial_data.columns:
            financial_data['Date'] = pd.to_datetime(financial_data['Date'], errors='coerce')

        # Convert date column in operations data
        if 'Date' in operations_data.columns:
            operations_data['Date'] = pd.to_datetime(operations_data['Date'], errors='coerce')

        # Convert date columns in patient data
        patient_date_cols = ['Date_of_Service', 'Treatment_Plan_Creation_Date', 'Treatment_Plan_Completion_Date', 
                           'Insurance_Claim_Submission_Date', 'Insurance_Claim_Payment_Date']
        for col in patient_date_cols:
            if col in patient_data.columns:
                patient_data[col] = pd.to_datetime(patient_data[col], errors='coerce')

        # Convert date column in staff data
        if 'Date' in staff_data.columns:
            staff_data['Date'] = pd.to_datetime(staff_data['Date'], errors='coerce')

        # Convert date column in equipment data
        if 'Date' in equipment_data.columns:
            equipment_data['Date'] = pd.to_datetime(equipment_data['Date'], errors='coerce')
        
        # Add month-year for grouping
        for df in [financial_data, operations_data, patient_data, staff_data, equipment_data]:
            date_col = 'Date' if 'Date' in df.columns else 'Date_of_Service' if 'Date_of_Service' in df.columns else None
            if date_col:
                df['Month_Year'] = df[date_col].dt.strftime('%Y-%m')
        
        return financial_data, operations_data, patient_data, staff_data, equipment_data
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None, None, None

financial_data, operations_data, patient_data, staff_data, equipment_data = load_data()


# Add this after the load_data() function and its call
def validate_financial_data(df):
    """
    Identifies and handles outliers in financial data.
    
    Parameters:
    df (pandas.DataFrame): The financial data to validate
    
    Returns:
    tuple: (clean_df, anomalies_df, has_anomalies)
    """
    if df is None or df.empty:
        return df, pd.DataFrame(), False
    
    # Create a copy to avoid modifying the original
    df_copy = df.copy()
    
    # Calculate statistical bounds for key metrics
    revenue_q75 = df_copy['Total_Revenue'].quantile(0.75)
    revenue_q25 = df_copy['Total_Revenue'].quantile(0.25)
    revenue_iqr = revenue_q75 - revenue_q25
    revenue_upper_bound = revenue_q75 + 3 * revenue_iqr  # Using 3*IQR for extreme outliers
    
    expense_q75 = df_copy['Total_Expenses'].quantile(0.75)
    expense_q25 = df_copy['Total_Expenses'].quantile(0.25)
    expense_iqr = expense_q75 - expense_q25
    expense_upper_bound = expense_q75 + 3 * expense_iqr
    
    # Flag anomalies
    revenue_anomalies = df_copy['Total_Revenue'] > revenue_upper_bound
    expense_anomalies = df_copy['Total_Expenses'] > expense_upper_bound
    
    # Combine anomalies
    anomalies = revenue_anomalies | expense_anomalies
    
    # Extract and log anomalies
    anomalies_df = df_copy[anomalies].copy()
    clean_df = df_copy[~anomalies].copy()
    
    has_anomalies = len(anomalies_df) > 0
    
    return clean_df, anomalies_df, has_anomalies

# Apply validation after loading data but before filtering
financial_data_clean, financial_anomalies, has_anomalies = validate_financial_data(financial_data)

# Replace the original with the clean data
financial_data = financial_data_clean



if all([financial_data is not None, operations_data is not None, patient_data is not None, 
      staff_data is not None, equipment_data is not None]):
    
     #Sidebar filters
    st.sidebar.header("Filters")

    # Date range filter
    min_date = financial_data['Date'].min().date()
    max_date = financial_data['Date'].max().date()

    # Set default start date to January 1, 2024
    default_start_date = datetime(2022, 1, 1).date()
    # Make sure the default date is within the valid range
    if default_start_date < min_date:
        default_start_date = min_date
    elif default_start_date > max_date:
        default_start_date = min_date

    # Date filter
    start_date = st.sidebar.date_input("Start Date", default_start_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
    
    # Location filter
    locations = ['All'] + sorted(financial_data['Location_Name'].unique().tolist())
    selected_location = st.sidebar.selectbox("Select Location", locations)
    
    # Period filter (Month, Quarter, Year)
    period_options = ['Month', 'Quarter', 'Year', 'All Time']
    selected_period = st.sidebar.selectbox("Select Time Period View", period_options)
    
    # Service line filter
    service_lines = ['All', 'Diagnostic', 'Preventive', 'Restorative', 'Endodontic', 'Periodontic',
                    'Prosthodontic', 'Oral_Surgery', 'Orthodontic', 'Implant', 'Adjunctive']
    selected_service = st.sidebar.selectbox("Select Service Line", service_lines)
    
    # Apply filters to financial data
    filtered_financial = financial_data.copy()
    
    # Date filter
    filtered_financial = filtered_financial[(filtered_financial['Date'].dt.date >= start_date) & 
                                          (filtered_financial['Date'].dt.date <= end_date)]
    
    # Location filter
    if selected_location != 'All':
        filtered_financial = filtered_financial[filtered_financial['Location_Name'] == selected_location]
    
    # Apply the same filters to operations data
    filtered_operations = operations_data[(operations_data['Date'].dt.date >= start_date) & 
                                        (operations_data['Date'].dt.date <= end_date)]
    
    if selected_location != 'All':
        filtered_operations = filtered_operations[filtered_operations['Location_Name'] == selected_location]
    
    # Apply the same filters to patient data
    filtered_patient = patient_data[(patient_data['Date_of_Service'].dt.date >= start_date) & 
                                  (patient_data['Date_of_Service'].dt.date <= end_date)]
    
    if selected_location != 'All':
        filtered_patient = filtered_patient[filtered_patient['Location_Name'] == selected_location]
    
    # Apply the same filters to staff data
    filtered_staff = staff_data[(staff_data['Date'].dt.date >= start_date) & 
                              (staff_data['Date'].dt.date <= end_date)]
    
    if selected_location != 'All':
        filtered_staff = filtered_staff[filtered_staff['Location_ID'].isin(filtered_financial['Location_ID'])]
    
    # Apply the same filters to equipment data
    filtered_equipment = equipment_data[(equipment_data['Date'].dt.date >= start_date) & 
                                      (equipment_data['Date'].dt.date <= end_date)]
    
    if selected_location != 'All':
        filtered_equipment = filtered_equipment[filtered_equipment['Location_ID'].isin(filtered_financial['Location_ID'])]
    
    # Key financial metrics
    total_revenue = filtered_financial['Total_Revenue'].sum()
    total_expenses = filtered_financial['Total_Expenses'].sum()
    total_ebitda = filtered_financial['EBITDA'].sum()
    ebitda_margin = (total_ebitda / total_revenue * 100) if total_revenue > 0 else 0
    avg_collection_rate = filtered_financial['Collection_Rate'].mean()
    avg_dso = filtered_financial['DSO'].mean()
    
    # Display key metrics
    st.markdown("## Key Financial Metrics")

    # Add dynamic location title
    if selected_location == 'All':
        location_title = "All Locations"
    else:
        location_title = selected_location

    # Get the relevant period data based on the selected_period
    if selected_period == 'Year':
        # Get the most recent year's data
        max_year = filtered_financial['Year'].max()
        period_data = filtered_financial[filtered_financial['Year'] == max_year]
        period_title = f"{max_year} (Yearly Data)"
    elif selected_period == 'Quarter':
        # Create a quarter column if it doesn't exist
        if 'Quarter' not in filtered_financial.columns:
            filtered_financial['Quarter'] = filtered_financial['Date'].dt.to_period('Q').astype(str)
        
        # Get the most recent quarter's data
        max_quarter = filtered_financial['Quarter'].max()
        period_data = filtered_financial[filtered_financial['Quarter'] == max_quarter]
        period_title = f"{max_quarter} (Quarterly Data)"
    elif selected_period == 'Month':
        # Get the most recent month's data
        max_month = filtered_financial['Month_Year'].max()
        period_data = filtered_financial[filtered_financial['Month_Year'] == max_month]
        period_title = f"{max_month} (Monthly Data)"
    else:  # All Time
        period_data = filtered_financial.copy()
        period_title = "All Time Data"

    # Calculate metrics based on the filtered period data
    period_total_revenue = period_data['Total_Revenue'].sum()
    period_total_expenses = period_data['Total_Expenses'].sum() if 'Total_Expenses' in period_data.columns else 0
    period_total_ebitda = period_data['EBITDA'].sum() if 'EBITDA' in period_data.columns else 0
    period_ebitda_margin = (period_total_ebitda / period_total_revenue * 100) if period_total_revenue > 0 else 0
    period_avg_collection_rate = period_data['Collection_Rate'].mean() if 'Collection_Rate' in period_data.columns else 0
    period_avg_dso = period_data['DSO'].mean() if 'DSO' in period_data.columns else 0
    period_chair_utilization = period_data['Chair_Utilization'].mean() if 'Chair_Utilization' in period_data.columns else 0

    # Calculate revenue per patient
    if 'Total_Patient_Visits' in period_data.columns:
        total_visits = period_data['Total_Patient_Visits'].sum()
        period_revenue_per_patient = period_total_revenue / total_visits if total_visits > 0 else 0
    else:
        period_revenue_per_patient = 0

    # Include the time period and date range in the subtitle
    date_range = f"{start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}"

    # Create formatted subtitle with location, period, and date range
    st.markdown(f"##### {location_title} | {period_title} | {date_range}")

    # Calculate period-over-period changes based on the selected period
    if selected_period == 'Year' and len(filtered_financial['Year'].unique()) > 1:
        # Get previous year data
        prev_year = max_year - 1
        prev_period_data = filtered_financial[filtered_financial['Year'] == prev_year]
        
        prev_total_revenue = prev_period_data['Total_Revenue'].sum()
        prev_total_ebitda = prev_period_data['EBITDA'].sum() if 'EBITDA' in prev_period_data.columns else 0
        prev_chair_utilization = prev_period_data['Chair_Utilization'].mean() if 'Chair_Utilization' in prev_period_data.columns else 0
        
        if 'Total_Patient_Visits' in prev_period_data.columns:
            prev_visits = prev_period_data['Total_Patient_Visits'].sum()
            prev_revenue_per_patient = prev_total_revenue / prev_visits if prev_visits > 0 else 0
        else:
            prev_revenue_per_patient = 0
        
        # Calculate YoY changes
        revenue_delta = ((period_total_revenue / prev_total_revenue) - 1) * 100 if prev_total_revenue > 0 else None
        ebitda_delta = ((period_total_ebitda / prev_total_ebitda) - 1) * 100 if prev_total_ebitda > 0 else None
        chair_util_delta = ((period_chair_utilization / prev_chair_utilization) - 1) * 100 if prev_chair_utilization > 0 else None
        rpp_delta = ((period_revenue_per_patient / prev_revenue_per_patient) - 1) * 100 if prev_revenue_per_patient > 0 else None
        
        delta_label = "(YoY)"

    elif selected_period == 'Quarter' and len(filtered_financial['Quarter'].unique()) > 1:
        # Get previous quarter data
        quarters = sorted(filtered_financial['Quarter'].unique())
        max_quarter_index = quarters.index(max_quarter)
        
        if max_quarter_index > 0:
            prev_quarter = quarters[max_quarter_index - 1]
            prev_period_data = filtered_financial[filtered_financial['Quarter'] == prev_quarter]
            
            prev_total_revenue = prev_period_data['Total_Revenue'].sum()
            prev_total_ebitda = prev_period_data['EBITDA'].sum() if 'EBITDA' in prev_period_data.columns else 0
            prev_chair_utilization = prev_period_data['Chair_Utilization'].mean() if 'Chair_Utilization' in prev_period_data.columns else 0
            
            if 'Total_Patient_Visits' in prev_period_data.columns:
                prev_visits = prev_period_data['Total_Patient_Visits'].sum()
                prev_revenue_per_patient = prev_total_revenue / prev_visits if prev_visits > 0 else 0
            else:
                prev_revenue_per_patient = 0
            
            # Calculate QoQ changes
            revenue_delta = ((period_total_revenue / prev_total_revenue) - 1) * 100 if prev_total_revenue > 0 else None
            ebitda_delta = ((period_total_ebitda / prev_total_ebitda) - 1) * 100 if prev_total_ebitda > 0 else None
            chair_util_delta = ((period_chair_utilization / prev_chair_utilization) - 1) * 100 if prev_chair_utilization > 0 else None
            rpp_delta = ((period_revenue_per_patient / prev_revenue_per_patient) - 1) * 100 if prev_revenue_per_patient > 0 else None
            
            delta_label = "(QoQ)"
        else:
            revenue_delta = None
            ebitda_delta = None
            chair_util_delta = None
            rpp_delta = None
            delta_label = ""
            
    elif selected_period == 'Month' and len(filtered_financial['Month_Year'].unique()) > 1:
        # Get previous month data
        months = sorted(filtered_financial['Month_Year'].unique())
        max_month_index = months.index(max_month)
        
        if max_month_index > 0:
            prev_month = months[max_month_index - 1]
            prev_period_data = filtered_financial[filtered_financial['Month_Year'] == prev_month]
            
            prev_total_revenue = prev_period_data['Total_Revenue'].sum()
            prev_total_ebitda = prev_period_data['EBITDA'].sum() if 'EBITDA' in prev_period_data.columns else 0
            prev_chair_utilization = prev_period_data['Chair_Utilization'].mean() if 'Chair_Utilization' in prev_period_data.columns else 0
            
            if 'Total_Patient_Visits' in prev_period_data.columns:
                prev_visits = prev_period_data['Total_Patient_Visits'].sum()
                prev_revenue_per_patient = prev_total_revenue / prev_visits if prev_visits > 0 else 0
            else:
                prev_revenue_per_patient = 0
            
            # Calculate MoM changes
            revenue_delta = ((period_total_revenue / prev_total_revenue) - 1) * 100 if prev_total_revenue > 0 else None
            ebitda_delta = ((period_total_ebitda / prev_total_ebitda) - 1) * 100 if prev_total_ebitda > 0 else None
            chair_util_delta = ((period_chair_utilization / prev_chair_utilization) - 1) * 100 if prev_chair_utilization > 0 else None
            rpp_delta = ((period_revenue_per_patient / prev_revenue_per_patient) - 1) * 100 if prev_revenue_per_patient > 0 else None
            
            delta_label = "(MoM)"
        else:
            revenue_delta = None
            ebitda_delta = None
            chair_util_delta = None
            rpp_delta = None
            delta_label = ""
    else:
        # No period-over-period comparison for All Time
        revenue_delta = None
        ebitda_delta = None
        chair_util_delta = None
        rpp_delta = None
        delta_label = ""

    # Display the metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Revenue", f"${period_total_revenue:,.0f}", 
                delta=f"{revenue_delta:.1f}% {delta_label}" if revenue_delta is not None else None,
                delta_color="normal")

    with col2:
        st.metric("EBITDA", f"${period_total_ebitda:,.0f}", 
                delta=f"{ebitda_delta:.1f}% {delta_label}" if ebitda_delta is not None else None,
                delta_color="normal")

    with col3:
        st.metric("Chair Utilization", f"{period_chair_utilization:.1f}%", 
                delta=f"{chair_util_delta:.1f}% {delta_label}" if chair_util_delta is not None else None,
                delta_color="normal")

    with col4:
        st.metric("Revenue Per Patient", f"${period_revenue_per_patient:.0f}", 
                delta=f"{rpp_delta:.1f}% {delta_label}" if rpp_delta is not None else None,
                delta_color="normal")
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Revenue Overview",
        "Expenses",
        "Cash Flow",
        "Accounts Receivable",
        "KPIs",
        "Trends & Forecasting",
        "Procedure Profitability"
    ])
    
# Tab 1: Revenue Overview
    with tab1:
        st.subheader("")
        
        # Revenue Over Time
        st.markdown("### Revenue Trends")
        
        # Group by date/month depending on the period selected
        if selected_period == 'Month':
            revenue_trends = filtered_financial.groupby('Month_Year').agg({
                'Total_Revenue': 'sum',
                'Revenue_MoM_Change': 'mean'
            }).reset_index()
            revenue_trends = revenue_trends.sort_values('Month_Year')
            x_axis = 'Month_Year'
            title_period = "Monthly"
        elif selected_period == 'Quarter':
            filtered_financial['Quarter'] = filtered_financial['Date'].dt.to_period('Q')
            revenue_trends = filtered_financial.groupby('Quarter').agg({
                'Total_Revenue': 'sum',
                # Using MoM change for now, but ideally this would be a quarterly change metric
                'Revenue_YoY_Change': 'mean' if 'Revenue_YoY_Change' in filtered_financial.columns else None
            }).reset_index()
            revenue_trends['Quarter'] = revenue_trends['Quarter'].astype(str)
            revenue_trends = revenue_trends.sort_values('Quarter')
            x_axis = 'Quarter'
            title_period = "Quarterly"
        elif selected_period == 'Year':
            revenue_trends = filtered_financial.groupby('Year').agg({
                'Total_Revenue': 'sum',
                'Revenue_YoY_Change': 'mean'
            }).reset_index()
            revenue_trends = revenue_trends.sort_values('Year')
            x_axis = 'Year'
            title_period = "Annual"
        else:  # All Time
            revenue_trends = filtered_financial.groupby('Month_Year').agg({
                'Total_Revenue': 'sum'
            }).reset_index()
            revenue_trends = revenue_trends.sort_values('Month_Year')
            x_axis = 'Month_Year'
            title_period = "All Time"
        
        if not revenue_trends.empty:
            # Create revenue trend chart
            fig = px.line(
                revenue_trends,
                x=x_axis,
                y='Total_Revenue',
                title=f"{title_period} Revenue Trend",
                labels={
                    x_axis: "Period",
                    'Total_Revenue': 'Revenue ($)'
                },
                markers=True
            )
            
            # Add annotations for growth rates if available
            if selected_period == 'Month' and 'Revenue_MoM_Change' in revenue_trends.columns:
                for i, row in revenue_trends.iterrows():
                    if not pd.isna(row['Revenue_MoM_Change']):
                        fig.add_annotation(
                            x=row[x_axis],
                            y=row['Total_Revenue'],
                            text=f"{row['Revenue_MoM_Change']:.1f}%",
                            showarrow=False,
                            yshift=10
                        )
            elif selected_period == 'Year' and 'Revenue_YoY_Change' in revenue_trends.columns:
                for i, row in revenue_trends.iterrows():
                    if not pd.isna(row['Revenue_YoY_Change']):
                        fig.add_annotation(
                            x=row[x_axis],
                            y=row['Total_Revenue'],
                            text=f"{row['Revenue_YoY_Change']:.1f}%",
                            showarrow=False,
                            yshift=10
                        )
            elif selected_period == 'Quarter' and 'Revenue_YoY_Change' in revenue_trends.columns:
                for i, row in revenue_trends.iterrows():
                    if not pd.isna(row['Revenue_YoY_Change']):
                        fig.add_annotation(
                            x=row[x_axis],
                            y=row['Total_Revenue'],
                            text=f"{row['Revenue_YoY_Change']:.1f}%",
                            showarrow=False,
                            yshift=10
                        )
            
            # Update layout
            fig.update_layout(
                xaxis_title="Period",
                yaxis_title="Revenue ($)",
                yaxis=dict(tickprefix="$")
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No revenue trend data available for the selected filters.")
        
        # Revenue by Service Line
        st.markdown("### Revenue by Service Line")

        # Get service line columns
        service_columns = [
            col for col in filtered_financial.columns 
            if col.startswith('Revenue_') and 
            col != 'Revenue_MoM_Change' and 
            col != 'Revenue_YoY_Change' and 
            col != 'Revenue_Per_Square_Foot' and 
            col != 'Revenue_Per_Patient'
        ]

        if service_columns:
            # Group by year-month and sum service revenue
            service_revenue = filtered_financial.groupby('Month_Year')[service_columns].sum().reset_index()
            
            # Melt the data for plotting
            service_revenue_melted = pd.melt(
                service_revenue,
                id_vars=['Month_Year'],
                value_vars=service_columns,
                var_name='Service_Line',
                value_name='Revenue'
            )
            
            # Create a mapping between original column names and clean display names
            # This ensures consistency between filtering and display
            display_names = {col: col.replace('Revenue_', '').replace('_', ' ') for col in service_columns}
            
            # Create a new column with clean names for display
            service_revenue_melted['Display_Name'] = service_revenue_melted['Service_Line'].map(display_names)

            # Create a copy for the pie chart that won't be filtered
            service_revenue_melted_all = service_revenue_melted.copy()
            
            # Filter by selected service line
            if selected_service != 'All':
                # Find the corresponding original column name
                service_col = f"Revenue_{selected_service}"
                if service_col in service_columns:
                    service_revenue_melted = service_revenue_melted[service_revenue_melted['Service_Line'] == service_col]
            
            # Create stacked bar chart
            fig = px.bar(
                service_revenue_melted,
                x='Month_Year',
                y='Revenue',
                color='Display_Name',  # Use display names for the legend
                title="Revenue by Service Line Over Time",
                labels={
                    'Month_Year': 'Month',
                    'Revenue': 'Revenue ($)',
                    'Display_Name': 'Service Line'
                }
            )

            # Update layout with legend at the bottom
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Revenue ($)",
                yaxis=dict(tickprefix="$"),
                legend=dict(
                    orientation="h",  # Horizontal orientation
                    yanchor="top",    # Anchor to top of the legend box
                    y=-0.15,          # Position below the chart (negative value)
                    xanchor="center", # Center the legend
                    x=0.5             # Center position horizontally
                )
            )

            st.plotly_chart(fig, use_container_width=True)
            
            # Create a pie chart of service distribution
            service_totals = service_revenue_melted_all.groupby('Display_Name')['Revenue'].sum().reset_index()
            service_totals = service_totals.sort_values('Revenue', ascending=False)
            
            fig = px.pie(
                service_totals,
                values='Revenue',
                names='Display_Name',
                title="Revenue Distribution by Service Line",
                hole=0.4
            )
            
            # Add percentage labels
            fig.update_traces(textposition='inside', textinfo='percent+label')
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No service line revenue data available.")
            
        # Revenue by Location - Fix: moved outside the else block to show regardless of service column presence
        if selected_location == 'All':
            st.markdown("### Revenue by Location")
            
            # Group by location
            location_revenue = filtered_financial.groupby('Location_Name')['Total_Revenue'].sum().reset_index()
            location_revenue = location_revenue.sort_values('Total_Revenue', ascending=False)
            
            # Create bar chart
            fig = px.bar(
                location_revenue,
                x='Location_Name',
                y='Total_Revenue',
                color='Total_Revenue',
                title="Total Revenue by Location",
                labels={
                    'Location_Name': 'Location',
                    'Total_Revenue': 'Revenue ($)'
                },
                color_continuous_scale=px.colors.sequential.Blues
            )
            
            # Add revenue labels on bars
            fig.update_traces(texttemplate='$%{y:,.0f}', textposition='outside')
            
            # Update layout
            fig.update_layout(
                xaxis_title="Location",
                yaxis_title="Revenue ($)",
                yaxis=dict(tickprefix="$"),
                coloraxis_showscale=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a heatmap of service lines by location
            if service_columns:  # Only show service by location heatmap if service columns exist
                service_by_location = filtered_financial.groupby('Location_Name')[service_columns].sum().reset_index()
                
                # Melt for heatmap
                service_location_melted = pd.melt(
                    service_by_location,
                    id_vars=['Location_Name'],
                    value_vars=service_columns,
                    var_name='Service_Line',
                    value_name='Revenue'
                )
                
                # Clean service line names
                service_location_melted['Service_Line'] = service_location_melted['Service_Line'].str.replace('Revenue_', '').str.replace('_', ' ')
                
                # Create pivot for heatmap
                service_pivot = service_location_melted.pivot(index='Location_Name', columns='Service_Line', values='Revenue')
                
                # Create heatmap
                fig = px.imshow(
                    service_pivot,
                    text_auto='.2s',
                    aspect="auto",
                    color_continuous_scale=px.colors.sequential.Blues,
                    title="Service Line Revenue by Location"
                )
                
                # Update layout
                fig.update_layout(
                    xaxis_title="Service Line",
                    yaxis_title="Location",
                    coloraxis_colorbar=dict(title="Revenue ($)")
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Revenue KPI Trends
                st.markdown("### Revenue KPI Trends")
                
                # Calculate Revenue KPIs if they don't exist
                if 'Revenue_Per_Patient' not in filtered_financial.columns:
                    filtered_financial['Revenue_Per_Patient'] = filtered_financial['Total_Revenue'] / filtered_financial['Total_Patient_Visits']
                
                if 'Revenue_Per_Chair' not in filtered_financial.columns:
                    filtered_financial['Revenue_Per_Chair'] = filtered_financial['Total_Revenue'] / filtered_financial['Chair_Capacity']
                
                if 'Revenue_Per_Hour' not in filtered_financial.columns:
                    filtered_financial['Revenue_Per_Hour'] = filtered_financial['Total_Revenue'] / filtered_financial['Used_Chair_Hours']
                
                # Group by month and calculate averages
                kpi_trends = filtered_financial.groupby('Month_Year').agg({
                    'Revenue_Per_Patient': 'mean',
                    'Revenue_Per_Chair': 'mean',
                    'Revenue_Per_Hour': 'mean',
                    'Total_Revenue': 'sum',
                    'Total_Patient_Visits': 'sum',
                    'Used_Chair_Hours': 'sum'
                }).reset_index()
                
                # Create three columns for metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    latest_revenue_per_patient = kpi_trends['Revenue_Per_Patient'].iloc[-1]
                    st.metric(
                        "Latest Revenue Per Patient",
                        f"${latest_revenue_per_patient:,.2f}",
                        f"{((latest_revenue_per_patient - kpi_trends['Revenue_Per_Patient'].iloc[-2]) / kpi_trends['Revenue_Per_Patient'].iloc[-2] * 100):.1f}%"
                    )
                
                with col2:
                    latest_revenue_per_chair = kpi_trends['Revenue_Per_Chair'].iloc[-1]
                    st.metric(
                        "Latest Revenue Per Chair",
                        f"${latest_revenue_per_chair:,.2f}",
                        f"{((latest_revenue_per_chair - kpi_trends['Revenue_Per_Chair'].iloc[-2]) / kpi_trends['Revenue_Per_Chair'].iloc[-2] * 100):.1f}%"
                    )
                
                with col3:
                    latest_revenue_per_hour = kpi_trends['Revenue_Per_Hour'].iloc[-1]
                    st.metric(
                        "Latest Revenue Per Hour",
                        f"${latest_revenue_per_hour:,.2f}",
                        f"{((latest_revenue_per_hour - kpi_trends['Revenue_Per_Hour'].iloc[-2]) / kpi_trends['Revenue_Per_Hour'].iloc[-2] * 100):.1f}%"
                    )
                
                # Create multi-line chart for trends
                fig = go.Figure()
                
                # Add traces for each KPI
                fig.add_trace(go.Scatter(
                    x=kpi_trends['Month_Year'],
                    y=kpi_trends['Revenue_Per_Patient'],
                    mode='lines+markers',
                    name='Revenue Per Patient',
                    line=dict(color='#1f77b4', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=kpi_trends['Month_Year'],
                    y=kpi_trends['Revenue_Per_Chair'],
                    mode='lines+markers',
                    name='Revenue Per Chair',
                    line=dict(color='#2ca02c', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=kpi_trends['Month_Year'],
                    y=kpi_trends['Revenue_Per_Hour'],
                    mode='lines+markers',
                    name='Revenue Per Hour',
                    line=dict(color='#ff7f0e', width=2)
                ))
                
                # Update layout
                fig.update_layout(
                    title="Revenue KPI Trends Over Time",
                    xaxis_title="Month",
                    yaxis_title="Amount ($)",
                    yaxis=dict(
                        tickprefix="$",
                        tickformat=",.0f"
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # Tab 2: Expense Analysis
    with tab2:
        st.subheader("Expense Analysis")
        
        # Get expense columns
        expense_columns = [col for col in filtered_financial.columns if col.startswith('Labor_') or 
                         col.startswith('Supplies_') or col == 'Rent_Lease' or 
                         col == 'Utilities' or col == 'Equipment_Costs' or
                         col == 'Marketing' or col == 'Insurance' or
                         col == 'Professional_Fees' or col == 'Lab_Fees' or
                         col == 'Software_IT']
        
        if expense_columns:
            # Group expenses by month
            expense_by_month = filtered_financial.groupby('Month_Year')[expense_columns].sum().reset_index()
            
            # Melt for stacked area chart
            expense_melted = pd.melt(
                expense_by_month,
                id_vars=['Month_Year'],
                value_vars=expense_columns,
                var_name='Expense_Category',
                value_name='Amount'
            )
            
            # Create stacked area chart
            fig = px.area(
                expense_melted,
                x='Month_Year',
                y='Amount',
                color='Expense_Category',
                title="Expense Breakdown Over Time",
                labels={
                    'Month_Year': 'Month',
                    'Amount': 'Expense Amount ($)',
                    'Expense_Category': 'Expense Category'
                }
            )
            
            # Update layout
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Expense Amount ($)",
                yaxis=dict(tickprefix="$"),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.2,  # Position below the chart
                    xanchor="center",
                    x=0.5
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create a pie chart of expense distribution
            expense_totals = expense_melted.groupby('Expense_Category')['Amount'].sum().reset_index()
            expense_totals = expense_totals.sort_values('Amount', ascending=False)
            
            fig = px.pie(
                expense_totals,
                values='Amount',
                names='Expense_Category',
                title="Expense Distribution",
                hole=0.4
            )
            
            # Add percentage labels
            fig.update_traces(textposition='inside', textinfo='percent+label')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Cost percentage trends
            st.markdown("### Cost as Percentage of Revenue")
            
            # Calculate cost percentages if they exist
            cost_cols = ['Labor_Cost_Percentage', 'Supply_Cost_Percentage']
            
            if all(col in filtered_financial.columns for col in cost_cols):
                # Group by month for cost percentages
                cost_pct_trends = filtered_financial.groupby('Month_Year')[cost_cols].mean().reset_index()
                cost_pct_trends = cost_pct_trends.sort_values('Month_Year')
                
                # Create line chart
                fig = go.Figure()
                
                for col in cost_cols:
                    fig.add_trace(go.Scatter(
                        x=cost_pct_trends['Month_Year'],
                        y=cost_pct_trends[col],
                        mode='lines+markers',
                        name=col.replace('_Percentage', '').replace('_', ' ')
                    ))
                
                # Add benchmark lines if you have industry benchmarks
                # fig.add_shape(type="line", x0=cost_pct_trends['Month_Year'].min(), y0=27, 
                #              x1=cost_pct_trends['Month_Year'].max(), y1=27,
                #              line=dict(color="green", width=2, dash="dash"),
                #              name="Labor Cost Benchmark (27%)")
                
                # Update layout
                fig.update_layout(
                    title="Cost Percentages Over Time",
                    xaxis_title="Month",
                    yaxis_title="Percentage of Revenue (%)",
                    yaxis=dict(ticksuffix="%"),
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
                st.info("Cost percentage data not available.")
        else:
            st.info("No expense breakdown data available.")
        
        # Profitability by Location
        if selected_location == 'All':
            st.markdown("### Profitability by Location")
            
            # Group by location
            location_profit = filtered_financial.groupby('Location_Name').agg({
                'Total_Revenue': 'sum',
                'Total_Expenses': 'sum',
                'EBITDA': 'sum',
                'EBITDA_Margin': 'mean'
            }).reset_index()
            
            # Calculate margin if not already in the data
            if 'EBITDA_Margin' not in location_profit.columns:
                location_profit['EBITDA_Margin'] = (location_profit['EBITDA'] / location_profit['Total_Revenue'] * 100).fillna(0)
            
            # Sort by EBITDA
            location_profit = location_profit.sort_values('EBITDA', ascending=False)
            
            # Create bar chart with margin overlay
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=location_profit['Location_Name'],
                y=location_profit['EBITDA'],
                name='EBITDA',
                marker_color='rgba(0, 123, 255, 0.7)'
            ))
            
            fig.add_trace(go.Scatter(
                x=location_profit['Location_Name'],
                y=location_profit['EBITDA_Margin'],
                name='EBITDA Margin (%)',
                mode='lines+markers',
                marker=dict(color='red'),
                line=dict(color='red'),
                yaxis='y2'
            ))
            
            # Update layout
            fig.update_layout(
                title="EBITDA and Margin by Location",
                xaxis_title="Location",
                yaxis=dict(
                    title="EBITDA ($)",
                    tickprefix="$"
                ),
                yaxis2=dict(
                    title="EBITDA Margin (%)",
                    overlaying='y',
                    side='right',
                    range=[0, 100]
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
            
            # Create a table of locations by profitability
            st.markdown("### Location Profitability Rankings")
            
            # Format for display
            display_df = location_profit.copy()
            display_df['EBITDA_Margin'] = display_df['EBITDA_Margin'].apply(lambda x: f"{x:.1f}%")
            display_df['Total_Revenue'] = display_df['Total_Revenue'].apply(lambda x: f"${x:,.0f}")
            display_df['Total_Expenses'] = display_df['Total_Expenses'].apply(lambda x: f"${x:,.0f}")
            display_df['EBITDA'] = display_df['EBITDA'].apply(lambda x: f"${x:,.0f}")
            
            # Rename columns for better readability
            display_df = display_df.rename(columns={
                'Location_Name': 'Location',
                'Total_Revenue': 'Revenue',
                'Total_Expenses': 'Expenses',
                'EBITDA': 'EBITDA',
                'EBITDA_Margin': 'EBITDA Margin'
            })
            
            st.dataframe(display_df, use_container_width=True)
    
    # Tab 3: Cash Flow
    with tab3:
        st.subheader("Cash Flow Analysis")
        
        # Check if we have the necessary data for cash flow projection
        if all(col in filtered_financial.columns for col in ['Total_Revenue', 'Collection_Rate', 'Total_Expenses']):
            # Group by month
            monthly_financials = filtered_financial.groupby('Month_Year').agg({
                'Total_Revenue': 'sum',
                'Collection_Rate': 'mean',
                'Total_Expenses': 'sum',
                'Date': 'first'  # Keep a date for proper time series ordering
            }).reset_index()
            
            # Sort by date
            monthly_financials = monthly_financials.sort_values('Date')
            
            # Calculate historical cash flow
            monthly_financials['Collections'] = monthly_financials['Total_Revenue'] * (monthly_financials['Collection_Rate'] / 100)
            monthly_financials['Cash_Flow'] = monthly_financials['Collections'] - monthly_financials['Total_Expenses']
            
            # Check if we have enough data for forecasting
            if len(monthly_financials) >= 6:  # Need at least 6 months of data for a meaningful forecast
                # Number of periods to forecast
                forecast_periods = 3  # Forecast next 3 months
                
                # Simple forecasting using moving averages
                # For revenue forecast
                window = min(3, len(monthly_financials))  # Use up to 3 months for moving average
                
                revenue_ma = monthly_financials['Total_Revenue'].rolling(window=window).mean().iloc[-1]
                collection_rate_ma = monthly_financials['Collection_Rate'].rolling(window=window).mean().iloc[-1]
                expenses_ma = monthly_financials['Total_Expenses'].rolling(window=window).mean().iloc[-1]
                
                # Create a date range for the forecast
                last_date = monthly_financials['Date'].max()
                forecast_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_periods, freq='MS')
                
                # Create a DataFrame for the forecast
                forecast_df = pd.DataFrame({
                    'Date': forecast_dates,
                    'Month_Year': [d.strftime('%Y-%m') for d in forecast_dates],
                    'Total_Revenue': [revenue_ma] * forecast_periods,
                    'Collection_Rate': [collection_rate_ma] * forecast_periods,
                    'Total_Expenses': [expenses_ma] * forecast_periods,
                    'Type': ['Forecast'] * forecast_periods
                })
                
                # Calculate forecast cash flow
                forecast_df['Collections'] = forecast_df['Total_Revenue'] * (forecast_df['Collection_Rate'] / 100)
                forecast_df['Cash_Flow'] = forecast_df['Collections'] - forecast_df['Total_Expenses']
                
                # Prepare historical data for plotting
                historical_df = pd.DataFrame({
                    'Date': monthly_financials['Date'],
                    'Month_Year': monthly_financials['Month_Year'],
                    'Collections': monthly_financials['Collections'],
                    'Total_Expenses': monthly_financials['Total_Expenses'],
                    'Cash_Flow': monthly_financials['Cash_Flow'],
                    'Type': ['Historical'] * len(monthly_financials)
                })
                
                # Combine historical and forecast data
                combined_df = pd.concat([historical_df, forecast_df[['Date', 'Month_Year', 'Collections', 'Total_Expenses', 'Cash_Flow', 'Type']]])
                
                # Create the cash flow chart
                fig = go.Figure()
                
                # Add collections
                fig.add_trace(go.Bar(
                    x=historical_df['Month_Year'],
                    y=historical_df['Collections'],
                    name='Historical Collections',
                    marker_color='rgba(0, 123, 255, 0.7)'
                ))
                
                fig.add_trace(go.Bar(
                    x=forecast_df['Month_Year'],
                    y=forecast_df['Collections'],
                    name='Forecast Collections',
                    marker_color='rgba(0, 123, 255, 0.3)'
                ))
                
                # Add expenses
                fig.add_trace(go.Bar(
                    x=historical_df['Month_Year'],
                    y=historical_df['Total_Expenses'],
                    name='Historical Expenses',
                    marker_color='rgba(255, 99, 132, 0.7)'
                ))
                
                fig.add_trace(go.Bar(
                    x=forecast_df['Month_Year'],
                    y=forecast_df['Total_Expenses'],
                    name='Forecast Expenses',
                    marker_color='rgba(255, 99, 132, 0.3)'
                ))
                
                # Add cash flow line
                fig.add_trace(go.Scatter(
                    x=combined_df['Month_Year'],
                    y=combined_df['Cash_Flow'],
                    name='Cash Flow',
                    mode='lines+markers',
                    line=dict(color='black', width=2)
                ))
                
                # Update layout
                fig.update_layout(
                    title="Cash Flow Projection",
                    xaxis_title="Month",
                    yaxis=dict(
                        title="Amount ($)",
                        tickprefix="$"
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    barmode='group'
                )
                
                st.plotly_chart(fig, use_container_width=True, key="tab6_cash_flow_projection_1")
                
                # Display cash flow metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Next Month Cash Flow", 
                        f"${forecast_df['Cash_Flow'].iloc[0]:,.0f}",
                        delta=f"{(forecast_df['Cash_Flow'].iloc[0] / historical_df['Cash_Flow'].iloc[-1] - 1) * 100:.1f}%" if historical_df['Cash_Flow'].iloc[-1] != 0 else None
                    )
                
                with col2:
                    st.metric(
                        "3-Month Forecast Cash Flow", 
                        f"${forecast_df['Cash_Flow'].sum():,.0f}"
                    )
                
                with col3:
                    last_3_months = historical_df['Cash_Flow'].tail(3).sum()
                    st.metric(
                        "vs. Last 3 Months", 
                        f"${last_3_months:,.0f}",
                        delta=f"{(forecast_df['Cash_Flow'].sum() / last_3_months - 1) * 100:.1f}%" if last_3_months != 0 else None
                    )
            else:
                st.info("Insufficient historical data for cash flow projection. Need at least 6 months of data.")
        else:
            st.info("Cash flow projection data not available.")
    
    # Tab 4: Accounts Receivable
    with tab4:
        st.subheader("Accounts Receivable Analysis")
        
        # AR Aging Analysis
        st.markdown("### AR Aging Analysis")
        
        # Get AR aging columns
        ar_columns = ['AR_Current', 'AR_31_60', 'AR_61_90', 'AR_91_Plus', 'Total_AR']
        
        if all(col in filtered_financial.columns for col in ar_columns):
            # Get the most recent month's data for AR aging
            latest_month = filtered_financial['Month_Year'].max()
            latest_ar = filtered_financial[filtered_financial['Month_Year'] == latest_month]
            
            # Aggregate AR across all selected locations
            ar_aging = latest_ar[ar_columns].sum()
            
            # Create DataFrame for plotting
            ar_df = pd.DataFrame({
                'Age': ['Current', '31-60 Days', '61-90 Days', '90+ Days'],
                'Amount': [ar_aging['AR_Current'], ar_aging['AR_31_60'], ar_aging['AR_61_90'], ar_aging['AR_91_Plus']]
            })
            
            # Calculate percentages
            ar_df['Percentage'] = ar_df['Amount'] / ar_aging['Total_AR'] * 100
            
            # Create a pie chart
            fig = px.pie(
                ar_df,
                values='Percentage',
                names='Age',
                title="AR Aging Distribution",
                color='Age',
                color_discrete_map={
                    'Current': 'green',
                    '31-60 Days': 'yellow',
                    '61-90 Days': 'orange',
                    '90+ Days': 'red'
                },
                hole=0.4
            )
            
            # Add percentage and amount labels
            fig.update_traces(
                texttemplate='%{percent:.1%}<br>$%{value:.2s}',
                textposition='inside'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate AR metrics
            total_ar = ar_aging['Total_AR']
            ar_over_90 = ar_aging['AR_91_Plus']
            ar_over_90_pct = (ar_over_90 / total_ar * 100) if total_ar > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total AR", f"${total_ar:,.0f}")
            
            with col2:
                st.metric("AR > 90 Days", f"${ar_over_90:,.0f}")
            
            with col3:
                st.metric("AR > 90 Days %", f"{ar_over_90_pct:.1f}%")
            
            # AR Trend Analysis
            st.markdown("### AR Trend Analysis")
            
            # Group by month for AR trend
            ar_trend = filtered_financial.groupby('Month_Year')[ar_columns + ['DSO']].sum().reset_index()
            ar_trend = ar_trend.sort_values('Month_Year')
            
            # Calculate claims trend data
            claims_trend = filtered_financial.groupby('Month_Year').agg({
                'Total_Claims_Submitted': 'sum',
                'Claims_Denied': 'sum'
            }).reset_index()
            
            # Calculate denial rate
            claims_trend['Denial_Rate'] = (claims_trend['Claims_Denied'] / claims_trend['Total_Claims_Submitted'] * 100).fillna(0)
            
            # Create stacked area chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=ar_trend['Month_Year'],
                y=ar_trend['AR_Current'],
                name='Current',
                mode='none',
                stackgroup='one',
                fillcolor='rgba(0, 128, 0, 0.5)'
            ))
            
            fig.add_trace(go.Scatter(
                x=ar_trend['Month_Year'],
                y=ar_trend['AR_31_60'],
                name='31-60 Days',
                mode='none',
                stackgroup='one',
                fillcolor='rgba(255, 255, 0, 0.5)'
            ))
            
            fig.add_trace(go.Scatter(
                x=ar_trend['Month_Year'],
                y=ar_trend['AR_61_90'],
                name='61-90 Days',
                mode='none',
                stackgroup='one',
                fillcolor='rgba(255, 165, 0, 0.5)'
            ))
            
            fig.add_trace(go.Scatter(
                x=ar_trend['Month_Year'],
                y=ar_trend['AR_91_Plus'],
                name='90+ Days',
                mode='none',
                stackgroup='one',
                fillcolor='rgba(255, 0, 0, 0.5)'
            ))
            
            # Add DSO line
            fig.add_trace(go.Scatter(
                x=ar_trend['Month_Year'],
                y=ar_trend['DSO'],
                name='DSO (Days)',
                mode='lines+markers',
                line=dict(color='#0066cc', width=2),
                yaxis='y2'
            ))
            
            # Update layout
            fig.update_layout(
                title="AR Aging and DSO Trends",
                xaxis_title="Month",
                yaxis=dict(
                    title="Number of Claims"
                ),
                yaxis2=dict(
                    title="Avg Days to Payment",
                    overlaying='y',
                    side='right'
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                barmode='group'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display denial rate chart
            fig = px.line(
                claims_trend,
                x='Month_Year',
                y='Denial_Rate',
                title="Insurance Claims Denial Rate Trend",
                labels={
                    'Month_Year': 'Month',
                    'Denial_Rate': 'Denial Rate (%)'
                },
                markers=True
            )
            
            # Add a target line at an acceptable denial rate (e.g., 5%)
            fig.add_shape(
                type="line",
                x0=claims_trend['Month_Year'].min(),
                y0=5,
                x1=claims_trend['Month_Year'].max(),
                y1=5,
                line=dict(color="red", width=2, dash="dash")
            )
            
            # Update layout
            fig.update_layout(
                xaxis_title="Month",
                yaxis=dict(
                    title="Denial Rate (%)",
                    ticksuffix="%"
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insurance claims data not available.")
        
        # Payor Mix Analysis if payor columns exist
        payor_cols = [col for col in filtered_financial.columns if col.startswith('Payor_')]
        
        if payor_cols:
            st.markdown("### Payor Mix Analysis")
            
            # Get the most recent month's data for payor mix
            latest_month = filtered_financial['Month_Year'].max()
            latest_payor = filtered_financial[filtered_financial['Month_Year'] == latest_month]
            
            # Aggregate payor data across all selected locations
            payor_mix = latest_payor[payor_cols].sum()
            
            # Create DataFrame for plotting
            payor_df = pd.DataFrame({
                'Payor': [col.replace('Payor_', '').replace('_', ' ') for col in payor_cols],
                'Amount': [payor_mix[col] for col in payor_cols]
            })
            
            # Calculate percentages
            payor_df['Percentage'] = payor_df['Amount'] / payor_df['Amount'].sum() * 100
            
            # Sort by amount
            payor_df = payor_df.sort_values('Amount', ascending=False)
            
            # Create a pie chart
            fig = px.pie(
                payor_df,
                values='Amount',
                names='Payor',
                title="Payor Mix Distribution",
                hole=0.4
            )
            
            # Add percentage and amount labels
            fig.update_traces(
                texttemplate='%{percent:.1%}<br>$%{value:.2s}',
                textposition='inside'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Collection Rate by Payor Analysis
            if 'Collection_Rate' in filtered_financial.columns and patient_data is not None:
                st.markdown("### Collection Rate by Payor")
                
                # Filter patient data for the same date range and location
                filtered_patient_data = patient_data[
                    (patient_data['Date_of_Service'].dt.date >= start_date) & 
                    (patient_data['Date_of_Service'].dt.date <= end_date)
                ]
                
                if selected_location != 'All':
                    filtered_patient_data = filtered_patient_data[filtered_patient_data['Location_Name'] == selected_location]
                
                # Group by insurance provider and calculate collection rate
                payor_collection = filtered_patient_data.groupby('Insurance_Provider').agg({
                    'Charged_Amount': 'sum',
                    'Amount_Paid': 'sum'
                }).reset_index()
                
                # Calculate collection rate for each payor
                payor_collection['Collection_Rate'] = (payor_collection['Amount_Paid'] / 
                                                    payor_collection['Charged_Amount'] * 100).fillna(0)
                
                # Sort by collection rate
                payor_collection = payor_collection.sort_values('Collection_Rate', ascending=False)
                
                # Create bar chart
                fig = px.bar(
                    payor_collection,
                    x='Insurance_Provider',
                    y='Collection_Rate',
                    title="Collection Rate by Insurance Provider",
                    labels={
                        'Insurance_Provider': 'Insurance Provider',
                        'Collection_Rate': 'Collection Rate (%)'
                    },
                    color='Collection_Rate',
                    color_continuous_scale=px.colors.sequential.Blues
                )
                
                # Add a target line for benchmark collection rate (e.g., 95%)
                fig.add_shape(
                    type="line",
                    x0=-0.5,
                    y0=95,
                    x1=len(payor_collection) - 0.5,
                    y1=95,
                    line=dict(color="red", width=2, dash="dash")
                )
                
                # Update layout
                fig.update_layout(
                    xaxis_title="Insurance Provider",
                    yaxis=dict(
                        title="Collection Rate (%)",
                        ticksuffix="%"
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Also show as a table with more details
                st.subheader("Collection Details by Payor")
                
                # Add more metrics to the table
                payor_collection['Charged_Amount'] = payor_collection['Charged_Amount'].map('${:,.2f}'.format)
                payor_collection['Amount_Paid'] = payor_collection['Amount_Paid'].map('${:,.2f}'.format)
                payor_collection['Collection_Rate'] = payor_collection['Collection_Rate'].map('{:.1f}%'.format)
                
                # Rename columns for display
                payor_collection = payor_collection.rename(columns={
                    'Insurance_Provider': 'Payor',
                    'Charged_Amount': 'Amount Billed',
                    'Amount_Paid': 'Amount Collected',
                    'Collection_Rate': 'Collection Rate'
                })
                
                st.dataframe(payor_collection)
            else:
                st.info("Patient data not available for collection rate analysis.")
        else:
            st.info("Payor mix data not available.")
    
    # Tab 5: Key Performance Metrics
    with tab5:
        st.subheader("")
        
        # KPI Trends
        st.markdown("### Financial KPI Trends")
        
        # Calculate financial KPIs
        if 'EBITDA_Margin' not in filtered_financial.columns:
            filtered_financial['EBITDA_Margin'] = (filtered_financial['EBITDA'] / filtered_financial['Total_Revenue'] * 100)
        
        if 'Operating_Margin' not in filtered_financial.columns:
            filtered_financial['Operating_Margin'] = ((filtered_financial['Total_Revenue'] - filtered_financial['Total_Expenses']) / filtered_financial['Total_Revenue'] * 100)
        
        # Group by month and calculate averages
        kpi_trends = filtered_financial.groupby('Month_Year').agg({
            'EBITDA_Margin': 'mean',
            'Operating_Margin': 'mean',
            'Collection_Rate': 'mean',
            'DSO': 'mean'
        }).reset_index()
        
        # Create four columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            latest_ebitda_margin = kpi_trends['EBITDA_Margin'].iloc[-1]
            st.metric(
                "Latest EBITDA Margin",
                f"{latest_ebitda_margin:.1f}%",
                f"{((latest_ebitda_margin - kpi_trends['EBITDA_Margin'].iloc[-2]) / kpi_trends['EBITDA_Margin'].iloc[-2] * 100):.1f}%"
            )
        
        with col2:
            latest_operating_margin = kpi_trends['Operating_Margin'].iloc[-1]
            st.metric(
                "Latest Operating Margin",
                f"{latest_operating_margin:.1f}%",
                f"{((latest_operating_margin - kpi_trends['Operating_Margin'].iloc[-2]) / kpi_trends['Operating_Margin'].iloc[-2] * 100):.1f}%"
            )
        
        with col3:
            latest_collection_rate = kpi_trends['Collection_Rate'].iloc[-1]
            st.metric(
                "Latest Collection Rate",
                f"{latest_collection_rate:.1f}%",
                f"{((latest_collection_rate - kpi_trends['Collection_Rate'].iloc[-2]) / kpi_trends['Collection_Rate'].iloc[-2] * 100):.1f}%"
            )
        
        with col4:
            latest_dso = kpi_trends['DSO'].iloc[-1]
            st.metric(
                "Latest DSO",
                f"{latest_dso:.1f} days",
                f"{((latest_dso - kpi_trends['DSO'].iloc[-2]) / kpi_trends['DSO'].iloc[-2] * 100):.1f}%"
            )
        
        # Create multi-line chart for trends
        fig = go.Figure()
        
        # Add traces for each KPI
        fig.add_trace(go.Scatter(
            x=kpi_trends['Month_Year'],
            y=kpi_trends['EBITDA_Margin'],
            mode='lines+markers',
            name='EBITDA Margin',
            line=dict(color='#1f77b4', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=kpi_trends['Month_Year'],
            y=kpi_trends['Operating_Margin'],
            mode='lines+markers',
            name='Operating Margin',
            line=dict(color='#2ca02c', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=kpi_trends['Month_Year'],
            y=kpi_trends['Collection_Rate'],
            mode='lines+markers',
            name='Collection Rate',
            line=dict(color='#ff7f0e', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=kpi_trends['Month_Year'],
            y=kpi_trends['DSO'],
            mode='lines+markers',
            name='DSO',
            line=dict(color='#d62728', width=2)
        ))
        
        # Update layout
        fig.update_layout(
            title="Financial KPI Trends Over Time",
            xaxis_title="Month",
            yaxis_title="Percentage (%)",
            yaxis=dict(
                ticksuffix="%"
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tab 6: Trends & Forecasting
    with tab6:
        st.subheader("Trends & Forecasting")
        
        # Revenue Forecasting
        st.markdown("### Revenue Forecast")
        
        # Get monthly revenue data
        if 'Total_Revenue' in filtered_financial.columns:
            # Group by month
            monthly_revenue = filtered_financial.groupby('Month_Year').agg({
                'Total_Revenue': 'sum',
                'Date': 'first'  # Keep a date for proper time series ordering
            }).reset_index()
            
            # Sort by date
            monthly_revenue = monthly_revenue.sort_values('Date')
            
            # Check if we have enough data for forecasting
            if len(monthly_revenue) >= 6:  # Need at least 6 months of data for a meaningful forecast
                # Create time series for forecasting
                revenue_ts = monthly_revenue.set_index('Date')['Total_Revenue']
                
                # Number of periods to forecast
                forecast_periods = 3  # Forecast next 3 months
                
                # Simple forecasting using moving average
                # For a simple moving average forecast
                window = min(3, len(revenue_ts))  # Use up to 3 months for moving average
                ma_forecast = revenue_ts.rolling(window=window).mean().iloc[-1]
                
                # Create a date range for the forecast
                last_date = revenue_ts.index.max()
                forecast_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_periods, freq='MS')
                
                # Create a DataFrame for the forecast
                forecast_df = pd.DataFrame({
                    'Date': forecast_dates,
                    'Month_Year': [d.strftime('%Y-%m') for d in forecast_dates],
                    'Forecast': [ma_forecast] * forecast_periods,
                    'Type': ['Forecast'] * forecast_periods
                })
                
                # Prepare historical data for plotting
                historical_df = pd.DataFrame({
                    'Date': monthly_revenue['Date'],
                    'Month_Year': monthly_revenue['Month_Year'],
                    'Forecast': monthly_revenue['Total_Revenue'],
                    'Type': ['Historical'] * len(monthly_revenue)
                })
                
                # Combine historical and forecast data
                combined_df = pd.concat([historical_df, forecast_df])
                
                # Create the forecast chart
                fig = px.line(
                    combined_df,
                    x='Month_Year',
                    y='Forecast',
                    color='Type',
                    title="Revenue Forecast",
                    labels={
                        'Month_Year': 'Month',
                        'Forecast': 'Revenue ($)'
                    },
                    markers=True,
                    color_discrete_map={
                        'Historical': 'blue',
                        'Forecast': 'red'
                    }
                )
                
                # Add confidence interval for forecast (simplistic approach)
                for i, row in forecast_df.iterrows():
                    fig.add_shape(
                        type="rect",
                        x0=i,
                        y0=row['Forecast'] * 0.9,  # Lower bound (10% below forecast)
                        x1=i + 1,
                        y1=row['Forecast'] * 1.1,  # Upper bound (10% above forecast)
                        line=dict(width=0),
                        fillcolor="rgba(255, 0, 0, 0.2)"
                    )
                
                # Update layout
                fig.update_layout(
                    xaxis_title="Month",
                    yaxis=dict(
                        title="Revenue ($)",
                        tickprefix="$"
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display forecast metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Next Month Forecast", 
                        f"${forecast_df['Forecast'].iloc[0]:,.0f}",
                        delta=f"{(forecast_df['Forecast'].iloc[0] / historical_df['Forecast'].iloc[-1] - 1) * 100:.1f}%"
                    )
                
                with col2:
                    st.metric(
                        "3-Month Forecast Total", 
                        f"${forecast_df['Forecast'].sum():,.0f}"
                    )
                
                with col3:
                    last_3_months = historical_df['Forecast'].tail(3).sum()
                    st.metric(
                        "vs. Last 3 Months", 
                        f"${last_3_months:,.0f}",
                        delta=f"{(forecast_df['Forecast'].sum() / last_3_months - 1) * 100:.1f}%"
                    )
            else:
                st.info("Insufficient historical data for forecasting. Need at least 6 months of data.")
        else:
            st.info("Revenue data not available for forecasting.")
        
        # Cash Flow Projection
        st.markdown("### Cash Flow Projection")
        
        # Check if we have the necessary data for cash flow projection
        if all(col in filtered_financial.columns for col in ['Total_Revenue', 'Collection_Rate', 'Total_Expenses']):
            # Group by month
            monthly_financials = filtered_financial.groupby('Month_Year').agg({
                'Total_Revenue': 'sum',
                'Collection_Rate': 'mean',
                'Total_Expenses': 'sum',
                'Date': 'first'  # Keep a date for proper time series ordering
            }).reset_index()
            
            # Sort by date
            monthly_financials = monthly_financials.sort_values('Date')
            
            # Calculate historical cash flow
            monthly_financials['Collections'] = monthly_financials['Total_Revenue'] * (monthly_financials['Collection_Rate'] / 100)
            monthly_financials['Cash_Flow'] = monthly_financials['Collections'] - monthly_financials['Total_Expenses']
            
            # Check if we have enough data for forecasting
            if len(monthly_financials) >= 6:  # Need at least 6 months of data for a meaningful forecast
                # Number of periods to forecast
                forecast_periods = 3  # Forecast next 3 months
                
                # Simple forecasting using moving averages
                # For revenue forecast
                window = min(3, len(monthly_financials))  # Use up to 3 months for moving average
                
                revenue_ma = monthly_financials['Total_Revenue'].rolling(window=window).mean().iloc[-1]
                collection_rate_ma = monthly_financials['Collection_Rate'].rolling(window=window).mean().iloc[-1]
                expenses_ma = monthly_financials['Total_Expenses'].rolling(window=window).mean().iloc[-1]
                
                # Create a date range for the forecast
                last_date = monthly_financials['Date'].max()
                forecast_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_periods, freq='MS')
                
                # Create a DataFrame for the forecast
                forecast_df = pd.DataFrame({
                    'Date': forecast_dates,
                    'Month_Year': [d.strftime('%Y-%m') for d in forecast_dates],
                    'Total_Revenue': [revenue_ma] * forecast_periods,
                    'Collection_Rate': [collection_rate_ma] * forecast_periods,
                    'Total_Expenses': [expenses_ma] * forecast_periods,
                    'Type': ['Forecast'] * forecast_periods
                })
                
                # Calculate forecast cash flow
                forecast_df['Collections'] = forecast_df['Total_Revenue'] * (forecast_df['Collection_Rate'] / 100)
                forecast_df['Cash_Flow'] = forecast_df['Collections'] - forecast_df['Total_Expenses']
                
                # Prepare historical data for plotting
                historical_df = pd.DataFrame({
                    'Date': monthly_financials['Date'],
                    'Month_Year': monthly_financials['Month_Year'],
                    'Collections': monthly_financials['Collections'],
                    'Total_Expenses': monthly_financials['Total_Expenses'],
                    'Cash_Flow': monthly_financials['Cash_Flow'],
                    'Type': ['Historical'] * len(monthly_financials)
                })
                
                # Combine historical and forecast data
                combined_df = pd.concat([historical_df, forecast_df[['Date', 'Month_Year', 'Collections', 'Total_Expenses', 'Cash_Flow', 'Type']]])
                
                # Create the cash flow chart
                fig = go.Figure()
                
                # Add collections
                fig.add_trace(go.Bar(
                    x=historical_df['Month_Year'],
                    y=historical_df['Collections'],
                    name='Historical Collections',
                    marker_color='rgba(0, 123, 255, 0.7)'
                ))
                
                fig.add_trace(go.Bar(
                    x=forecast_df['Month_Year'],
                    y=forecast_df['Collections'],
                    name='Forecast Collections',
                    marker_color='rgba(0, 123, 255, 0.3)'
                ))
                
                # Add expenses
                fig.add_trace(go.Bar(
                    x=historical_df['Month_Year'],
                    y=historical_df['Total_Expenses'],
                    name='Historical Expenses',
                    marker_color='rgba(255, 99, 132, 0.7)'
                ))
                
                fig.add_trace(go.Bar(
                    x=forecast_df['Month_Year'],
                    y=forecast_df['Total_Expenses'],
                    name='Forecast Expenses',
                    marker_color='rgba(255, 99, 132, 0.3)'
                ))
                
                # Add cash flow line
                fig.add_trace(go.Scatter(
                    x=combined_df['Month_Year'],
                    y=combined_df['Cash_Flow'],
                    name='Cash Flow',
                    mode='lines+markers',
                    line=dict(color='black', width=2)
                ))
                
                # Update layout
                fig.update_layout(
                    title="Cash Flow Projection",
                    xaxis_title="Month",
                    yaxis=dict(
                        title="Amount ($)",
                        tickprefix="$"
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    barmode='group'
                )
                
                st.plotly_chart(fig, use_container_width=True, key="tab3_cash_flow_projection_1")
                
                # Display cash flow metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Next Month Cash Flow", 
                        f"${forecast_df['Cash_Flow'].iloc[0]:,.0f}",
                        delta=f"{(forecast_df['Cash_Flow'].iloc[0] / historical_df['Cash_Flow'].iloc[-1] - 1) * 100:.1f}%" if historical_df['Cash_Flow'].iloc[-1] != 0 else None
                    )
                
                with col2:
                    st.metric(
                        "3-Month Forecast Cash Flow", 
                        f"${forecast_df['Cash_Flow'].sum():,.0f}"
                    )
                
                with col3:
                    last_3_months = historical_df['Cash_Flow'].tail(3).sum()
                    st.metric(
                        "vs. Last 3 Months", 
                        f"${last_3_months:,.0f}",
                        delta=f"{(forecast_df['Cash_Flow'].sum() / last_3_months - 1) * 100:.1f}%" if last_3_months != 0 else None
                    )
            else:
                st.info("Insufficient historical data for cash flow projection. Need at least 6 months of data.")
        else:
            st.info("Cash flow projection data not available.")
        
        # Financial What-If Scenarios
        st.markdown("### Financial What-If Scenarios")
        
        # Create sliders for scenario modeling
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Revenue Scenarios")
            
            # Get the most recent month's data
            latest_month = filtered_financial['Month_Year'].max()
            latest_data = filtered_financial[filtered_financial['Month_Year'] == latest_month]
            
            # Calculate averages for the baseline
            avg_revenue = latest_data['Total_Revenue'].mean()
            
            # Sliders for revenue scenarios
            revenue_change = st.slider(
                "Revenue Change (%)", 
                min_value=-20.0, 
                max_value=20.0, 
                value=0.0, 
                step=0.5,
                format="%.1f%%"
            )
            
            # If we have service line data, allow adjusting the mix
            service_columns = [
                col for col in filtered_financial.columns 
                if col.startswith('Revenue_') and 
                col != 'Revenue_MoM_Change' and 
                col != 'Revenue_YoY_Change' and 
                col != 'Revenue_Per_Square_Foot' and 
                col != 'Revenue_Per_Patient'
            ]
            
            if service_columns:
                st.subheader("Service Mix Adjustments")
                
                # Calculate service percentages
                service_totals = latest_data[service_columns].sum()
                service_percentages = (service_totals / service_totals.sum() * 100).to_dict()
                
                # Create sliders for each service line
                service_mix_changes = {}
                for col in service_columns:
                    service_name = col.replace('Revenue_', '').replace('_', ' ')
                    default_pct = round(service_percentages[col] / 0.5) * 0.5  # Round to nearest 0.5
                    min_val = max(0.0, round((default_pct - 10.0) / 0.5) * 0.5)  # Round down to nearest 0.5
                    max_val = min(100.0, round((default_pct + 10.0) / 0.5) * 0.5)  # Round up to nearest 0.5
                    service_mix_changes[col] = st.slider(
                        f"{service_name} Mix (%)", 
                        min_value=min_val,
                        max_value=max_val,
                        value=default_pct,
                        step=0.5,
                        format="%.1f%%"
                    )
        
        with col2:
            st.subheader("Cost Scenarios")
            
            # Calculate averages for the baseline
            avg_expenses = latest_data['Total_Expenses'].mean() if 'Total_Expenses' in latest_data.columns else 0
            avg_labor_pct = latest_data['Labor_Cost_Percentage'].mean() if 'Labor_Cost_Percentage' in latest_data.columns else 0
            avg_supply_pct = latest_data['Supply_Cost_Percentage'].mean() if 'Supply_Cost_Percentage' in latest_data.columns else 0
            
            # Sliders for cost scenarios
            if 'Labor_Cost_Percentage' in latest_data.columns:
                labor_change = st.slider(
                    "Labor Cost Change (%)", 
                    min_value=-10.0, 
                    max_value=10.0, 
                    value=0.0, 
                    step=0.5,
                    format="%.1f%%"
                )
            else:
                labor_change = 0.0
            
            if 'Supply_Cost_Percentage' in latest_data.columns:
                supply_change = st.slider(
                    "Supply Cost Change (%)", 
                    min_value=-10.0, 
                    max_value=10.0, 
                    value=0.0, 
                    step=0.5,
                    format="%.1f%%"
                )
            else:
                supply_change = 0.0
            
            if 'Collection_Rate' in latest_data.columns:
                avg_collection_rate = latest_data['Collection_Rate'].mean()
                collection_change = st.slider(
                    "Collection Rate Change (%)", 
                    min_value=-10.0, 
                    max_value=10.0, 
                    value=0.0, 
                    step=0.5,
                    format="%.1f%%"
                )
            else:
                collection_change = 0.0
                avg_collection_rate = 0.0
        
        # Display scenario results
        st.subheader("Scenario Impact")
        
        # Calculate scenario impacts
        new_revenue = avg_revenue * (1 + revenue_change / 100)
        
        # Calculate new expenses based on changes
        if 'Total_Expenses' in latest_data.columns:
            labor_portion = avg_expenses * (avg_labor_pct / 100) if avg_labor_pct > 0 else 0
            supply_portion = avg_expenses * (avg_supply_pct / 100) if avg_supply_pct > 0 else 0
            other_expenses = avg_expenses - labor_portion - supply_portion
            
            new_labor = labor_portion * (1 + labor_change / 100)
            new_supplies = supply_portion * (1 + supply_change / 100)
            new_expenses = new_labor + new_supplies + other_expenses
        else:
            new_expenses = 0
        
        # Calculate new EBITDA
        new_collections = new_revenue * ((avg_collection_rate + collection_change) / 100) if avg_collection_rate > 0 else new_revenue
        new_ebitda = new_collections - new_expenses
        new_ebitda_margin = (new_ebitda / new_revenue * 100) if new_revenue > 0 else 0
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Scenario Revenue", 
                f"${new_revenue:,.0f}",
                delta=f"{revenue_change:.1f}%"
            )
        
        with col2:
            st.metric(
                "Scenario EBITDA", 
                f"${new_ebitda:,.0f}",
                delta=f"{(new_ebitda / avg_revenue - (avg_revenue - avg_expenses) / avg_revenue) * 100:.1f}%" if avg_revenue > 0 else None
            )
        
        with col3:
            st.metric(
                "Scenario EBITDA Margin", 
                f"{new_ebitda_margin:.1f}%",
                delta=f"{new_ebitda_margin - ((avg_revenue - avg_expenses) / avg_revenue * 100):.1f}%" if avg_revenue > 0 else None
            )
        
        # Visual comparison of baseline vs. scenario
        baseline_values = [avg_revenue, avg_revenue - avg_expenses, (avg_revenue - avg_expenses) / avg_revenue * 100 if avg_revenue > 0 else 0]
        scenario_values = [new_revenue, new_ebitda, new_ebitda_margin]
        
        # Create comparison chart
        comparison_df = pd.DataFrame({
            'Metric': ['Revenue', 'EBITDA', 'EBITDA Margin (%)'],
            'Baseline': baseline_values,
            'Scenario': scenario_values
        })
        
        # Create bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=comparison_df['Metric'],
            y=comparison_df['Baseline'],
            name='Baseline',
            marker_color='rgba(0, 123, 255, 0.7)'
        ))
        
        fig.add_trace(go.Bar(
            x=comparison_df['Metric'],
            y=comparison_df['Scenario'],
            name='Scenario',
            marker_color='rgba(40, 167, 69, 0.7)'
        ))
        
        # Update layout
        fig.update_layout(
            title="Baseline vs. Scenario Comparison",
            xaxis_title="Metric",
            yaxis=dict(
                title="Value",
                tickprefix="$" if True else ""
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tab 7: Procedure Profitability Analysis
    with tab7:
        st.header("Procedure Profitability Analysis")
        
        # Calculate procedure revenue metrics
        procedure_revenue = pd.DataFrame({
            'Procedure': ['Diagnostic', 'Preventive', 'Restorative', 'Endodontic', 
                         'Periodontic', 'Prosthodontic', 'Oral Surgery', 'Orthodontic',
                         'Implant', 'Adjunctive'],
            'Billed_Revenue': [
                filtered_financial['Revenue_Diagnostic'].sum(),
                filtered_financial['Revenue_Preventive'].sum(),
                filtered_financial['Revenue_Restorative'].sum(),
                filtered_financial['Revenue_Endodontic'].sum(),
                filtered_financial['Revenue_Periodontic'].sum(),
                filtered_financial['Revenue_Prosthodontic'].sum(),
                filtered_financial['Revenue_Oral_Surgery'].sum(),
                filtered_financial['Revenue_Orthodontic'].sum(),
                filtered_financial['Revenue_Implant'].sum(),
                filtered_financial['Revenue_Adjunctive'].sum()
            ]
        })
        
        # Calculate collected revenue (using collection rate)
        procedure_revenue['Collected_Revenue'] = procedure_revenue['Billed_Revenue'] * filtered_financial['Collection_Rate'].mean()
        procedure_revenue['Profitability'] = procedure_revenue['Collected_Revenue'] - procedure_revenue['Billed_Revenue']
        
        # Create visualization
        fig = go.Figure()
        
        # Add billed revenue bars
        fig.add_trace(go.Bar(
            name='Billed Revenue',
            x=procedure_revenue['Procedure'],
            y=procedure_revenue['Billed_Revenue'],
            marker_color='rgb(55, 83, 109)'
        ))
        
        # Add collected revenue bars
        fig.add_trace(go.Bar(
            name='Collected Revenue',
            x=procedure_revenue['Procedure'],
            y=procedure_revenue['Collected_Revenue'],
            marker_color='rgb(26, 118, 255)'
        ))
        
        # Update layout
        fig.update_layout(
            title='Procedure Revenue Analysis',
            xaxis_title='Procedure Type',
            yaxis_title='Revenue ($)',
            barmode='group',
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, key="tab7_procedure_revenue_1")
        
        # Display profitability metrics
        st.subheader("Top 3 Most Profitable Procedures")
        top_profitable = procedure_revenue.nlargest(3, 'Collected_Revenue')
        
        # Create three columns for horizontal layout
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                top_profitable.iloc[0]['Procedure'],
                f"${top_profitable.iloc[0]['Collected_Revenue']:,.2f}",
                f"${top_profitable.iloc[0]['Billed_Revenue']:,.2f} billed"
            )
        
        with col2:
            st.metric(
                top_profitable.iloc[1]['Procedure'],
                f"${top_profitable.iloc[1]['Collected_Revenue']:,.2f}",
                f"${top_profitable.iloc[1]['Billed_Revenue']:,.2f} billed"
            )
        
        with col3:
            st.metric(
                top_profitable.iloc[2]['Procedure'],
                f"${top_profitable.iloc[2]['Collected_Revenue']:,.2f}",
                f"${top_profitable.iloc[2]['Billed_Revenue']:,.2f} billed"
            )
    
    # Footer with download options
    st.subheader("Data Download")
    
    # Create tabs for different data downloads
    tab1, tab2 = st.tabs(["Financial Data", "Key Metrics"])
    
    with tab1:
        st.dataframe(filtered_financial, height=300)
        csv_financial = filtered_financial.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Financial Data as CSV",
            data=csv_financial,
            file_name="filtered_financial_data.csv",
            mime="text/csv"
        )
    
    with tab2:
        # Create a summary metrics table
        metrics_dict = {
            'Month': filtered_financial['Month_Year'].unique().tolist(),
            'Total Revenue': [filtered_financial[filtered_financial['Month_Year'] == m]['Total_Revenue'].sum() for m in filtered_financial['Month_Year'].unique()],
            'EBITDA': [filtered_financial[filtered_financial['Month_Year'] == m]['EBITDA'].sum() for m in filtered_financial['Month_Year'].unique()],
            'EBITDA Margin (%)': [filtered_financial[filtered_financial['Month_Year'] == m]['EBITDA_Margin'].mean() for m in filtered_financial['Month_Year'].unique()],
            'Collection Rate (%)': [filtered_financial[filtered_financial['Month_Year'] == m]['Collection_Rate'].mean() for m in filtered_financial['Month_Year'].unique()],
            'DSO': [filtered_financial[filtered_financial['Month_Year'] == m]['DSO'].mean() for m in filtered_financial['Month_Year'].unique()]
        }
        
        metrics_df = pd.DataFrame(metrics_dict)
        
        st.dataframe(metrics_df, height=300)
        csv_metrics = metrics_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Key Metrics as CSV",
            data=csv_metrics,
            file_name="financial_key_metrics.csv",
            mime="text/csv"
        )

else:
    st.error("Failed to load data. Please check your data files and paths.")
