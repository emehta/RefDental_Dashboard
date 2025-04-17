// Dental Clinic Dataset Generator for CFO Analytics
// This script creates a realistic dataset of dental appointments, procedures, and financial data
// Can be run in Node.js with lodash and papaparse packages installed

const fs = require('fs');

// Helper function to generate random appointment times during business hours
function randomAppointmentTime() {
  // Dental offices typically open 8am-5pm
  const hour = randomBetween(8, 16); // 8am to 4pm start times
  const minute = [0, 15, 30, 45][randomBetween(0, 3)]; // Appointments usually start on quarter hours
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
}

// Helper function to generate random numbers within a range
function randomBetween(min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min);
}

// Helper function to generate random dates within a range
function randomDate(start, end) {
  return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
}

// Helper function to format dates as YYYY-MM-DD
function formatDate(date) {
  return date.toISOString().split('T')[0];
}

// Track last cleaning date for each patient to model recall patterns
const patientLastCleaningDate = {};

// Function to determine if patient is due for recall based on procedure
function isDueForRecall(patientId, procedureCode, currentDate) {
  // Only implement recall patterns for cleaning procedures
  if (procedureCode !== 'D1110' && procedureCode !== 'D1120') {
    return true; // Not a cleaning, so no recall pattern needed
  }
  
  const lastCleaning = patientLastCleaningDate[patientId];
  if (!lastCleaning) {
    return true; // First cleaning, so they're due
  }
  
  // Calculate time since last cleaning
  const lastDate = new Date(lastCleaning);
  const currentDateTime = new Date(currentDate);
  const monthsSince = (currentDateTime.getFullYear() - lastDate.getFullYear()) * 12 + 
                     (currentDateTime.getMonth() - lastDate.getMonth());
  
  // Patients typically get cleanings every 6 months, with some variation
  return monthsSince >= 5; // Due for recall if at least 5 months since last cleaning
}

// Track active treatment plans
const activeTreatmentPlans = {};

// Constants for the dataset
const START_DATE = new Date(2020, 0, 1); // Jan 1, 2020
const END_DATE = new Date(2025, 3, 1);   // Apr 1, 2025
const NUM_RECORDS = 10000;                 // Number of appointment records
const NUM_PATIENTS = 600;                 // Number of unique patients

// Create location data
const locations = [
  { id: 'LOC001', name: 'Downtown Dental', address: '123 Main St, Portland, OR 97201', google_rating: 4.8, opened_date: '2015-03-15', services_offered: 'General|Cosmetic|Orthodontic|Pediatric|Implants' },
  { id: 'LOC002', name: 'Westside Smile Center', address: '456 Park Ave, Portland, OR 97229', google_rating: 4.6, opened_date: '2017-06-22', services_offered: 'General|Cosmetic|Periodontic|Implants|Emergency' },
  { id: 'LOC003', name: 'East Valley Dental Care', address: '789 River Rd, Gresham, OR 97030', google_rating: 4.5, opened_date: '2019-11-10', services_offered: 'General|Cosmetic|Pediatric|Emergency' },
  { id: 'LOC004', name: 'North Portland Family Dental', address: '234 Market St, Portland, OR 97217', google_rating: 4.7, opened_date: '2018-08-05', services_offered: 'General|Cosmetic|Pediatric|Emergency|Endodontic' }
];

