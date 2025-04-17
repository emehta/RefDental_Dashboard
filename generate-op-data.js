// Dental Clinic Operations Dataset Generator for CFO Analytics
// This script creates a realistic dataset of dental clinic operations metrics
// Integrates with existing appointment data to ensure consistency

const fs = require('fs');
// Using built-in modules instead of csv-parser

// Helper function to generate random numbers within a range
function randomBetween(min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min);
}

// Helper function to generate random float numbers within a range with specified precision
function randomFloatBetween(min, max, precision = 2) {
  const value = Math.random() * (max - min) + min;
  const multiplier = Math.pow(10, precision);
  return Math.round(value * multiplier) / multiplier;
}

// Helper function to format dates as YYYY-MM-DD
function formatDate(date) {
  return date.toISOString().split('T')[0];
}

// Constants for the dataset
const START_DATE = new Date(2020, 0, 1); // Jan 1, 2020
const END_DATE = new Date(2025, 3, 1);   // Apr 1, 2025

// Create location data (matching the patient/appointment dataset)
const locations = [
  { 
    id: 'LOC001', 
    name: 'Downtown Dental', 
    address: '123 Main St, Portland, OR 97201', 
    opened_date: '2015-03-15',
    chairs: 5,
    operatingHours: 9, // 8am - 5pm
    avgPatientsPerChairPerDay: 8,
    staffCount: { dentist: 3, hygienist: 4, assistant: 6, admin: 3 },
    target_chair_utilization: 0.85,
    target_collection_rate: 0.92,
    target_new_patients: 30,
    target_cancellation_rate: 0.05
  },
  { 
    id: 'LOC002', 
    name: 'Westside Smile Center', 
    address: '456 Park Ave, Portland, OR 97229', 
    opened_date: '2017-06-22',
    chairs: 4,
    operatingHours: 10, // 8am - 6pm
    avgPatientsPerChairPerDay: 7,
    staffCount: { dentist: 2, hygienist: 3, assistant: 4, admin: 2 },
    target_chair_utilization: 0.82,
    target_collection_rate: 0.90,
    target_new_patients: 25,
    target_cancellation_rate: 0.06
  },
  { 
    id: 'LOC003', 
    name: 'East Valley Dental Care', 
    address: '789 River Rd, Gresham, OR 97030', 
    opened_date: '2019-11-10',
    chairs: 3,
    operatingHours: 8, // 9am - 5pm
    avgPatientsPerChairPerDay: 6,
    staffCount: { dentist: 2, hygienist: 2, assistant: 3, admin: 2 },
    target_chair_utilization: 0.80,
    target_collection_rate: 0.88,
    target_new_patients: 20,
    target_cancellation_rate: 0.07
  },
  {
    id: 'LOC004',
    name: 'North Portland Family Dental',
    address: '234 Market St, Portland, OR 97217',
    opened_date: '2018-08-05',
    chairs: 4,
    operatingHours: 9, // 8am - 5pm
    avgPatientsPerChairPerDay: 7,
    staffCount: { dentist: 2, hygienist: 3, assistant: 4, admin: 2 },
    target_chair_utilization: 0.83,
    target_collection_rate: 0.91,
    target_new_patients: 25,
    target_cancellation_rate: 0.06
  }
];

