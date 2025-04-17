// Dental Practice Financial Dataset Generator for CFO Analytics
// This script creates a realistic financial dataset spanning 2020 to 2025
// Focus on base-level financial data for multi-site dental practices
// Integrates with patient and operations data for consistency

const fs = require('fs');

// Helper functions
function randomBetween(min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min);
}
function randomFloatBetween(min, max, precision = 2) {
  const value = Math.random() * (max - min) + min;
  const multiplier = Math.pow(10, precision);
  return Math.round(value * multiplier) / multiplier;
}

function formatDate(date) {
  return date.toISOString().split('T')[0];
}

// Constants
const START_DATE = new Date(2020, 0, 1); // Jan 1, 2020
const END_DATE = new Date(2025, 3, 1);   // Apr 1, 2025

// Locations data - matches patient and operations data
const locations = [
  { 
    id: 'LOC001', 
    name: 'Downtown Dental', 
    address: '123 Main St, Portland, OR 97201',
    opened_date: '2015-03-15',
    square_footage: 3200,
    monthly_rent: 12800,
    acquisition_cost: 850000,
    acquisition_date: '2015-01-15',
    chairs: 5,
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
    square_footage: 2800,
    monthly_rent: 9800,
    acquisition_cost: 720000,
    acquisition_date: '2017-04-10',
    chairs: 4,
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
    square_footage: 2400,
    monthly_rent: 7200,
    acquisition_cost: 650000,
    acquisition_date: '2019-09-05',
    chairs: 3,
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
    square_footage: 2600,
    monthly_rent: 8500,
    acquisition_cost: 695000,
    acquisition_date: '2018-06-15',
    chairs: 4,
    target_chair_utilization: 0.83,
    target_collection_rate: 0.91,
    target_new_patients: 25,
    target_cancellation_rate: 0.06
  }
];

// Service categories for revenue breakdowns
const serviceCategories = [
  'Diagnostic',
  'Preventive',
  'Restorative',
  'Endodontic',
  'Periodontic',
  'Prosthodontic',
  'Oral Surgery',
  'Orthodontic',
  'Implant',
  'Adjunctive'
];

// Insurance providers for payor mix - matches patient data
const insuranceProviders = [
  { name: 'Delta Dental', reimbursement_rate: 0.85 },
  { name: 'Cigna Dental', reimbursement_rate: 0.80 },
  { name: 'Aetna', reimbursement_rate: 0.75 },
  { name: 'MetLife', reimbursement_rate: 0.82 },
  { name: 'Guardian', reimbursement_rate: 0.78 },
  { name: 'United Healthcare', reimbursement_rate: 0.79 },
  { name: 'No Insurance', reimbursement_rate: 1.00 }
];

// Expense categories
const expenseCategories = [
  'Labor - Clinical',
  'Labor - Administrative',
  'Supplies - Clinical',
  'Supplies - Office',
  'Rent/Lease',
  'Utilities',
  'Equipment Costs',
  'Marketing',
  'Insurance',
  'Professional Fees',
  'Continuing Education',
  'Lab Fees',
  'Software & IT',
  'Travel',
  'Miscellaneous'
];

// Generate holidays and special dates (to account for lower volume) - from operations data
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

// Generate seasonal and growth factors
function getSeasonalFactor(date) {
  const month = date.getMonth();
  
  // Check if it's a holiday
  const formattedDate = formatDate(date);
  const isHoliday = holidays.includes(formattedDate);
  if (isHoliday) {
    return randomFloatBetween(0.4, 0.6); // Significant reduction on holidays
  }
  
  // Winter - slightly slower
  if (month === 11 || month === 0 || month === 1) {
    return randomFloatBetween(0.85, 0.95);
  }
  
  // Spring - busy season
  if (month >= 2 && month <= 4) {
    return randomFloatBetween(1.05, 1.15);
  }
  
  // Summer - mixed
  if (month >= 5 && month <= 7) {
    return randomFloatBetween(0.9, 1.1);
  }
  
  // Fall - moderately busy
  return randomFloatBetween(0.95, 1.05);
}

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