// Create provider data
const providers = [
  { id: 'DR001', name: 'Dr. Sarah Johnson', role: 'Dentist', primary_location: 'LOC001', specialty: 'General', hourly_rate: 150, full_time: true },
  { id: 'DR002', name: 'Dr. Michael Chen', role: 'Dentist', primary_location: 'LOC001', specialty: 'Orthodontics', hourly_rate: 160, full_time: true },
  { id: 'DR003', name: 'Dr. Robert Garcia', role: 'Dentist', primary_location: 'LOC002', specialty: 'Periodontics', hourly_rate: 155, full_time: true },
  { id: 'DR004', name: 'Dr. Emily Wilson', role: 'Dentist', primary_location: 'LOC002', specialty: 'General', hourly_rate: 145, full_time: false },
  { id: 'DR005', name: 'Dr. David Kim', role: 'Dentist', primary_location: 'LOC003', specialty: 'General', hourly_rate: 140, full_time: true },
  { id: 'DR006', name: 'Dr. Lisa Patel', role: 'Dentist', primary_location: 'LOC003', specialty: 'Endodontics', hourly_rate: 165, full_time: false },
  { id: 'DR007', name: 'Dr. James Taylor', role: 'Dentist', primary_location: 'LOC004', specialty: 'Oral Surgery', hourly_rate: 170, full_time: false },
  // Hygienists
  { id: 'HYG001', name: 'Lisa Martinez', role: 'Hygienist', primary_location: 'LOC001', specialty: 'Hygiene', hourly_rate: 60, full_time: true },
  { id: 'HYG002', name: 'John Anderson', role: 'Hygienist', primary_location: 'LOC002', specialty: 'Hygiene', hourly_rate: 58, full_time: true },
  { id: 'HYG003', name: 'Sophia Lee', role: 'Hygienist', primary_location: 'LOC003', specialty: 'Hygiene', hourly_rate: 55, full_time: true },
  { id: 'HYG004', name: 'Michael Brooks', role: 'Hygienist', primary_location: 'LOC001', specialty: 'Hygiene', hourly_rate: 62, full_time: true },
  { id: 'HYG005', name: 'Jennifer Lopez', role: 'Hygienist', primary_location: 'LOC001', specialty: 'Hygiene', hourly_rate: 59, full_time: true },
  { id: 'HYG006', name: 'Thomas Wright', role: 'Hygienist', primary_location: 'LOC002', specialty: 'Hygiene', hourly_rate: 57, full_time: true },
  { id: 'HYG007', name: 'Emily Davis', role: 'Hygienist', primary_location: 'LOC002', specialty: 'Hygiene', hourly_rate: 56, full_time: false },
  { id: 'HYG008', name: 'Ryan Cooper', role: 'Hygienist', primary_location: 'LOC003', specialty: 'Hygiene', hourly_rate: 54, full_time: true },
  { id: 'HYG009', name: 'Olivia Martinez', role: 'Hygienist', primary_location: 'LOC004', specialty: 'Hygiene', hourly_rate: 61, full_time: false },

  // Dental Assistants
  { id: 'ASST001', name: 'Maria Rodriguez', role: 'Assistant', primary_location: 'LOC001', specialty: 'General', hourly_rate: 28, full_time: true },
  { id: 'ASST002', name: 'David Smith', role: 'Assistant', primary_location: 'LOC001', specialty: 'General', hourly_rate: 27, full_time: true },
  { id: 'ASST003', name: 'Sarah Johnson', role: 'Assistant', primary_location: 'LOC001', specialty: 'Orthodontics', hourly_rate: 29, full_time: true },
  { id: 'ASST004', name: 'Michael Brown', role: 'Assistant', primary_location: 'LOC001', specialty: 'General', hourly_rate: 26, full_time: true },
  { id: 'ASST005', name: 'Jessica Lee', role: 'Assistant', primary_location: 'LOC001', specialty: 'Oral Surgery', hourly_rate: 30, full_time: true },
  { id: 'ASST006', name: 'Robert Wilson', role: 'Assistant', primary_location: 'LOC002', specialty: 'General', hourly_rate: 27, full_time: true },
  { id: 'ASST007', name: 'Karen Miller', role: 'Assistant', primary_location: 'LOC002', specialty: 'General', hourly_rate: 26, full_time: true },
  { id: 'ASST008', name: 'Daniel Taylor', role: 'Assistant', primary_location: 'LOC002', specialty: 'General', hourly_rate: 25, full_time: true },
  { id: 'ASST009', name: 'Michelle Davis', role: 'Assistant', primary_location: 'LOC002', specialty: 'Periodontics', hourly_rate: 28, full_time: true },
  { id: 'ASST010', name: 'Andrew Garcia', role: 'Assistant', primary_location: 'LOC003', specialty: 'General', hourly_rate: 26, full_time: true },
  { id: 'ASST011', name: 'Patricia Martinez', role: 'Assistant', primary_location: 'LOC003', specialty: 'General', hourly_rate: 25, full_time: true },
  { id: 'ASST012', name: 'Kevin Johnson', role: 'Assistant', primary_location: 'LOC003', specialty: 'General', hourly_rate: 24, full_time: true },
  { id: 'ASST013', name: 'Rachel Thompson', role: 'Assistant', primary_location: 'LOC004', specialty: 'Endodontics', hourly_rate: 27, full_time: true },
  
  // Administrative Staff
  { id: 'ADM001', name: 'Jennifer Williams', role: 'Admin', primary_location: 'LOC001', specialty: 'Reception', hourly_rate: 24, full_time: true },
  { id: 'ADM002', name: 'Christopher Davis', role: 'Admin', primary_location: 'LOC001', specialty: 'Billing', hourly_rate: 26, full_time: true },
  { id: 'ADM003', name: 'Amanda Johnson', role: 'Admin', primary_location: 'LOC001', specialty: 'Office Manager', hourly_rate: 32, full_time: true },
  { id: 'ADM004', name: 'Matthew Miller', role: 'Admin', primary_location: 'LOC002', specialty: 'Reception', hourly_rate: 23, full_time: true },
  { id: 'ADM005', name: 'Emma Smith', role: 'Admin', primary_location: 'LOC002', specialty: 'Office Manager', hourly_rate: 30, full_time: true },
  { id: 'ADM006', name: 'Brandon Wilson', role: 'Admin', primary_location: 'LOC003', specialty: 'Reception', hourly_rate: 22, full_time: true },
  { id: 'ADM007', name: 'Sophia Garcia', role: 'Admin', primary_location: 'LOC004', specialty: 'Office Manager', hourly_rate: 29, full_time: true },

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

// Create insurance provider data
const insuranceProviders = [
  { name: 'Delta Dental', avg_reimbursement_rate: 0.85 },
  { name: 'Cigna Dental', avg_reimbursement_rate: 0.80 },
  { name: 'Aetna', avg_reimbursement_rate: 0.75 },
  { name: 'MetLife', avg_reimbursement_rate: 0.82 },
  { name: 'Guardian', avg_reimbursement_rate: 0.78 },
  { name: 'No Insurance', avg_reimbursement_rate: 1.00 } // Self-pay
];

// Create procedure categories and codes
const procedures = [
  // Diagnostic
  { code: 'D0120', description: 'Periodic Oral Evaluation', category: 'Diagnostic', avg_fee: 60, duration: 15 },
  { code: 'D0150', description: 'Comprehensive Oral Evaluation', category: 'Diagnostic', avg_fee: 110, duration: 30 },
  { code: 'D0210', description: 'Complete Series X-rays', category: 'Diagnostic', avg_fee: 150, duration: 30 },
  { code: 'D0220', description: 'Periapical X-ray (First Film)', category: 'Diagnostic', avg_fee: 35, duration: 10 },
  { code: 'D0274', description: 'Bitewing X-rays (Four Films)', category: 'Diagnostic', avg_fee: 70, duration: 15 },
  
  // Preventive
  { code: 'D1110', description: 'Prophylaxis (Cleaning) - Adult', category: 'Preventive', avg_fee: 110, duration: 45 },
  { code: 'D1120', description: 'Prophylaxis (Cleaning) - Child', category: 'Preventive', avg_fee: 85, duration: 30 },
  { code: 'D1208', description: 'Fluoride Treatment', category: 'Preventive', avg_fee: 45, duration: 15 },
  { code: 'D1351', description: 'Sealant (Per Tooth)', category: 'Preventive', avg_fee: 60, duration: 20 },
  
  // Restorative
  { code: 'D2140', description: 'Amalgam Filling - One Surface', category: 'Restorative', avg_fee: 155, duration: 45 },
  { code: 'D2150', description: 'Amalgam Filling - Two Surfaces', category: 'Restorative', avg_fee: 195, duration: 60 },
  { code: 'D2160', description: 'Amalgam Filling - Three Surfaces', category: 'Restorative', avg_fee: 235, duration: 75 },
  { code: 'D2330', description: 'Resin Filling - One Surface', category: 'Restorative', avg_fee: 175, duration: 45 },
  { code: 'D2331', description: 'Resin Filling - Two Surfaces', category: 'Restorative', avg_fee: 215, duration: 60 },
  { code: 'D2332', description: 'Resin Filling - Three Surfaces', category: 'Restorative', avg_fee: 255, duration: 75 },
  { code: 'D2740', description: 'Crown - Porcelain/Ceramic', category: 'Restorative', avg_fee: 1250, duration: 90 },
  { code: 'D2750', description: 'Crown - Porcelain Fused to Metal', category: 'Restorative', avg_fee: 1150, duration: 90 },
  
  // Endodontics
  { code: 'D3310', description: 'Root Canal - Anterior', category: 'Endodontic', avg_fee: 825, duration: 90 },
  { code: 'D3320', description: 'Root Canal - Bicuspid', category: 'Endodontic', avg_fee: 950, duration: 105 },
  { code: 'D3330', description: 'Root Canal - Molar', category: 'Endodontic', avg_fee: 1150, duration: 120 },
  
  // Periodontics
  { code: 'D4341', description: 'Periodontal Scaling & Root Planing (Per Quadrant)', category: 'Periodontic', avg_fee: 275, duration: 60 },
  { code: 'D4910', description: 'Periodontal Maintenance', category: 'Periodontic', avg_fee: 135, duration: 45 },
  
  // Prosthodontics
  { code: 'D5110', description: 'Complete Denture - Maxillary', category: 'Prosthodontic', avg_fee: 1890, duration: 100 },
  { code: 'D5120', description: 'Complete Denture - Mandibular', category: 'Prosthodontic', avg_fee: 1850, duration: 90 },
  { code: 'D5213', description: 'Partial Denture - Maxillary', category: 'Prosthodontic', avg_fee: 1650, duration: 90 },
  { code: 'D5214', description: 'Partial Denture - Mandibular', category: 'Prosthodontic', avg_fee: 1650, duration: 90 },
  
  // Implants
  { code: 'D6010', description: 'Surgical Implant Placement', category: 'Implant', avg_fee: 2100, duration: 120 },
  { code: 'D6056', description: 'Implant Abutment', category: 'Implant', avg_fee: 650, duration: 60 },
  { code: 'D6058', description: 'Implant Crown', category: 'Implant', avg_fee: 1550, duration: 90 },
  
  // Orthodontics
  { code: 'D8080', description: 'Comprehensive Orthodontic Treatment - Adolescent', category: 'Orthodontic', avg_fee: 5500, duration: 120 },
  { code: 'D8090', description: 'Comprehensive Orthodontic Treatment - Adult', category: 'Orthodontic', avg_fee: 6200, duration: 120 },
  
  // Adjunctive Services
  { code: 'D9110', description: 'Palliative Treatment (Emergency)', category: 'Adjunctive', avg_fee: 125, duration: 30 },
  { code: 'D9215', description: 'Local Anesthesia', category: 'Adjunctive', avg_fee: 45, duration: 10 },
  { code: 'D9310', description: 'Consultation', category: 'Adjunctive', avg_fee: 95, duration: 45 }
];

// Define common teeth for dental procedures
const teeth = [
  '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16',  // Upper teeth (1-16)
  '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32'  // Lower teeth (17-32)
];

// Generate patient data
function generatePatients() {
  const patients = [];
  const genders = ['Male', 'Female'];
  const firstNamesMale = [
    'James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles',
    'Kwame', 'Kenji', 'Mateo', 'Rajiv', 'Omar', 'Javier', 'Andre', 'Devon', 'Suresh', 'Jamal'
  ];

  const firstNamesFemale = [
    'Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica', 'Sarah', 'Karen',
    'Aisha', 'Sakura', 'Sofia', 'Priya', 'Fatima', 'Isabella', 'Naomi', 'Keisha', 'Lakshmi', 'Aaliyah'
  ];

  const lastNames = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', 'Davis', 'Garcia', 'Rodriguez', 'Wilson',
    'Lee', 'Patel', 'Khan', 'Nguyen', 'Singh', 'Ali', 'Gupta', 'Silva', 'Kim', 'Pereira'
  ];

  const zipCodes = [
    '97201', '97202', '97203', '97204', '97205', // Portland, OR
    '02108', '02116', '02115', '02210', '02129', // Boston, MA
    '10001', '10002', '10003', '10004', '10005', // New York, NY
    '90210', '90211', '90212', '90213', '90214', // Beverly Hills, CA
    '60601', '60602', '60603', '60604', '60605'  // Chicago, IL
  ];
  
  for (let i = 1; i <= NUM_PATIENTS; i++) {
    const gender = genders[Math.floor(Math.random() * genders.length)];
    const firstName = gender === 'Male' 
      ? firstNamesMale[Math.floor(Math.random() * firstNamesMale.length)] 
      : firstNamesFemale[Math.floor(Math.random() * firstNamesFemale.length)];
    const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
    
    // More realistic age distribution - weighted toward 25-65
    let age;
    const ageDistribution = Math.random();
    if (ageDistribution < 0.15) {
      // 15% chance of child/teen (2-17)
      age = randomBetween(2, 17);
    } else if (ageDistribution < 0.70) {
      // 55% chance of adult (25-65)
      age = randomBetween(25, 65);
    } else if (ageDistribution < 0.90) {
      // 20% chance of young adult (18-24)
      age = randomBetween(18, 24);
    } else {
      // 10% chance of senior (66-90)
      age = randomBetween(66, 90);
    }
    
    // 80% have insurance
    const hasInsurance = Math.random() < 0.67;
    const insuranceProvider = hasInsurance 
      ? insuranceProviders[Math.floor(Math.random() * (insuranceProviders.length - 1))].name
      : 'No Insurance';
    
    // Registration date between 2018 and 2024
    const regYear = randomBetween(2018, 2024);
    const regMonth = randomBetween(1, 12);
    const regDay = randomBetween(1, 28);
    const registrationDate = `${regYear}-${String(regMonth).padStart(2, '0')}-${String(regDay).padStart(2, '0')}`;
    
    patients.push({
      patient_id: `PAT${String(i).padStart(4, '0')}`,
      first_name: firstName,
      last_name: lastName,
      name: `${firstName} ${lastName}`,
      gender: gender,
      age: age,
      zip_code: zipCodes[Math.floor(Math.random() * zipCodes.length)],
      registration_date: registrationDate,
      insurance_provider: insuranceProvider,
      is_active: Math.random() < 0.9 // 90% of patients are active
    });
  }
  
  return patients;
}