// Create provider/staff data (matching the patient/appointment dataset)
const staffMembers = [
  // Dentists
  { id: 'DR001', name: 'Dr. Sarah Johnson', role: 'Dentist', primary_location: 'LOC001', specialty: 'General', hourly_rate: 150, full_time: true },
  { id: 'DR002', name: 'Dr. Michael Chen', role: 'Dentist', primary_location: 'LOC001', specialty: 'Orthodontics', hourly_rate: 160, full_time: true },
  { id: 'DR003', name: 'Dr. Robert Garcia', role: 'Dentist', primary_location: 'LOC002', specialty: 'Periodontics', hourly_rate: 155, full_time: true },
  { id: 'DR004', name: 'Dr. Emily Wilson', role: 'Dentist', primary_location: 'LOC002', specialty: 'General', hourly_rate: 145, full_time: false },
  { id: 'DR005', name: 'Dr. David Kim', role: 'Dentist', primary_location: 'LOC003', specialty: 'General', hourly_rate: 140, full_time: true },
  { id: 'DR006', name: 'Dr. Lisa Patel', role: 'Dentist', primary_location: 'LOC003', specialty: 'Endodontics', hourly_rate: 165, full_time: false },
  { id: 'DR007', name: 'Dr. James Taylor', role: 'Dentist', primary_location: 'LOC001', specialty: 'Oral Surgery', hourly_rate: 170, full_time: false },
  
  // Hygienists
  { id: 'HYG001', name: 'Lisa Martinez', role: 'Hygienist', primary_location: 'LOC001', specialty: 'Hygiene', hourly_rate: 60, full_time: true },
  { id: 'HYG002', name: 'John Anderson', role: 'Hygienist', primary_location: 'LOC002', specialty: 'Hygiene', hourly_rate: 58, full_time: true },
  { id: 'HYG003', name: 'Sophia Lee', role: 'Hygienist', primary_location: 'LOC003', specialty: 'Hygiene', hourly_rate: 55, full_time: true },
  { id: 'HYG004', name: 'Michael Brooks', role: 'Hygienist', primary_location: 'LOC001', specialty: 'Hygiene', hourly_rate: 62, full_time: true },
  { id: 'HYG005', name: 'Jennifer Lopez', role: 'Hygienist', primary_location: 'LOC001', specialty: 'Hygiene', hourly_rate: 59, full_time: true },
  { id: 'HYG006', name: 'Thomas Wright', role: 'Hygienist', primary_location: 'LOC002', specialty: 'Hygiene', hourly_rate: 57, full_time: true },
  { id: 'HYG007', name: 'Emily Davis', role: 'Hygienist', primary_location: 'LOC002', specialty: 'Hygiene', hourly_rate: 56, full_time: false },
  { id: 'HYG008', name: 'Ryan Cooper', role: 'Hygienist', primary_location: 'LOC003', specialty: 'Hygiene', hourly_rate: 54, full_time: true },
  { id: 'HYG009', name: 'Olivia Martinez', role: 'Hygienist', primary_location: 'LOC001', specialty: 'Hygiene', hourly_rate: 61, full_time: false },
  
  // Dental Assistants
  { id: 'ASST001', name: 'Maria Rodriguez', role: 'Assistant', primary_location: 'LOC001', specialty: 'General', hourly_rate: 28, full_time: true },
  { id: 'ASST002', name: 'David Smith', role: 'Assistant', primary_location: 'LOC001', specialty: 'General', hourly_rate: 27, full_time: true },
  { id: 'ASST003', name: 'Sarah Johnson', role: 'Assistant', primary_location: 'LOC001', specialty: 'Orthodontics', hourly_rate: 29, full_time: true },
  { id: 'ASST004', name: 'Michael Brown', role: 'Assistant', primary_location: 'LOC001', specialty: 'General', hourly_rate: 26, full_time: true },
  { id: 'ASST005', name: 'Jessica Lee', role: 'Assistant', primary_location: 'LOC001', specialty: 'Oral Surgery', hourly_rate: 30, full_time: true },
  { id: 'ASST006', name: 'Robert Wilson', role: 'Assistant', primary_location: 'LOC001', specialty: 'General', hourly_rate: 27, full_time: true },
  { id: 'ASST007', name: 'Karen Miller', role: 'Assistant', primary_location: 'LOC002', specialty: 'General', hourly_rate: 26, full_time: true },
  { id: 'ASST008', name: 'Daniel Taylor', role: 'Assistant', primary_location: 'LOC002', specialty: 'General', hourly_rate: 25, full_time: true },
  { id: 'ASST009', name: 'Michelle Davis', role: 'Assistant', primary_location: 'LOC002', specialty: 'Periodontics', hourly_rate: 28, full_time: true },
  { id: 'ASST010', name: 'Andrew Garcia', role: 'Assistant', primary_location: 'LOC002', specialty: 'General', hourly_rate: 26, full_time: true },
  { id: 'ASST011', name: 'Patricia Martinez', role: 'Assistant', primary_location: 'LOC003', specialty: 'General', hourly_rate: 25, full_time: true },
  { id: 'ASST012', name: 'Kevin Johnson', role: 'Assistant', primary_location: 'LOC003', specialty: 'General', hourly_rate: 24, full_time: true },
  { id: 'ASST013', name: 'Rachel Thompson', role: 'Assistant', primary_location: 'LOC003', specialty: 'Endodontics', hourly_rate: 27, full_time: true },
  
  // Administrative Staff
  { id: 'ADM001', name: 'Jennifer Williams', role: 'Admin', primary_location: 'LOC001', specialty: 'Reception', hourly_rate: 24, full_time: true },
  { id: 'ADM002', name: 'Christopher Davis', role: 'Admin', primary_location: 'LOC001', specialty: 'Billing', hourly_rate: 26, full_time: true },
  { id: 'ADM003', name: 'Amanda Johnson', role: 'Admin', primary_location: 'LOC001', specialty: 'Office Manager', hourly_rate: 32, full_time: true },
  { id: 'ADM004', name: 'Matthew Miller', role: 'Admin', primary_location: 'LOC002', specialty: 'Reception', hourly_rate: 23, full_time: true },
  { id: 'ADM005', name: 'Emma Smith', role: 'Admin', primary_location: 'LOC002', specialty: 'Office Manager', hourly_rate: 30, full_time: true },
  { id: 'ADM006', name: 'Brandon Wilson', role: 'Admin', primary_location: 'LOC003', specialty: 'Reception', hourly_rate: 22, full_time: true },
  { id: 'ADM007', name: 'Sophia Garcia', role: 'Admin', primary_location: 'LOC003', specialty: 'Office Manager', hourly_rate: 29, full_time: true },

  // New staff for LOC004
  { id: 'DR008', name: 'Dr. Natalie Wong', role: 'Dentist', primary_location: 'LOC004', specialty: 'General', hourly_rate: 155, full_time: true },
  { id: 'DR009', name: 'Dr. Marcus Jackson', role: 'Dentist', primary_location: 'LOC004', specialty: 'Pediatric', hourly_rate: 160, full_time: false },
  { id: 'HYG010', name: 'Benjamin Carter', role: 'Hygienist', primary_location: 'LOC004', specialty: 'Hygiene', hourly_rate: 58, full_time: true },
  { id: 'HYG011', name: 'Amelia Zhang', role: 'Hygienist', primary_location: 'LOC004', specialty: 'Hygiene', hourly_rate: 55, full_time: true },
  { id: 'ASST014', name: 'Tyler Robinson', role: 'Assistant', primary_location: 'LOC004', specialty: 'General', hourly_rate: 26, full_time: true },
  { id: 'ASST015', name: 'Alexandra Singh', role: 'Assistant', primary_location: 'LOC004', specialty: 'Pediatric', hourly_rate: 27, full_time: true },
  { id: 'ASST016', name: 'Caleb Washington', role: 'Assistant', primary_location: 'LOC004', specialty: 'General', hourly_rate: 25, full_time: true },
  { id: 'ASST017', name: 'Hannah Patel', role: 'Assistant', primary_location: 'LOC004', specialty: 'General', hourly_rate: 24, full_time: false },
  { id: 'ADM008', name: 'Noah Reynolds', role: 'Admin', primary_location: 'LOC004', specialty: 'Reception', hourly_rate: 23, full_time: true },
  { id: 'ADM009', name: 'Isabella Ramirez', role: 'Admin', primary_location: 'LOC004', specialty: 'Billing', hourly_rate: 26, full_time: true }
];