function getGrowthFactor(date, location) {
  // Calculate years since location opened
  const locationOpenDate = new Date(location.opened_date);
  const yearsSinceOpening = date.getFullYear() - locationOpenDate.getFullYear() + 
                           (date.getMonth() - locationOpenDate.getMonth()) / 12;
  
  // Growth curve - faster growth in early years, then stabilizing
  // Start with baseline
  let baseGrowth = 1.0;
  
  // Clinics less than 2 years old grow at 15-25% annually
  if (yearsSinceOpening < 2) {
    baseGrowth += (yearsSinceOpening * 0.2) * randomFloatBetween(0.9, 1.1);
  } 
  // Clinics 2-4 years old grow at 8-15% annually
  else if (yearsSinceOpening < 4) {
    baseGrowth += 0.4 + ((yearsSinceOpening - 2) * 0.12) * randomFloatBetween(0.9, 1.1);
  } 
  // Clinics 4+ years old grow at 3-8% annually
  else {
    baseGrowth += 0.64 + ((yearsSinceOpening - 4) * 0.055) * randomFloatBetween(0.9, 1.1);
  }
  
  return baseGrowth;
}

// READ APPOINTMENT AND OPERATIONS DATA
// This function reads data from generated files to use for better alignment
function readExistingData() {
  return new Promise((resolve, reject) => {
    // Create containers for the aggregated data
    const appointmentsByLocationMonth = {};
    const operationsByLocationMonth = {};
    
    // First try to read appointment data
    try {
      // Check if the file exists
      if (fs.existsSync('Pat_App_Data.csv')) {
        const data = fs.readFileSync('Pat_App_Data.csv', 'utf8');
        
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
          const locationId = row.Location_ID;
          const year = parseInt(row.Year);
          const month = parseInt(row.Month);
          const chargedAmount = parseInt(row.Charged_Amount) || 0;
          const insuranceCovered = parseInt(row.Insurance_Covered_Amount) || 0;
          const amountPaid = parseInt(row.Amount_Paid) || 0;
          const appointmentStatus = row.Appointment_Status;
          
          // Create key for location and month
          const key = `${locationId}-${year}-${month}`;
          
          // Initialize if first time seeing this location/month
          if (!appointmentsByLocationMonth[key]) {
            appointmentsByLocationMonth[key] = {
              totalAppointments: 0,
              completedAppointments: 0,
              canceledAppointments: 0,
              noShowAppointments: 0,
              totalChargedAmount: 0,
              totalInsuranceCovered: 0,
              totalAmountPaid: 0,
              serviceCategoryCounts: {},
              payorCounts: {}
            };
          }
          
          // Update counters
          appointmentsByLocationMonth[key].totalAppointments++;
          
          if (appointmentStatus === 'Completed') {
            appointmentsByLocationMonth[key].completedAppointments++;
            appointmentsByLocationMonth[key].totalChargedAmount += chargedAmount;
            appointmentsByLocationMonth[key].totalInsuranceCovered += insuranceCovered;
            appointmentsByLocationMonth[key].totalAmountPaid += amountPaid;
            
            // Track service categories
            const category = row.Procedure_Category;
            if (category) {
              appointmentsByLocationMonth[key].serviceCategoryCounts[category] = 
                (appointmentsByLocationMonth[key].serviceCategoryCounts[category] || 0) + 1;
            }
            
            // Track insurance providers
            const insuranceProvider = row.Insurance_Provider;
            if (insuranceProvider) {
              appointmentsByLocationMonth[key].payorCounts[insuranceProvider] = 
                (appointmentsByLocationMonth[key].payorCounts[insuranceProvider] || 0) + 1;
            }
          } else if (appointmentStatus === 'Canceled') {
            appointmentsByLocationMonth[key].canceledAppointments++;
          } else if (appointmentStatus === 'No-Show') {
            appointmentsByLocationMonth[key].noShowAppointments++;
          }
        }
        
        console.log('Successfully processed appointment data');
      } else {
        console.log('Appointment data file not found, will generate synthetic data');
      }
    } catch (err) {
      console.error('Error reading appointment data:', err);
      // Continue with synthetic data if appointment data not available
    }
    
    // Next try to read operations data
    try {
      // Check if the file exists
      if (fs.existsSync('Operations_Data.csv')) {
        const data = fs.readFileSync('Operations_Data.csv', 'utf8');
        
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
          const locationId = row.Location_ID;
          const year = parseInt(row.Year);
          const month = parseInt(row.Month);
          const date = row.Date;
          const chairUtilization = parseFloat(row.Chair_Utilization) || 0;
          const actualAppointments = parseInt(row.Actual_Appointments) || 0;
          const newPatients = parseInt(row.New_Patient_Count) || 0;
          const totalLaborCost = parseInt(row.Total_Labor_Cost) || 0;
          const totalLaborHours = parseFloat(row.Total_Labor_Hours) || 0;
          const collectionRate = parseFloat(row.Actual_Collection_Rate) || 0;
          
          // Create key for location and month
          const key = `${locationId}-${year}-${month}`;
          
          // Initialize if first time seeing this location/month
          if (!operationsByLocationMonth[key]) {
            operationsByLocationMonth[key] = {
              daysInMonth: 0,
              totalAppointments: 0,
              totalNewPatients: 0,
              totalLaborCost: 0,
              totalLaborHours: 0,
              avgChairUtilization: 0,
              avgCollectionRate: 0
            };
          }
          
          // Update counters
          operationsByLocationMonth[key].daysInMonth++;
          operationsByLocationMonth[key].totalAppointments += actualAppointments;
          operationsByLocationMonth[key].totalNewPatients += newPatients;
          operationsByLocationMonth[key].totalLaborCost += totalLaborCost;
          operationsByLocationMonth[key].totalLaborHours += totalLaborHours;
          operationsByLocationMonth[key].avgChairUtilization += chairUtilization;
          operationsByLocationMonth[key].avgCollectionRate += collectionRate;
        }
        
        // Calculate averages for each location/month
        for (const key in operationsByLocationMonth) {
          const data = operationsByLocationMonth[key];
          if (data.daysInMonth > 0) {
            data.avgChairUtilization /= data.daysInMonth;
            data.avgCollectionRate /= data.daysInMonth;
          }
        }
        
        console.log('Successfully processed operations data');
      } else {
        console.log('Operations data file not found, will generate synthetic data');
      }
    } catch (err) {
      console.error('Error reading operations data:', err);
      // Continue with synthetic data if operations data not available
    }
    
    resolve({ appointmentsByLocationMonth, operationsByLocationMonth });
  });
}

