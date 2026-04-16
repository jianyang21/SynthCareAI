import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'

export default function SharedProfile() {
  const { user } = useAuth()
  const [file, setFile] = useState(null)
  const [recordType, setRecordType] = useState('general_report')
  const [status, setStatus] = useState({ loading: false, message: '', isError: false })

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0])
      setStatus({ loading: false, message: '', isError: false }) // Reset status on new file
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file) {
      setStatus({ loading: false, message: 'Please select a PDF document to upload.', isError: true })
      return
    }

    setStatus({ loading: true, message: 'Uploading and analyzing document...', isError: false })

    const formData = new FormData()
    formData.append('file', file)
    formData.append('record_type', recordType)
    
    // Using the authenticated user's ID. 
    // Fallback to 1 just in case your auth context uses a different key for the ID.
    formData.append('patient_id', user?.id || 1) 
    
    if (user?.role === 'doctor') {
      formData.append('doctor_id', user.id)
    }

    try {
      // Replace with your actual API base URL if different
      const response = await fetch('http://localhost:8000/records/build-page-index', {
        method: 'POST',
        body: formData,
        // Note: Do not set 'Content-Type' manually when sending FormData in Vite/React. 
        // The browser automatically sets it with the correct multipart boundary.
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to upload document')
      }

      const data = await response.json()
      
      setStatus({ 
        loading: false, 
        message: `Success! Indexed ${data.pages_indexed} pages. Summary: ${data.summary.substring(0, 100)}...`, 
        isError: false 
      })
      
      // Reset form
      setFile(null)
      e.target.reset()

    } catch (error) {
      setStatus({ loading: false, message: error.message, isError: true })
    }
  }

  return (
    <div className="min-h-screen bg-bg p-6 md:p-12">
      <div className="max-w-3xl mx-auto space-y-8">
        
        {/* Profile Header */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">My Profile</h1>
          <div className="text-gray-600">
            <p><span className="font-medium text-gray-800">Role:</span> <span className="capitalize">{user?.role}</span></p>
            <p><span className="font-medium text-gray-800">Email:</span> {user?.email || 'N/A'}</p>
          </div>
        </div>

        {/* Document Upload Section */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Add Medical Document</h2>
          <p className="text-sm text-gray-500 mb-6">
            Upload PDF records to automatically index and summarize them for your medical history.
          </p>

          <form onSubmit={handleUpload} className="space-y-4">
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Record Type</label>
              <select 
                value={recordType}
                onChange={(e) => setRecordType(e.target.value)}
                className="w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="general_report">General Report</option>
                <option value="lab_result">Lab Result</option>
                <option value="prescription">Prescription</option>
                <option value="discharge_summary">Discharge Summary</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">PDF File</label>
              <input 
                type="file" 
                accept="application/pdf"
                onChange={handleFileChange}
                className="w-full border border-gray-300 rounded-md p-2 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>

            <button 
              type="submit" 
              disabled={status.loading}
              className={`w-full py-2 px-4 rounded-md text-white font-medium transition-colors ${
                status.loading ? 'bg-blue-300 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {status.loading ? 'Processing...' : 'Upload & Index'}
            </button>

            {/* Status Message Display */}
            {status.message && (
              <div className={`p-4 rounded-md text-sm mt-4 ${status.isError ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
                {status.message}
              </div>
            )}

          </form>
        </div>

      </div>
    </div>
  )
}