// Equipment data
const equipment = [
  { id: 'EQ001', name: 'Digital X-Ray Machine', type: 'Imaging', locations: ['LOC001', 'LOC002', 'LOC003', 'LOC004'], avg_usage_time: 15, avg_daily_uses: 12, maintenance_interval_days: 90 },
  { id: 'EQ002', name: 'Panoramic X-Ray', type: 'Imaging', locations: ['LOC001', 'LOC002', 'LOC004'], avg_usage_time: 20, avg_daily_uses: 6, maintenance_interval_days: 120 },
  { id: 'EQ003', name: 'CBCT Scanner', type: 'Imaging', locations: ['LOC001'], avg_usage_time: 30, avg_daily_uses: 3, maintenance_interval_days: 180 },
  { id: 'EQ004', name: 'Dental Chair 1', type: 'Treatment', locations: ['LOC001', 'LOC002', 'LOC003', 'LOC004'], avg_usage_time: 45, avg_daily_uses: 10, maintenance_interval_days: 60 },
  { id: 'EQ005', name: 'Dental Chair 2', type: 'Treatment', locations: ['LOC001', 'LOC002', 'LOC003', 'LOC004'], avg_usage_time: 45, avg_daily_uses: 10, maintenance_interval_days: 60 },
  { id: 'EQ006', name: 'Dental Chair 3', type: 'Treatment', locations: ['LOC001', 'LOC002', 'LOC003', 'LOC004'], avg_usage_time: 45, avg_daily_uses: 10, maintenance_interval_days: 60 },
  { id: 'EQ007', name: 'Dental Chair 4', type: 'Treatment', locations: ['LOC001', 'LOC002', 'LOC004'], avg_usage_time: 45, avg_daily_uses: 10, maintenance_interval_days: 60 },
  { id: 'EQ008', name: 'Dental Chair 5', type: 'Treatment', locations: ['LOC001'], avg_usage_time: 45, avg_daily_uses: 10, maintenance_interval_days: 60 },
  { id: 'EQ009', name: 'CAD/CAM System', type: 'Restoration', locations: ['LOC001'], avg_usage_time: 60, avg_daily_uses: 2, maintenance_interval_days: 90 },
  { id: 'EQ010', name: 'Sterilization Unit', type: 'Sterilization', locations: ['LOC001', 'LOC002', 'LOC003', 'LOC004'], avg_usage_time: 30, avg_daily_uses: 15, maintenance_interval_days: 30 },
  { id: 'EQ011', name: 'Dental Laser', type: 'Treatment', locations: ['LOC001', 'LOC002', 'LOC004'], avg_usage_time: 25, avg_daily_uses: 4, maintenance_interval_days: 60 },
  { id: 'EQ012', name: 'Intraoral Scanner', type: 'Imaging', locations: ['LOC001', 'LOC002', 'LOC003', 'LOC004'], avg_usage_time: 20, avg_daily_uses: 5, maintenance_interval_days: 45 }
];

// Generate holidays and special dates (to account for lower volume)
const holidays = [
  // 2020 holidays
  '2020-01-01', '2020-01-20', '2020-02-17', '2020-05-25', '2020-07-04', '2020-09-07', '2020-11-11', '2020-11-26', '2020-12-25',
  // 2021 holidays  
  '2021-01-01', '2021-01-18', '2021-02-15', '2021-05-31', '2021-07-04', '2021-09-06', '2021-11-11', '2021-11-25', '2021-12-25',
  // 2022 holidays
  '2022-01-01', '2022-01-17', '2022-02-21', '2022-05-30', '2022-07-04', '2022-09-05', '2022-11-11', '2022-11-24', '2022-12-25',
  // 2023 holidays
  '2023-01-01', '2023-01-16', '2023-02-20', '2023-05-29', '2023-07-04', '2023-09-04', '2023-11-11', '2023-11-23', '2023-12-25',
  // 2024 holidays
  '2024-01-01', '2024-01-15', '2024-02-19', '2024-05-27', '2024-07-04', '2024-09-02', '2024-11-11', '2024-11-28', '2024-12-25',
  // 2025 holidays
  '2025-01-01', '2025-01-20', '2025-02-17', '2025-05-26', '2025-07-04'
];