// Generate monthly financial data for a specific location and month
async function generateMonthlyFinancialData(date, location, existingData) {
  const formattedDate = formatDate(date);
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  
  // Create key for lookup in existing data
  const lookupKey = `${location.id}-${year}-${month}`;
  
  // Extract any existing appointment data
  const appointmentData = existingData.appointmentsByLocationMonth[lookupKey];
  const operationsData = existingData.operationsByLocationMonth[lookupKey];
  
  // Calculate seasonal and growth factors
  const seasonalFactor = getSeasonalFactor(date);
  const growthFactor = getGrowthFactor(date, location);
  
  // Get comparative periods
  const lastMonthDate = new Date(date);
  lastMonthDate.setMonth(date.getMonth() - 1);
  const lastYearDate = new Date(date);
  lastYearDate.setFullYear(date.getFullYear() - 1);
  
  // ------ Generate Revenue Data -------
  
  let totalRevenue = 0;
  
  if (appointmentData && appointmentData.totalChargedAmount > 0) {
    // Use actual data from appointments if available
    totalRevenue = appointmentData.totalChargedAmount;
  } else {
    // Base revenue - varies by location size with some randomness
    let baseRevenue = 0;
    if (location.id === 'LOC001') { // Largest location
      baseRevenue = randomBetween(180000, 220000);
    } else if (location.id === 'LOC002') {
      baseRevenue = randomBetween(140000, 170000);
    } else if (location.id === 'LOC004') {
      baseRevenue = randomBetween(120000, 150000);
    } else {
      baseRevenue = randomBetween(100000, 130000);
    }
    
    // Apply seasonal and growth factors
    totalRevenue = Math.round(baseRevenue * seasonalFactor * growthFactor);
  }
  
  // Revenue breakdown by service category
  const serviceRevenue = {};
  if (appointmentData && Object.keys(appointmentData.serviceCategoryCounts).length > 0) {
    // Calculate service category revenue based on actual appointment counts
    let totalServiceCount = 0;
    for (const category in appointmentData.serviceCategoryCounts) {
      totalServiceCount += appointmentData.serviceCategoryCounts[category];
    }
    
    for (const category of serviceCategories) {
      const categoryCount = appointmentData.serviceCategoryCounts[category] || 0;
      serviceRevenue[category] = Math.round((categoryCount / totalServiceCount) * totalRevenue);
    }
  } else {
    // Use standard category weights with randomness
    const categoryWeights = {
      'Diagnostic': 0.10,
      'Preventive': 0.20,
      'Restorative': 0.25,
      'Endodontic': 0.08,
      'Periodontic': 0.07,
      'Prosthodontic': 0.10,
      'Oral Surgery': 0.05,
      'Orthodontic': 0.08,
      'Implant': 0.05,
      'Adjunctive': 0.02
    };
    
    // Add some randomness to the category weights
    let totalWeight = 0;
    for (const category of serviceCategories) {
      serviceRevenue[category] = categoryWeights[category] * randomFloatBetween(0.85, 1.15);
      totalWeight += serviceRevenue[category];
    }
    
    // Normalize and calculate actual amounts
    for (const category of serviceCategories) {
      serviceRevenue[category] = Math.round((serviceRevenue[category] / totalWeight) * totalRevenue);
    }
  }
  
  // ------ Generate Expense Data -------
  
  // Base expense categories
  const expenseData = {};
  
  // Labor - typically 24-32% of revenue
  if (operationsData && operationsData.totalLaborCost > 0) {
    // Use actual labor costs from operations data
    expenseData['Labor - Clinical'] = Math.round(operationsData.totalLaborCost * 0.75); // 75% of labor is clinical
    expenseData['Labor - Administrative'] = Math.round(operationsData.totalLaborCost * 0.25); // 25% is administrative
  } else {
    expenseData['Labor - Clinical'] = Math.round(totalRevenue * randomFloatBetween(0.18, 0.22));
    expenseData['Labor - Administrative'] = Math.round(totalRevenue * randomFloatBetween(0.06, 0.10));
  }
  
  // Supplies - typically 6-10% of revenue
  expenseData['Supplies - Clinical'] = Math.round(totalRevenue * randomFloatBetween(0.05, 0.08));
  expenseData['Supplies - Office'] = Math.round(totalRevenue * randomFloatBetween(0.01, 0.02));
  
  // Rent - fixed monthly cost but varies slightly
  expenseData['Rent/Lease'] = Math.round(location.monthly_rent * randomFloatBetween(0.98, 1.02));
  
  // Utilities - 1-3% of revenue
  expenseData['Utilities'] = Math.round(totalRevenue * randomFloatBetween(0.01, 0.03));
  
  // Equipment costs - typically 3-5% of revenue (includes lease payments, repairs)
  expenseData['Equipment Costs'] = Math.round(totalRevenue * randomFloatBetween(0.03, 0.05));
  
  // Marketing - 3-7% of revenue
  expenseData['Marketing'] = Math.round(totalRevenue * randomFloatBetween(0.03, 0.07));
  
  // Insurance - 2-4% of revenue
  expenseData['Insurance'] = Math.round(totalRevenue * randomFloatBetween(0.02, 0.04));
  
  // Professional fees - 2-4% of revenue (accounting, legal, consulting)
  expenseData['Professional Fees'] = Math.round(totalRevenue * randomFloatBetween(0.02, 0.04));
  
  // Continuing education - 0.5-1.5% of revenue
  expenseData['Continuing Education'] = Math.round(totalRevenue * randomFloatBetween(0.005, 0.015));
  
  // Lab fees - 6-10% of revenue
  expenseData['Lab Fees'] = Math.round(totalRevenue * randomFloatBetween(0.06, 0.10));
  
  // Software & IT - 1-3% of revenue
  expenseData['Software & IT'] = Math.round(totalRevenue * randomFloatBetween(0.01, 0.03));
  
  // Travel - 0.5-1.5% of revenue
  expenseData['Travel'] = Math.round(totalRevenue * randomFloatBetween(0.005, 0.015));
  
  // Miscellaneous - 1-3% of revenue
  expenseData['Miscellaneous'] = Math.round(totalRevenue * randomFloatBetween(0.01, 0.03));
  
  // Calculate total expenses
  const totalExpenses = Object.values(expenseData).reduce((sum, value) => sum + value, 0);
  
  // ------ Generate Cash Flow Data -------
  
  // Accounts receivable - 30-45 days of revenue
  const daysInAR = randomBetween(30, 45);
  const accountsReceivable = Math.round(totalRevenue * (daysInAR / 30));
  
  // AR aging buckets
  const arAging = {
    'Current': Math.round(accountsReceivable * randomFloatBetween(0.55, 0.65)),
    '31-60 Days': Math.round(accountsReceivable * randomFloatBetween(0.20, 0.25)),
    '61-90 Days': Math.round(accountsReceivable * randomFloatBetween(0.08, 0.12)),
    '91+ Days': Math.round(accountsReceivable * randomFloatBetween(0.05, 0.10))
  };
  
  // Insurance claims data
  let collectionRate = 0;
  
  if (operationsData && operationsData.avgCollectionRate > 0) {
    // Use actual collection rate from operations data
    collectionRate = operationsData.avgCollectionRate;
  } else if (appointmentData && appointmentData.totalChargedAmount > 0) {
    // Calculate from appointment data
    collectionRate = appointmentData.totalAmountPaid / appointmentData.totalChargedAmount;
  } else {
    // Use target with some randomness
    collectionRate = randomFloatBetween(
      Math.max(0.6, location.target_collection_rate - 0.1), 
      Math.min(0.98, location.target_collection_rate + 0.05)
    );
  }
  
  // Claims data
  const totalClaims = Math.round(totalRevenue * 0.8 / 150); // Estimate number of claims based on avg claim of $150
  const claimsSubmitted = totalClaims;
  const claimsOutstanding = Math.round(totalClaims * randomFloatBetween(0.3, 0.4));
  const claimsDenied = Math.round(totalClaims * randomFloatBetween(0.02, 0.05));
  const avgDaysToPayment = randomBetween(25, 40);
  
  // Payment collection data
  const collectionsExpected = totalRevenue * 0.9; // Expected to collect 90% of revenue
  const collectionsActual = Math.round(totalRevenue * collectionRate);
  
  // Procedure data
  let numberOfProcedures = 0;
  let completedProcedures = 0;
  let cancelledProcedures = 0;
  
  if (appointmentData) {
    // Use actual appointment data
    completedProcedures = appointmentData.completedAppointments;
    cancelledProcedures = appointmentData.canceledAppointments + appointmentData.noShowAppointments;
    numberOfProcedures = completedProcedures + cancelledProcedures;
  } else if (operationsData) {
    // Use operations data
    completedProcedures = operationsData.totalAppointments;
    cancelledProcedures = Math.round(completedProcedures * randomFloatBetween(0.02, 0.08));
    numberOfProcedures = completedProcedures + cancelledProcedures;
  } else {
    // Estimate based on revenue
    numberOfProcedures = Math.round(totalRevenue / randomBetween(200, 300)); // Average procedure value
    completedProcedures = Math.round(numberOfProcedures * randomFloatBetween(0.92, 0.98));
    cancelledProcedures = numberOfProcedures - completedProcedures;
  }
  
  // Patient data
  let patientVisits = 0;
  let newPatients = 0;
  let returningPatients = 0;
  
  if (operationsData) {
    // Use actual operations data
    patientVisits = operationsData.totalAppointments;
    newPatients = operationsData.totalNewPatients;
    returningPatients = patientVisits - newPatients;
  } else {
    // Estimate based on procedures
    patientVisits = Math.round(numberOfProcedures * 0.7); // Some patients get multiple procedures
    newPatients = Math.round(patientVisits * randomFloatBetween(0.15, 0.25));
    returningPatients = patientVisits - newPatients;
  }
  
  const patientRetentionRate = randomFloatBetween(0.75, 0.9);
  
  // Capacity and utilization
  const chairCapacity = location.chairs;
  const operatingDays = 22; // Average business days in month
  const operatingHours = 8; // Hours per day
  const totalChairHours = chairCapacity * operatingDays * operatingHours;
  let chairUtilization = 0;
  
  if (operationsData && operationsData.avgChairUtilization > 0) {
    // Use actual chair utilization from operations data
    chairUtilization = operationsData.avgChairUtilization;
  } else {
    // Estimate based on target with some randomness
    chairUtilization = randomFloatBetween(0.7, 0.9);
  }
  
  const usedChairHours = totalChairHours * chairUtilization;
  
  // Payor mix - distribution of revenue by insurance provider
  const payorMix = {};
  
  if (appointmentData && Object.keys(appointmentData.payorCounts).length > 0) {
    // Calculate payor mix based on actual appointment counts
    let totalPayorCount = 0;
    for (const provider in appointmentData.payorCounts) {
      totalPayorCount += appointmentData.payorCounts[provider];
    }
    
    for (const provider of insuranceProviders) {
      const providerCount = appointmentData.payorCounts[provider.name] || 0;
      payorMix[provider.name] = Math.round((providerCount / totalPayorCount) * totalRevenue);
    }
  } else {
    // Use standard payor weights with randomness
    const payorWeights = {
      'Delta Dental': 0.30,
      'Cigna Dental': 0.15,
      'Aetna': 0.12,
      'MetLife': 0.10,
      'Guardian': 0.08,
      'United Healthcare': 0.05,
      'No Insurance': 0.20
    };
    
    // Add some randomness to the payor weights
    let totalPayorWeight = 0;
    for (const provider of insuranceProviders) {
      const weight = payorWeights[provider.name] || 0.02;
      payorMix[provider.name] = weight * randomFloatBetween(0.85, 1.15);
      totalPayorWeight += payorMix[provider.name];
    }
    
    // Normalize and calculate actual amounts
    for (const provider of insuranceProviders) {
      payorMix[provider.name] = Math.round((payorMix[provider.name] / totalPayorWeight) * totalRevenue);
    }
  }
  
  // Treatment acceptance and completion rates
  const treatmentPlansPresented = Math.round(patientVisits * randomFloatBetween(0.3, 0.5));
  const treatmentPlansAccepted = Math.round(treatmentPlansPresented * randomFloatBetween(0.6, 0.8));
  const treatmentPlansCompleted = Math.round(treatmentPlansAccepted * randomFloatBetween(0.7, 0.9));
  
  // Generate KPIs and ratios
  const ebitda = totalRevenue - totalExpenses;
  const ebitdaMargin = ebitda / totalRevenue;
  const operatingCashFlow = collectionsActual - totalExpenses;
  const dso = accountsReceivable / (totalRevenue / 30); // Days Sales Outstanding
  const revenuePerSquareFoot = totalRevenue / location.square_footage;
  const revenuePerPatient = totalRevenue / patientVisits;
  const marketingROI = (totalRevenue * 0.15) / expenseData['Marketing']; // Assume 15% of revenue from marketing
  
  // Generate main financial record
  return {
    Financial_ID: `FIN-${location.id}-${year}${String(month).padStart(2, '0')}`,
    Location_ID: location.id,
    Location_Name: location.name,
    Date: formattedDate,
    Year: year,
    Month: month,
    Period: `${year}-${String(month).padStart(2, '0')}`,
    
    // Revenue metrics
    Total_Revenue: totalRevenue,
    Revenue_Diagnostic: serviceRevenue['Diagnostic'],
    Revenue_Preventive: serviceRevenue['Preventive'],
    Revenue_Restorative: serviceRevenue['Restorative'],
    Revenue_Endodontic: serviceRevenue['Endodontic'],
    Revenue_Periodontic: serviceRevenue['Periodontic'],
    Revenue_Prosthodontic: serviceRevenue['Prosthodontic'],
    Revenue_Oral_Surgery: serviceRevenue['Oral Surgery'],
    Revenue_Orthodontic: serviceRevenue['Orthodontic'],
    Revenue_Implant: serviceRevenue['Implant'],
    Revenue_Adjunctive: serviceRevenue['Adjunctive'],
    
    // Expense metrics
    Total_Expenses: totalExpenses,
    Labor_Clinical: expenseData['Labor - Clinical'],
    Labor_Administrative: expenseData['Labor - Administrative'],
    Supplies_Clinical: expenseData['Supplies - Clinical'],
    Supplies_Office: expenseData['Supplies - Office'],
    Rent_Lease: expenseData['Rent/Lease'],
    Utilities: expenseData['Utilities'],
    Equipment_Costs: expenseData['Equipment Costs'],
    Marketing: expenseData['Marketing'],
    Insurance: expenseData['Insurance'],
    Professional_Fees: expenseData['Professional Fees'],
    Continuing_Education: expenseData['Continuing Education'],
    Lab_Fees: expenseData['Lab Fees'],
    Software_IT: expenseData['Software & IT'],
    Travel: expenseData['Travel'],
    Miscellaneous: expenseData['Miscellaneous'],
    
    // Profitability metrics
    EBITDA: ebitda,
    EBITDA_Margin: ebitdaMargin.toFixed(4),
    Labor_Cost_Percentage: ((expenseData['Labor - Clinical'] + expenseData['Labor - Administrative']) / totalRevenue).toFixed(4),
    Supply_Cost_Percentage: ((expenseData['Supplies - Clinical'] + expenseData['Supplies - Office']) / totalRevenue).toFixed(4),
    
    // Accounts receivable
    Total_AR: accountsReceivable,
    AR_Current: arAging['Current'],
    AR_31_60: arAging['31-60 Days'],
    AR_61_90: arAging['61-90 Days'],
    AR_91_Plus: arAging['91+ Days'],
    DSO: dso.toFixed(1),
    
    // Insurance claims
    Total_Claims_Submitted: claimsSubmitted,
    Claims_Outstanding: claimsOutstanding,
    Claims_Denied: claimsDenied,
    Avg_Days_To_Payment: avgDaysToPayment,
    
    // Collections
    Collections_Expected: Math.round(collectionsExpected),
    Collections_Actual: collectionsActual,
    Collection_Rate: collectionRate.toFixed(4),
    
    // Procedure metrics
    Total_Procedures: numberOfProcedures,
    Completed_Procedures: completedProcedures,
    Cancelled_Procedures: cancelledProcedures,
    
    // Patient metrics
    Total_Patient_Visits: patientVisits,
    New_Patients: newPatients,
    Returning_Patients: returningPatients,
    Patient_Retention_Rate: patientRetentionRate.toFixed(4),
    Revenue_Per_Patient: revenuePerPatient.toFixed(2),
    
    // Capacity metrics
    Chair_Capacity: chairCapacity,
    Total_Chair_Hours: totalChairHours,
    Used_Chair_Hours: Math.round(usedChairHours),
    Chair_Utilization: chairUtilization.toFixed(4),
    
    // Payor mix
    Payor_Delta_Dental: payorMix['Delta Dental'],
    Payor_Cigna_Dental: payorMix['Cigna Dental'],
    Payor_Aetna: payorMix['Aetna'],
    Payor_MetLife: payorMix['MetLife'],
    Payor_Guardian: payorMix['Guardian'],
    Payor_United_Healthcare: payorMix['United Healthcare'],
    Payor_Self_Pay: payorMix['No Insurance'],
    
    // Treatment plan metrics
    Treatment_Plans_Presented: treatmentPlansPresented,
    Treatment_Plans_Accepted: treatmentPlansAccepted,
    Treatment_Plans_Completed: treatmentPlansCompleted,
    Case_Acceptance_Rate: (treatmentPlansAccepted / treatmentPlansPresented).toFixed(4),
    Treatment_Completion_Rate: (treatmentPlansCompleted / treatmentPlansAccepted).toFixed(4),
    
    // PE/CFO specific metrics
    Revenue_Per_Square_Foot: revenuePerSquareFoot.toFixed(2),
    Marketing_ROI: marketingROI.toFixed(2),
    Operating_Cash_Flow: operatingCashFlow,
    
    // Comparative metrics
    Revenue_MoM_Change: 0, // Will be filled in later
    Revenue_YoY_Change: 0, // Will be filled in later
    EBITDA_MoM_Change: 0,  // Will be filled in later
    EBITDA_YoY_Change: 0   // Will be filled in later
  };
}