// Generate appointments and procedures
function generateAppointmentData(patients) {
  const appointments = [];
  const appointmentStatuses = ['Completed', 'No-Show', 'Canceled', 'Rescheduled'];
  const statusProbabilities = [0.85, 0.05, 0.07, 0.03]; // 85% completed, 5% no-show, etc.
  const paymentMethods = ['Credit Card', 'Debit Card', 'Cash', 'Check', 'Insurance Only'];
  
  for (let i = 0; i < NUM_RECORDS; i++) {
    // Select a random patient with bias toward frequent visitors
    const patientIndex = Math.floor(Math.pow(Math.random(), 1.5) * patients.length);
    const patient = patients[patientIndex];
    
    // Create visit date (between registration date and END_DATE)
    const regDate = new Date(patient.registration_date);
    const visitDate = randomDate(regDate > START_DATE ? regDate : START_DATE, END_DATE);
    const formattedVisitDate = formatDate(visitDate);
    const appointmentTime = randomAppointmentTime();
    
    // Extract year and month
    const year = visitDate.getFullYear();
    const month = visitDate.getMonth() + 1;
    
    // Select location 
    const location = locations[Math.floor(Math.random() * locations.length)];

    // Filter providers who work at this location
    const locationProviders = providers.filter(p => p.primary_location === location.id);

    // If no providers available at this location, select a random one (fallback)
    // Otherwise, select from providers at this location
    const provider = locationProviders.length > 0 
      ? locationProviders[Math.floor(Math.random() * locationProviders.length)]
      : providers.find(p => p.primary_location === location.id) || providers[Math.floor(Math.random() * providers.length)];
    
    // Determine appointment status
    let statusRand = Math.random();
    let statusIndex = 0;
    let cumulativeProb = 0;
    
    for (let j = 0; j < statusProbabilities.length; j++) {
      cumulativeProb += statusProbabilities[j];
      if (statusRand <= cumulativeProb) {
        statusIndex = j;
        break;
      }
    }
    
    const appointmentStatus = appointmentStatuses[statusIndex];
    
    // Visit ID
    const visitId = `V${String(i + 1).padStart(6, '0')}`;
    
    // Select 1-3 procedures for this visit
    const numProceduresForVisit = randomBetween(1, 3);
    
    for (let p = 0; p < numProceduresForVisit; p++) {
      // Select a procedure based on age appropriateness
      let procedureIndex;
      const patientAge = patient.age;

      // Age-appropriate procedure selection
      if (patientAge < 18) {
        // For children/teens
        if (Math.random() < 0.7) {
          // Higher chance of preventive, diagnostic, and orthodontic for younger patients
          const youthProcedureCodes = ['D0120', 'D0150', 'D1120', 'D1208', 'D1351', 'D8080'];
          const selectedCode = youthProcedureCodes[Math.floor(Math.random() * youthProcedureCodes.length)];
          procedureIndex = procedures.findIndex(p => p.code === selectedCode);
        } else {
          // Some chance of other procedures
          procedureIndex = Math.floor(Math.random() * procedures.length);
        }
      } else if (patientAge > 55) {
        // For older adults
        if (Math.random() < 0.6) {
          // Higher chance of restorative, endodontic, and implant procedures
          const seniorProcedureCodes = ['D2740', 'D2750', 'D3310', 'D3320', 'D3330', 'D5110', 'D5120', 'D6010', 'D6058'];
          const selectedCode = seniorProcedureCodes[Math.floor(Math.random() * seniorProcedureCodes.length)];
          procedureIndex = procedures.findIndex(p => p.code === selectedCode);
        } else {
          // Some chance of other procedures
          procedureIndex = Math.floor(Math.random() * procedures.length);
        }
      } else {
        // For general adult population
        if (Math.random() < 0.6) { // 60% chance of common procedure
          procedureIndex = Math.floor(Math.random() * 10); // First 10 are common procedures
        } else {
          procedureIndex = Math.floor(Math.random() * procedures.length);
        }
      }

      // Fallback if procedure not found
      if (procedureIndex === -1) {
        procedureIndex = Math.floor(Math.random() * procedures.length);
      }

      const procedure = procedures[procedureIndex];

      // If this is a cleaning procedure, check if patient is due
      if ((procedure.code === 'D1110' || procedure.code === 'D1120') && 
          !isDueForRecall(patient.patient_id, procedure.code, formattedVisitDate)) {
        // Skip this iteration if patient not due for cleaning
        continue;
      }

      // If a cleaning was performed, update the last cleaning date
      if (procedure.code === 'D1110' || procedure.code === 'D1120') {
        patientLastCleaningDate[patient.patient_id] = formattedVisitDate;
      }
      
      // Procedure ID
      const procedureId = `PROC${String(i * 10 + p + 1).padStart(6, '0')}`;
      
      // Only proceed with financial calculations if the appointment was completed
      if (appointmentStatus === 'Completed') {
        // Financial calculations
        const chargedAmount = Math.round(procedure.avg_fee * (0.9 + Math.random() * 0.2));
        
        // Insurance calculations
        const hasInsurance = patient.insurance_provider !== 'No Insurance';
        let insuranceCovered = 0;
        
        if (hasInsurance) {
          // Different insurance providers cover different percentages
          let coverageRate = 0;
          const provider = insuranceProviders.find(p => p.name === patient.insurance_provider);
          coverageRate = provider ? provider.avg_reimbursement_rate : 0.75;
          
          // Add some variation
          coverageRate = Math.max(0.5, Math.min(0.95, coverageRate * (0.9 + Math.random() * 0.2)));
          insuranceCovered = Math.round(chargedAmount * coverageRate);
        }
        
        // Patient responsibility
        const patientResponsibility = chargedAmount - insuranceCovered;
        
        // Discount (15% chance)
        const hasDiscount = Math.random() < 0.15;
        const discountRate = hasDiscount ? (randomBetween(1, 3)) / 10 : 0; // 10%, 20%, or 30% discount
        const discountAmount = Math.round(patientResponsibility * discountRate);
        
        // Final out of pocket
        const outOfPocket = patientResponsibility - discountAmount;
        
        // Payment info
        const isPaid = Math.random() < 0.95; // 95% of procedures are paid
        const amountPaid = isPaid ? outOfPocket : 0;
        const paymentMethod = isPaid ? paymentMethods[Math.floor(Math.random() * paymentMethods.length)] : '';
        
        // Generate a tooth number if applicable
        const needsTooth = ['Restorative', 'Endodontic', 'Periodontic', 'Implant'].includes(procedure.category);
        const toothNumber = needsTooth ? teeth[Math.floor(Math.random() * teeth.length)] : '';
        
        // Treatment plan data
        let treatmentPlanId = '';
        let treatmentPlanCreationDate = '';
        let treatmentPlanCompletionDate = '';
        let treatmentPlanCompletionRate = 0;
        let estimatedTotalCost = chargedAmount;

        // Check if patient has an active treatment plan
        if (activeTreatmentPlans[patient.patient_id]) {
          // Use existing treatment plan
          const existingPlan = activeTreatmentPlans[patient.patient_id];
          treatmentPlanId = existingPlan.id;
          treatmentPlanCreationDate = existingPlan.creationDate;
          estimatedTotalCost = existingPlan.totalCost;
          
          // Increment completion rate based on procedure
          existingPlan.completedProcedures += 1;
          
          // Update completion rate (simple model: each procedure is equal weight)
          treatmentPlanCompletionRate = Math.min(100, 
            Math.round((existingPlan.completedProcedures / existingPlan.totalProcedures) * 100));
          
          // If plan is now complete, set completion date
          if (treatmentPlanCompletionRate >= 100) {
            treatmentPlanCompletionDate = formattedVisitDate;
            // Remove from active plans
            delete activeTreatmentPlans[patient.patient_id];
          }
        } else if (Math.random() < 0.3 && ['Restorative', 'Endodontic', 'Prosthodontic', 'Implant'].includes(procedure.category)) {
          // 30% chance to create new treatment plan for certain procedure categories
          treatmentPlanId = `TP${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`;
          treatmentPlanCreationDate = formattedVisitDate;
          
          // Estimated number of procedures in this plan (1-5)
          const totalProcedures = randomBetween(1, 5);
          
          // Store the new treatment plan
          activeTreatmentPlans[patient.patient_id] = {
            id: treatmentPlanId,
            creationDate: treatmentPlanCreationDate,
            totalProcedures: totalProcedures,
            completedProcedures: 1, // This procedure counts as the first one
            totalCost: estimatedTotalCost * totalProcedures
          };
          
          // Update estimated total cost
          estimatedTotalCost = activeTreatmentPlans[patient.patient_id].totalCost;
          
          // Initial completion rate
          treatmentPlanCompletionRate = Math.round((1 / totalProcedures) * 100);
        }
        
        // Claim information
        const claimStatus = hasInsurance ? 
            (Math.random() < 0.95 ? 'Paid' : (Math.random() < 0.5 ? 'Pending' : 'Denied')) : '';
        const claimSubmissionDate = hasInsurance ? formattedVisitDate : '';
        
        let claimPaymentDate = '';
        if (claimStatus === 'Paid') {
            // Payment typically comes 15-45 days after submission
            const paymentDateObj = new Date(visitDate);
            paymentDateObj.setDate(paymentDateObj.getDate() + randomBetween(15, 45));
            claimPaymentDate = formatDate(paymentDateObj);
        }
        
        // Add to appointments array
        appointments.push({
          Visit_ID: visitId,
          Procedure_ID: procedureId,
          Patient_ID: patient.patient_id,
          Patient_Name: patient.name,
          Patient_Gender: patient.gender,
          Patient_Age: patient.age,
          Patient_Zip_Code: patient.zip_code,
          Location_ID: location.id,
          Location_Name: location.name,
          Provider_ID: provider.id,
          Provider_Name: provider.name,
          Provider_Role: provider.role,
          Provider_Specialty: provider.specialty,
          Date_of_Service: formattedVisitDate,
          Appointment_Time: appointmentTime,
          Appointment_Status: appointmentStatus,
          Procedure_Code: procedure.code,
          Procedure_Description: procedure.description,
          Procedure_Category: procedure.category,
          Procedure_Duration: procedure.duration,
          Tooth_Number: toothNumber,
          Charged_Amount: chargedAmount,
          Insurance_Provider: patient.insurance_provider,
          Insurance_Covered_Amount: insuranceCovered,
          Patient_Responsibility: patientResponsibility,
          Discount_Applied: discountAmount,
          Out_of_Pocket: outOfPocket,
          Amount_Paid: amountPaid,
          Payment_Method: paymentMethod,
          Payment_Status: isPaid ? 'Paid' : 'Outstanding',
          Is_New_Patient: new Date(patient.registration_date).toISOString().split('T')[0] === formattedVisitDate,
          Insurance_Claim_Status: claimStatus,
          Insurance_Claim_Submission_Date: claimSubmissionDate,
          Insurance_Claim_Payment_Date: claimPaymentDate,
          Google_Rating: location.google_rating,
          Treatment_Plan_ID: treatmentPlanId,
          Treatment_Plan_Creation_Date: treatmentPlanCreationDate,
          Treatment_Plan_Completion_Date: treatmentPlanCompletionDate,
          Treatment_Plan_Completion_Rate: treatmentPlanCompletionRate,
          Estimated_Total_Cost: estimatedTotalCost,
          Year: year,
          Month: month
        });
      } else {
        // For non-completed appointments, we still add basic info without financial data
        appointments.push({
          Visit_ID: visitId,
          Procedure_ID: procedureId,
          Patient_ID: patient.patient_id,
          Patient_Name: patient.name,
          Patient_Gender: patient.gender,
          Patient_Age: patient.age,
          Patient_Zip_Code: patient.zip_code,
          Location_ID: location.id,
          Location_Name: location.name,
          Provider_ID: provider.id,
          Provider_Name: provider.name,
          Provider_Role: provider.role,
          Provider_Specialty: provider.specialty,
          Date_of_Service: formattedVisitDate,
          Appointment_Time: appointmentTime,
          Appointment_Status: appointmentStatus,
          Procedure_Code: '',
          Procedure_Description: '',
          Procedure_Category: '',
          Procedure_Duration: 0,
          Tooth_Number: '',
          Charged_Amount: 0,
          Insurance_Provider: patient.insurance_provider,
          Insurance_Covered_Amount: 0,
          Patient_Responsibility: 0,
          Discount_Applied: 0,
          Out_of_Pocket: 0,
          Amount_Paid: 0,
          Payment_Method: '',
          Payment_Status: '',
          Is_New_Patient: new Date(patient.registration_date).toISOString().split('T')[0] === formattedVisitDate,
          Insurance_Claim_Status: '',
          Insurance_Claim_Submission_Date: '',
          Insurance_Claim_Payment_Date: '',
          Google_Rating: location.google_rating,
          Treatment_Plan_ID: '',
          Treatment_Plan_Creation_Date: '',
          Treatment_Plan_Completion_Date: '',
          Treatment_Plan_Completion_Rate: 0,
          Estimated_Total_Cost: 0,
          Year: year,
          Month: month
        });
      }
    }
  }
  
  // Sort appointments by date and time
  appointments.sort((a, b) => {
    const dateA = new Date(a.Date_of_Service + 'T' + a.Appointment_Time);
    const dateB = new Date(b.Date_of_Service + 'T' + b.Appointment_Time);
    return dateA - dateB;
  });
  
  return appointments;
}