// Function to get seasonal factors (busier seasons, slower seasons)
function getSeasonalFactor(date) {
  const month = date.getMonth();
  
  // December (11), January (0), February (1): Winter - slightly slower
  if (month === 11 || month === 0 || month === 1) {
    return randomFloatBetween(0.8, 0.95);
  }
  
  // March (2), April (3), May (4): Spring - busy season
  if (month >= 2 && month <= 4) {
    return randomFloatBetween(1.0, 1.15);
  }
  
  // June (5), July (6), August (7): Summer - busy for kids, slower for adults
  if (month >= 5 && month <= 7) {
    return randomFloatBetween(0.9, 1.1);
  }
  
  // September (8), October (9), November (10): Fall - moderately busy
  return randomFloatBetween(0.95, 1.05);
}

// Function to calculate day of week factors (busier on certain days)
function getDayOfWeekFactor(date) {
  const day = date.getDay();
  
  // Sunday (0): Closed
  if (day === 0) {
    return 0;
  }
  
  // Monday (1): Start of week, often busy
  if (day === 1) {
    return randomFloatBetween(1.05, 1.15);
  }
  
  // Tuesday (2), Wednesday (3): Mid-week, very busy
  if (day === 2 || day === 3) {
    return randomFloatBetween(1.1, 1.2);
  }
  
  // Thursday (4): Busy day
  if (day === 4) {
    return randomFloatBetween(1.0, 1.1);
  }
  
  // Friday (5): Slower end of week
  if (day === 5) {
    return randomFloatBetween(0.8, 0.9);
  }
  
  // Saturday (6): Limited hours, often emergency only
  return randomFloatBetween(0.4, 0.6);
}

// Function to calculate growth factor over time
function getGrowthFactor(date) {
  // Start with baseline
  let baseGrowth = 1.0;
  
  // Calculate years since 2020
  const yearsSince2020 = date.getFullYear() - 2020 + (date.getMonth() / 12);
  
  // Add growth - assume 5% annual growth with some random variation
  baseGrowth += (yearsSince2020 * 0.05) * randomFloatBetween(0.8, 1.2);
  
  return baseGrowth;
}

// READ APPOINTMENT DATA AND PROCESS IT
// This function reads the appointment data from the CSV file and organizes it for easy lookup
function readAppointmentData() {
  return new Promise((resolve, reject) => {
    fs.readFile('Pat_App_Data.csv', 'utf8', (err, data) => {
      if (err) {
        console.error('Error reading appointment data file:', err);
        reject(err);
        return;
      }
      
      const appointmentsByDateLocation = {};
      
      // Parse CSV manually
      const rows = data.split('\n');
      const headers = rows[0].split(',').map(header => 
        header.replace(/^"|"$/g, '') // Remove quotes from headers
      );
      
      // Process each row starting from index 1 (skipping headers)
      for (let i = 1; i < rows.length; i++) {
        if (!rows[i].trim()) continue; // Skip empty rows
        
        // Split by comma, but respect quoted values
        const values = [];
        let current = '';
        let inQuotes = false;
        
        for (let char of rows[i]) {
          if (char === '"') {
            inQuotes = !inQuotes;
          } else if (char === ',' && !inQuotes) {
            values.push(current);
            current = '';
          } else {
            current += char;
          }
        }
        values.push(current); // Add the last value
        
        // Create a row object with header->value mapping
        const row = {};
        headers.forEach((header, index) => {
          if (index < values.length) {
            row[header] = values[index].replace(/^"|"$/g, ''); // Remove quotes
          } else {
            row[header] = '';
          }
        });
        
        // Extract key data
        const date = row.Date_of_Service;
        const locationId = row.Location_ID;
        const status = row.Appointment_Status;
        const duration = parseInt(row.Procedure_Duration) || 0;
        
        // Initialize structure if first time seeing this date/location
        if (!appointmentsByDateLocation[date]) {
          appointmentsByDateLocation[date] = {};
        }
        
        if (!appointmentsByDateLocation[date][locationId]) {
          appointmentsByDateLocation[date][locationId] = {
            total: 0,
            completed: 0,
            canceled: 0,
            noShow: 0,
            rescheduled: 0,
            totalDuration: 0,
            newPatients: 0,
            procedures: [],
            chargedAmount: 0,
            insuranceCovered: 0,
            patientResponsibility: 0,
            amountPaid: 0
          };
        }
        
        // Update counters based on appointment status
        appointmentsByDateLocation[date][locationId].total++;
        
        if (status === 'Completed') {
          appointmentsByDateLocation[date][locationId].completed++;
          appointmentsByDateLocation[date][locationId].totalDuration += duration;
          
          // Track financial data for completed appointments
          appointmentsByDateLocation[date][locationId].chargedAmount += parseInt(row.Charged_Amount) || 0;
          appointmentsByDateLocation[date][locationId].insuranceCovered += parseInt(row.Insurance_Covered_Amount) || 0;
          appointmentsByDateLocation[date][locationId].patientResponsibility += parseInt(row.Patient_Responsibility) || 0;
          appointmentsByDateLocation[date][locationId].amountPaid += parseInt(row.Amount_Paid) || 0;
          
          // Track procedure details
          if (row.Procedure_Code) {
            appointmentsByDateLocation[date][locationId].procedures.push({
              code: row.Procedure_Code,
              description: row.Procedure_Description,
              category: row.Procedure_Category,
              duration: duration
            });
          }
        } else if (status === 'Canceled') {
          appointmentsByDateLocation[date][locationId].canceled++;
        } else if (status === 'No-Show') {
          appointmentsByDateLocation[date][locationId].noShow++;
        } else if (status === 'Rescheduled') {
          appointmentsByDateLocation[date][locationId].rescheduled++;
        }
        
        // Track new patients
        if (row.Is_New_Patient === 'true') {
          appointmentsByDateLocation[date][locationId].newPatients++;
        }
      }
      
      console.log('Successfully processed appointment data');
      resolve(appointmentsByDateLocation);
    });
  });
}