// Function to generate the entire dataset
async function generateFinancialDataset() {
  // Get existing data from appointment and operations files
  const existingData = await readExistingData();
  
  const financialData = [];
  
  // Generate monthly records for each location
  for (const location of locations) {
    // Get start date for this location (either global start date or location opening date, whichever is later)
    const locationOpenDate = new Date(location.opened_date);
    const startDate = locationOpenDate > START_DATE ? new Date(locationOpenDate) : new Date(START_DATE);
    
    // Set to first day of the month
    startDate.setDate(1);
    
    // Generate data for each month
    let currentDate = new Date(startDate);
    
    while (currentDate <= END_DATE) {
      const monthData = await generateMonthlyFinancialData(currentDate, location, existingData);
      financialData.push(monthData);
      
      // Move to next month
      currentDate.setMonth(currentDate.getMonth() + 1);
    }
  }
  
  // Sort by location and date
  financialData.sort((a, b) => {
    if (a.Location_ID === b.Location_ID) {
      return new Date(a.Date) - new Date(b.Date);
    }
    return a.Location_ID.localeCompare(b.Location_ID);
  });
  
  // Calculate comparative metrics (MoM and YoY changes)
  for (let i = 0; i < financialData.length; i++) {
    const current = financialData[i];
    
    // Find previous month record (same location)
    const prevMonth = financialData.find(item => 
      item.Location_ID === current.Location_ID && 
      item.Year === (current.Month === 1 ? current.Year - 1 : current.Year) && 
      item.Month === (current.Month === 1 ? 12 : current.Month - 1)
    );
    
    // Find previous year record (same location, same month)
    const prevYear = financialData.find(item => 
      item.Location_ID === current.Location_ID && 
      item.Year === current.Year - 1 && 
      item.Month === current.Month
    );
    
    // Calculate MoM changes
    if (prevMonth) {
      current.Revenue_MoM_Change = ((current.Total_Revenue - prevMonth.Total_Revenue) / prevMonth.Total_Revenue).toFixed(4);
      current.EBITDA_MoM_Change = ((current.EBITDA - prevMonth.EBITDA) / prevMonth.EBITDA).toFixed(4);
    }
    
    // Calculate YoY changes
    if (prevYear) {
      current.Revenue_YoY_Change = ((current.Total_Revenue - prevYear.Total_Revenue) / prevYear.Total_Revenue).toFixed(4);
      current.EBITDA_YoY_Change = ((current.EBITDA - prevYear.EBITDA) / prevYear.EBITDA).toFixed(4);
    }
  }
  
  return financialData;
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
    // Generate the dataset
    console.log("Reading existing data and generating financial data...");
    const financialDataset = await generateFinancialDataset();
    
    // Save dataset to CSV file
    const financialCSV = convertToCSV(financialDataset);
    fs.writeFileSync('Financial_Data.csv', financialCSV);
    
    // Log results
    console.log(`Generated ${financialDataset.length} financial records`);
    console.log('Data saved to "Financial_Data.csv"');
    
    // Calculate some metrics for verification
    const totalRevenue = financialDataset.reduce((sum, record) => sum + record.Total_Revenue, 0);
    const totalEBITDA = financialDataset.reduce((sum, record) => sum + record.EBITDA, 0);
    const avgMargin = totalEBITDA / totalRevenue;
    
    console.log(`Total Revenue: $${totalRevenue.toLocaleString()}`);
    console.log(`Total EBITDA: $${totalEBITDA.toLocaleString()}`);
    console.log(`Average EBITDA Margin: ${(avgMargin * 100).toFixed(2)}%`);
    
    // Count records by year
    const byYear = {};
    financialDataset.forEach(record => {
      byYear[record.Year] = (byYear[record.Year] || 0) + 1;
    });
    console.log("Records by year:", byYear);
    
    // Count records by location
    const byLocation = {};
    financialDataset.forEach(record => {
      byLocation[record.Location_Name] = (byLocation[record.Location_Name] || 0) + 1;
    });
    console.log("Records by location:", byLocation);
  
  } catch (error) {
    console.error("Error generating financial data:", error);
  }
}

// Run the main function
main();