// Generate the datasets
const patients = generatePatients();
const appointments = generateAppointmentData(patients);

// Convert arrays to CSV
function convertToCSV(data) {
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

// Save datasets to CSV files
const appointmentsCSV = convertToCSV(appointments);
fs.writeFileSync('Pat_App_Data.csv', appointmentsCSV);

console.log(`Created ${appointments.length} dental appointment records`);
console.log(`Data saved to 'Pat_App_Data.csv'`);

// Calculate some metrics for verification
const totalCharged = appointments.reduce((sum, a) => sum + (a.Charged_Amount || 0), 0);
const totalCollected = appointments.reduce((sum, a) => sum + (a.Amount_Paid || 0), 0);
console.log(`Total charged: $${totalCharged.toLocaleString()}`);
console.log(`Total collected: $${totalCollected.toLocaleString()}`);
console.log(`Collection rate: ${(totalCollected / totalCharged * 100).toFixed(2)}%`);

// Count records by year
const byYear = {};
appointments.forEach(a => {
  byYear[a.Year] = (byYear[a.Year] || 0) + 1;
});
console.log("Records by year:", byYear);

// Count unique patients, locations, and providers
const uniquePatients = new Set(appointments.map(a => a.Patient_ID)).size;
const uniqueLocations = new Set(appointments.map(a => a.Location_ID)).size;
const uniqueProviders = new Set(appointments.map(a => a.Provider_ID)).size;
console.log(`Number of unique patients: ${uniquePatients}`);
console.log(`Number of unique locations: ${uniqueLocations}`);
console.log(`Number of unique providers: ${uniqueProviders}`);