// Generate operations data for a particular date and location
function generateDailyOperations(date, location, appointmentData) {
  const formattedDate = formatDate(date);
  
  // Check if it's a holiday
  const isHoliday = holidays.includes(formattedDate);
  
  // Check if it's a weekend
  const isWeekend = date.getDay() === 0 || date.getDay() === 6;
  
  // If Sunday or holiday, the clinic is closed
  if (date.getDay() === 0 || isHoliday) {
    return null;
  }
  
  // Get appointment metrics from the appointment data
  const appointmentMetrics = appointmentData[formattedDate] && 
                            appointmentData[formattedDate][location.id] ? 
                            appointmentData[formattedDate][location.id] : 
                            {
                              total: 0,
                              completed: 0,
                              canceled: 0,
                              noShow: 0,
                              rescheduled: 0,
                              totalDuration: 0,
                              newPatients: 0,
                              procedures: [],
                              chargedAmount: 0,
                              insuranceCovered: 0,
                              patientResponsibility: 0,
                              amountPaid: 0
                            };
  
  // Calculate chair utilization based on actual procedure durations
  let chairUtilization = 0;
  let targetUtilization = location.target_chair_utilization;
  
  // Improve target over time (0.5% per year)
  const yearsSince2020 = date.getFullYear() - 2020;
  targetUtilization += (yearsSince2020 * 0.005);
  
  // Calculate available chair minutes
  let availableMinutes = location.chairs * location.operatingHours * 60;
  if (date.getDay() === 6) { // Saturday half day
    availableMinutes = availableMinutes / 2;
  }
  
  // Calculate actual chair utilization if we have appointment data
  if (appointmentMetrics.totalDuration > 0) {
    chairUtilization = Math.min(0.95, appointmentMetrics.totalDuration / availableMinutes);
  } else {
    // Fallback to random if no appointment data available
    chairUtilization = randomFloatBetween(
      Math.max(0.65, targetUtilization - 0.1), 
      Math.min(0.95, targetUtilization + 0.05)
    );
  }
  
  // Calculate cancellation and no-show rates from actual data
  const totalScheduled = appointmentMetrics.total;
  const cancellations = appointmentMetrics.canceled;
  const noShows = appointmentMetrics.noShow;
  
  // Calculate rates
  const cancellationRate = totalScheduled > 0 ? cancellations / totalScheduled : 0;
  const noShowRate = totalScheduled > 0 ? noShows / totalScheduled : 0;
  
  // Use actual new patients count
  const newPatients = appointmentMetrics.newPatients;
  const actualAppointments = appointmentMetrics.completed;
  const returningPatients = actualAppointments - newPatients;
  
  // Calculate average wait time (in minutes) - still random since not in appointment data
  const avgWaitTime = randomBetween(5, 25);
  
  // Generate staff hours data
  let staffData = [];
  let totalLaborHours = 0;
  let totalLaborCost = 0;
  
  // Filter staff for this location
  const locationStaff = staffMembers.filter(staff => staff.primary_location === location.id);
  
  // Certain percentage of staff working each day
  const staffWorkingPercent = {
    'Dentist': 0.9,    // 90% of dentists working on any given day
    'Hygienist': 0.833,  // 80% of hygienists
    'Assistant': 0.85, // 85% of assistants
    'Admin': 0.973      // 95% of admin staff
  };
  
  // For each staff role, determine who's working
  Object.keys(staffWorkingPercent).forEach(role => {
    const staffInRole = locationStaff.filter(s => s.role === role);
    
    // Determine number of staff working today
    const numWorking = Math.round(staffInRole.length * staffWorkingPercent[role]);
    
    // Randomly select staff members working today
    const shuffled = [...staffInRole].sort(() => 0.5 - Math.random());
    const workingToday = shuffled.slice(0, numWorking);
    
    // For each working staff member, generate hours
    workingToday.forEach(staff => {
      // Full-time staff work 7-9 hours, part-time 4-6 hours
      let hoursWorked;
      if (date.getDay() === 6) { // Saturday
        hoursWorked = staff.full_time ? randomFloatBetween(4, 5) : randomFloatBetween(3, 4);
      } else {
        hoursWorked = staff.full_time ? randomFloatBetween(7, 9) : randomFloatBetween(4, 6);
      }
      
      // Calculate labor cost
      const laborCost = hoursWorked * staff.hourly_rate;
      
      // Add to totals
      totalLaborHours += hoursWorked;
      totalLaborCost += laborCost;
      
      // Add staff record
      staffData.push({
        Staff_ID: staff.id,
        Staff_Name: staff.name,
        Staff_Role: staff.role,
        Staff_Specialty: staff.specialty,
        Hours_Worked: hoursWorked,
        Labor_Cost: laborCost
      });
    });
  });
  
  // Generate equipment usage data
  let equipmentData = [];
  
  // Filter equipment for this location
  const locationEquipment = equipment.filter(eq => eq.locations.includes(location.id));
  
  // For each piece of equipment, generate usage data
  locationEquipment.forEach(eq => {
    // Adjust average usage based on appointment volume
    let volumeFactor = 1.0;
    if (location.avgPatientsPerChairPerDay > 0) {
      volumeFactor = actualAppointments / (location.avgPatientsPerChairPerDay * location.chairs);
    }
    
    const dailyUses = Math.round(eq.avg_daily_uses * volumeFactor * randomFloatBetween(0.8, 1.2));
    
    // Calculate total usage time
    const usageTime = dailyUses * eq.avg_usage_time;
    
    // Calculate utilization rate (usage time / available time)
    let availableMinutes = location.operatingHours * 60;
    if (date.getDay() === 6) { // Saturday half day
      availableMinutes = availableMinutes / 2;
    }
    
    const utilizationRate = Math.min(0.95, usageTime / availableMinutes);
    
    // Add equipment data
    equipmentData.push({
      Equipment_ID: eq.id,
      Equipment_Name: eq.name,
      Equipment_Type: eq.type,
      Usage_Count: dailyUses,
      Usage_Time_Minutes: usageTime,
      Utilization_Rate: utilizationRate.toFixed(2)
    });
  });
  
  // Calculate treatment plan metrics - deriving from actual appointment data
  // Use remaining code from the original function for treatment plans
  
  // Realistic treatment plan completion rate improvement over time
  const baseCompletionRate = 0.65; // 65% in 2020
  const targetCompletionRate = 0.85; // Target 85% by 2025
  
  // Linear interpolation based on year
  const fractionalYear = date.getFullYear() - 2020 + (date.getMonth() / 12);
  const treatmentPlanCompletionRate = baseCompletionRate + 
    ((targetCompletionRate - baseCompletionRate) * (fractionalYear / 5)) + 
    randomFloatBetween(-0.05, 0.05); // Add some random variation
  
  // Treatment plan metrics
  const activeTreatmentPlans = Math.round(actualAppointments * 0.433); // 40% of patients have active treatment plans
  const completedTreatmentPlans = Math.round(activeTreatmentPlans * treatmentPlanCompletionRate);
  const treatmentPlanStageTracking = {
    'Not Started': Math.round(activeTreatmentPlans * 0.1),
    'In Progress': Math.round(activeTreatmentPlans * 0.7),
    'Completed': completedTreatmentPlans,
    'Delayed': Math.round(activeTreatmentPlans * 0.2)
  };
  
  // Calculate insurance processing metrics
  // Show improvement over time
  const baseProcessingDays = 30; // 30 days in 2020
  const targetProcessingDays = 15; // Target 15 days by 2025
  
  // Linear interpolation for days to payment
  const avgDaysToPayment = baseProcessingDays - 
    ((baseProcessingDays - targetProcessingDays) * (fractionalYear / 5)) + 
    randomBetween(-2, 3); // Add some random variation
  
  // Insurance claim metrics - now derived from actual appointments with insurance
  const dailyClaimsSubmitted = Math.round(actualAppointments * 0.8); // 80% of appointments result in claims
  const dailyClaimsProcessed = Math.round(dailyClaimsSubmitted * randomFloatBetween(0.9, 1.1));
  const dailyClaimsPaid = Math.round(dailyClaimsProcessed * randomFloatBetween(0.85, 0.95));
  const dailyClaimsDenied = Math.round(dailyClaimsProcessed * randomFloatBetween(0.02, 0.08));
  
  // Calculate aging metrics for claims
  const claimsAging = {
    '0-30 days': Math.round(dailyClaimsSubmitted * 0.6),
    '31-60 days': Math.round(dailyClaimsSubmitted * 0.25),
    '61-90 days': Math.round(dailyClaimsSubmitted * 0.1),
    '90+ days': Math.round(dailyClaimsSubmitted * 0.05)
  };
  
  // Calculate financial metrics from actual appointment data
  const actualCollectionRate = appointmentMetrics.chargedAmount > 0 ? 
    appointmentMetrics.amountPaid / appointmentMetrics.chargedAmount : 
    randomFloatBetween(
      Math.max(0.6, location.target_collection_rate - 0.1), 
      Math.min(0.98, location.target_collection_rate + 0.05)
    );
  
  // Calculate revenue metrics
  let revenuePerHour = 0;
  let revenuePerChair = 0;
  let revenuePerPatient = 0;
  
  if (totalLaborHours > 0) {
    revenuePerHour = Math.round(appointmentMetrics.chargedAmount / totalLaborHours);
  } else {
    revenuePerHour = Math.round(randomFloatBetween(900, 1400) * getGrowthFactor(date));
  }
  
  if (location.chairs > 0) {
    revenuePerChair = Math.round(appointmentMetrics.chargedAmount / location.chairs);
  } else {
    revenuePerChair = Math.round(randomFloatBetween(1800, 2400) * getGrowthFactor(date));
  }
  
  if (actualAppointments > 0) {
    revenuePerPatient = Math.round(appointmentMetrics.chargedAmount / actualAppointments);
  } else {
    revenuePerPatient = Math.round(randomFloatBetween(250, 350) * getGrowthFactor(date));
  }
  
  // Cost percentages still use randomized values
  const laborCostPercentage = totalLaborCost > 0 && appointmentMetrics.chargedAmount > 0 ?
    (totalLaborCost / appointmentMetrics.chargedAmount).toFixed(2) :
    randomFloatBetween(0.27, 0.33).toFixed(2);
  
  const supplyCostPercentage = randomFloatBetween(0.12, 0.16).toFixed(2);
  const overheadPercentage = randomFloatBetween(0.35, 0.42).toFixed(2);
  
  // Create operations record
  return {
    Operations_ID: `OP-${location.id}-${formattedDate.replace(/-/g, '')}`,
    Location_ID: location.id,
    Location_Name: location.name,
    Date: formattedDate,
    Year: date.getFullYear(),
    Month: date.getMonth() + 1,
    Day_of_Week: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][date.getDay()],
    Is_Holiday: isHoliday,
    Is_Weekend: isWeekend,
    
    // Basic operational metrics - now from actual appointments
    Appointment_Capacity: location.chairs * location.avgPatientsPerChairPerDay,
    Scheduled_Appointments: totalScheduled,
    Actual_Appointments: actualAppointments,
    Chair_Utilization: chairUtilization.toFixed(2),
    Target_Chair_Utilization: targetUtilization.toFixed(2),
    Cancellation_Count: cancellations,
    Cancellation_Rate: cancellationRate.toFixed(2),
    No_Show_Count: noShows,
    No_Show_Rate: noShowRate.toFixed(2),
    Avg_Wait_Time: avgWaitTime,
    
    // Patient metrics - from actual appointments
    Total_Patients_Seen: actualAppointments,
    New_Patient_Count: newPatients,
    Returning_Patient_Count: returningPatients,
    Target_New_Patients: location.target_new_patients / 20, // Daily target (monthly/20)
    
    // Staff metrics
    Total_Labor_Hours: totalLaborHours.toFixed(1),
    Total_Labor_Cost: Math.round(totalLaborCost),
    Staff_Count: staffData.length,
    Dentist_Count: staffData.filter(s => s.Staff_Role === 'Dentist').length,
    Hygienist_Count: staffData.filter(s => s.Staff_Role === 'Hygienist').length,
    Assistant_Count: staffData.filter(s => s.Staff_Role === 'Assistant').length,
    Admin_Count: staffData.filter(s => s.Staff_Role === 'Admin').length,
    
    // Equipment metrics
    Equipment_Count: equipmentData.length,
    Avg_Equipment_Utilization: equipmentData.length > 0 
      ? (equipmentData.reduce((sum, eq) => sum + parseFloat(eq.Utilization_Rate), 0) / equipmentData.length).toFixed(2) 
      : "0.00",
    
    // Treatment plan metrics
    Active_Treatment_Plans: activeTreatmentPlans,
    Completed_Treatment_Plans: completedTreatmentPlans,
    Treatment_Plan_Completion_Rate: treatmentPlanCompletionRate.toFixed(2),
    Treatment_Plans_Not_Started: treatmentPlanStageTracking['Not Started'],
    Treatment_Plans_In_Progress: treatmentPlanStageTracking['In Progress'],
    Treatment_Plans_Completed: treatmentPlanStageTracking['Completed'],
    Treatment_Plans_Delayed: treatmentPlanStageTracking['Delayed'],
    
    // Insurance metrics
    Insurance_Claims_Submitted: dailyClaimsSubmitted,
    Insurance_Claims_Processed: dailyClaimsProcessed,
    Insurance_Claims_Paid: dailyClaimsPaid,
    Insurance_Claims_Denied: dailyClaimsDenied,
    Insurance_Denial_Rate: (dailyClaimsDenied / dailyClaimsProcessed).toFixed(2),
    Avg_Days_To_Payment: avgDaysToPayment,
    Claims_Aging_0_30: claimsAging['0-30 days'],
    Claims_Aging_31_60: claimsAging['31-60 days'],
    Claims_Aging_61_90: claimsAging['61-90 days'],
    Claims_Aging_90_Plus: claimsAging['90+ days'],
    
    // CFO-specific financial benchmarks - now from actual appointment data
    Target_Collection_Rate: location.target_collection_rate.toFixed(2),
    Actual_Collection_Rate: actualCollectionRate.toFixed(2),
    
    Revenue_Per_Hour: revenuePerHour,
    Revenue_Per_Chair: revenuePerChair,
    Revenue_Per_Patient: revenuePerPatient,
    Labor_Cost_Percentage: laborCostPercentage,
    Supply_Cost_Percentage: supplyCostPercentage,
    Overhead_Percentage: overheadPercentage,
    
    // Reference to staff and equipment data
    Staff_Details: staffData,
    Equipment_Details: equipmentData
  };
}

