import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const http = axios.create({ baseURL: BASE_URL })

// Export base URL so fetch() calls (file upload) can use it too
export const API_URL = BASE_URL

export const queryRecords           = (table, filters = {})  => http.post('/query',  { table, filters }).then(r => r.data)
export const createRecord           = (table, data)          => http.post('/create', { table, data    }).then(r => r.data)
export const updateRecord           = (table, filters, data) => http.post('/update', { table, filters, data }).then(r => r.data)
export const deleteRecord           = (table, filters)       => http.post('/delete', { table, filters }).then(r => r.data)
export const getPatientAppointments = (limit = 100)          => http.get('/joins/patient-appointments', { params: { limit } }).then(r => r.data)
export const getPatientOrders       = (limit = 100)          => http.get('/joins/patient-orders',        { params: { limit } }).then(r => r.data)
export const getPrescriptionDetails = (params = {})          => http.get('/joins/prescription-details',  { params }).then(r => r.data)
export const getLowStock            = ()                     => http.get('/inventory/low-stock').then(r => r.data)
export const getDashboard           = ()                     => http.get('/analytics/dashboard').then(r => r.data)
export const generateOrder          = (prescriptionId)       => http.post(`/prescriptions/${prescriptionId}/generate-order`, {}).then(r => r.data)
export const searchMedicalRecords   = (patient_id, query)    => http.post('/records/search',   { patient_id, query }).then(r => r.data)
export const addMedicalNote         = (patient_id, text)     => http.post('/records/add-note', { patient_id, text  }).then(r => r.data)
export const chatWithAgent          = (message, history = []) => http.post('/chat', { message, history }).then(r => r.data)