// Generate operations dataset
async function generateOperationsDataset() {
  const appointmentData = await readAppointmentData();
  
  const operationsData = [];
  const staffHoursData = [];
  const equipmentUsageData = [];
  
  // Generate daily records
  let date = new Date(START_DATE);
  let recordsGenerated = 0;
  
  while (date <= END_DATE) {
    // For each location, generate daily operations data
    for (const location of locations) {
      const dailyData = generateDailyOperations(date, location, appointmentData);
      
      // Skip if null (clinic closed)
      if (dailyData) {
        // Extract staff and equipment data to separate datasets
        const staffDetails = [...dailyData.Staff_Details];
        const equipmentDetails = [...dailyData.Equipment_Details];
        
        // Remove from main dataset to avoid redundancy
        delete dailyData.Staff_Details;
        delete dailyData.Equipment_Details;
        
        // Add to main operations dataset
        operationsData.push(dailyData);
        
        // Add staff hours to separate dataset
        staffDetails.forEach(staffRecord => {
          staffHoursData.push({
            Operations_ID: dailyData.Operations_ID,
            Location_ID: dailyData.Location_ID,
            Date: dailyData.Date,
            Staff_ID: staffRecord.Staff_ID,
            Staff_Name: staffRecord.Staff_Name,
            Staff_Role: staffRecord.Staff_Role,
            Staff_Specialty: staffRecord.Staff_Specialty,
            Hours_Worked: staffRecord.Hours_Worked,
            Labor_Cost: staffRecord.Labor_Cost
          });
        });
        
        // Add equipment usage to separate dataset
        equipmentDetails.forEach(equipRecord => {
          equipmentUsageData.push({
            Operations_ID: dailyData.Operations_ID,
            Location_ID: dailyData.Location_ID,
            Date: dailyData.Date,
            Equipment_ID: equipRecord.Equipment_ID,
            Equipment_Name: equipRecord.Equipment_Name,
            Equipment_Type: equipRecord.Equipment_Type,
            Usage_Count: equipRecord.Usage_Count,
            Usage_Time_Minutes: equipRecord.Usage_Time_Minutes,
            Utilization_Rate: equipRecord.Utilization_Rate
          });
        });
        
        recordsGenerated++;
      }
    }
    
    // Move to next day
    date.setDate(date.getDate() + 1);
  }
  
  return { operationsData, staffHoursData, equipmentUsageData };
}

// Convert array to CSV
function convertToCSV(data) {
  // Skip empty datasets
  if (!data || data.length === 0) return '';
  
  // Get headers
  const headers = Object.keys(data[0]);
  
  // Create CSV rows
  const csvRows = [];
  
  // Add headers row
  csvRows.push(headers.join(','));
  
  // Add data rows
  for (const row of data) {
    const values = headers.map(header => {
      const value = row[header];
      // Handle string values that might contain commas
      return typeof value === 'string' ? `"${value}"` : value;
    });
    csvRows.push(values.join(','));
  }
  
  return csvRows.join('\n');
}

// Main execution function
async function main() {
  try {
    // Generate the datasets
    console.log("Reading appointment data and generating operations data...");
    const { operationsData, staffHoursData, equipmentUsageData } = await generateOperationsDataset();
    
    // Save datasets to CSV files
    console.log("Saving data to CSV files...");
    const operationsCSV = convertToCSV(operationsData);
    fs.writeFileSync('Dental_Operations_Data.csv', operationsCSV);
    
    const staffHoursCSV = convertToCSV(staffHoursData);
    fs.writeFileSync('Dental_Staff_Hours_Data.csv', staffHoursCSV);
    
    const equipmentUsageCSV = convertToCSV(equipmentUsageData);
    fs.writeFileSync('Dental_Equipment_Usage_Data.csv', equipmentUsageCSV);
    
    // Log results
    console.log(`Generated ${operationsData.length} dental operations records`);
    console.log(`Generated ${staffHoursData.length} staff hours records`);
    console.log(`Generated ${equipmentUsageData.length} equipment usage records`);
    console.log(`Data saved to 'Dental_Operations_Data.csv', 'Dental_Staff_Hours_Data.csv', and 'Dental_Equipment_Usage_Data.csv'`);
    
    // Calculate some metrics for verification
    const totalAppointments = operationsData.reduce((sum, op) => sum + op.Actual_Appointments, 0);
    const totalLaborCost = operationsData.reduce((sum, op) => sum + op.Total_Labor_Cost, 0);
    const avgChairUtilization = operationsData.reduce((sum, op) => sum + parseFloat(op.Chair_Utilization), 0) / operationsData.length;
    
    console.log(`Total appointments across all locations: ${totalAppointments}`);
    console.log(`Total labor cost: $${totalLaborCost.toLocaleString()}`);
    console.log(`Average chair utilization: ${(avgChairUtilization * 100).toFixed(1)}%`);
    
    // Count records by year
    const byYear = {};
    operationsData.forEach(op => {
      byYear[op.Year] = (byYear[op.Year] || 0) + 1;
    });
    console.log("Records by year:", byYear);
    
    // Count records by location
    const byLocation = {};
    operationsData.forEach(op => {
      byLocation[op.Location_Name] = (byLocation[op.Location_Name] || 0) + 1;
    });
    console.log("Records by location:", byLocation);
    
  } catch (error) {
    console.error("Error generating operations data:", error);
  }
}

// Run the main function
main();