import { useState, useEffect } from 'react'
import { X, Upload, Globe, FileText, Trash2, CheckCircle, AlertCircle } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'

export default function ContentManagement({ isOpen, onClose }) {
  const { user, getAuthHeaders } = useAuth()
  const [activeTab, setActiveTab] = useState('upload')
  const [contentList, setContentList] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isSubmittingUrl, setIsSubmittingUrl] = useState(false)
  const [urlInput, setUrlInput] = useState('')

  useEffect(() => {
    if (isOpen) {
      // Add a small delay to ensure auth state is loaded
      const timer = setTimeout(() => {
        fetchContentList()
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [isOpen])

  const fetchContentList = async () => {
    setIsLoading(true)
    try {
      // Check if user is authenticated
      if (!user) {
        console.log('No user found, cannot fetch content')
        toast.error('Please login to view your documents')
        return
      }
      
      const headers = await getAuthHeaders()
      console.log('Fetching content with headers:', headers)
      
      if (!headers.Authorization) {
        console.log('No authorization header found')
        toast.error('Authentication required. Please login again.')
        return
      }
      
      const response = await fetch('/api/content/list', {
        headers
      })

      console.log('Content list response status:', response.status)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('Content list error:', errorText)
        throw new Error(`Failed to fetch content: ${response.status} ${errorText}`)
      }

      const data = await response.json()
      console.log('Content list data:', data)
      setContentList(data.content || [])
    } catch (error) {
      console.error('Error fetching content:', error)
      toast.error('Failed to load content: ' + error.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return

    setIsUploading(true)
    const uploadPromises = Array.from(files).map(async (file) => {
      const formData = new FormData()
      formData.append('file', file)

      try {
        // Get token directly from multiple sources
        let token = null
        
        // Try from user context first
        if (user && user.token) {
          token = user.token
          console.log('Token from user context:', token.substring(0, 20) + '...')
        }
        
        // Try from localStorage if not in context
        if (!token) {
          token = localStorage.getItem('auth_token')
          console.log('Token from localStorage:', token ? token.substring(0, 20) + '...' : 'null')
        }
        
        // Try from auth context as fallback
        if (!token) {
          const authHeaders = await getAuthHeaders()
          token = authHeaders.Authorization?.replace('Bearer ', '')
          console.log('Token from getAuthHeaders:', token ? token.substring(0, 20) + '...' : 'null')
        }
        
        if (!token) {
          throw new Error('No authentication token available. Please login again.')
        }
        
        const headers = {
          'Authorization': `Bearer ${token}`
          // Don't set Content-Type for FormData - browser will set it automatically
        }
        
        console.log('Final upload headers:', { Authorization: `Bearer ${token.substring(0, 20)}...` })
        
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
          headers: headers
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || 'Upload failed')
        }

        const data = await response.json()
        toast.success(`${file.name} uploaded successfully`)
        return data
      } catch (error) {
        console.error(`Error uploading ${file.name}:`, error)
        toast.error(`Failed to upload ${file.name}: ${error.message}`)
        return null
      }
    })

    await Promise.all(uploadPromises)
    setIsUploading(false)
    fetchContentList()
  }

  const handleUrlSubmit = async (e) => {
    e.preventDefault()
    if (!urlInput.trim()) return

    setIsSubmittingUrl(true)
    try {
      const formData = new FormData()
      formData.append('url', urlInput.trim())

      const response = await fetch('/api/content/url', {
        method: 'POST',
        body: formData,
        headers: await getAuthHeaders()
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'URL submission failed')
      }

      const data = await response.json()
      toast.success('URL content processed successfully')
      setUrlInput('')
      fetchContentList()
    } catch (error) {
      console.error('Error submitting URL:', error)
      toast.error(`Failed to process URL: ${error.message}`)
    } finally {
      setIsSubmittingUrl(false)
    }
  }

  const handleDeleteContent = async (contentId) => {
    if (!confirm('Are you sure you want to delete this content?')) return

    try {
      const response = await fetch(`/api/content/${contentId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        throw new Error('Failed to delete content')
      }

      toast.success('Content deleted successfully')
      fetchContentList()
    } catch (error) {
      console.error('Error deleting content:', error)
      toast.error('Failed to delete content')
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getContentIcon = (contentType, source) => {
    if (contentType === 'url') return <Globe className="h-5 w-5 text-blue-600" />
    if (source?.includes('.pdf')) return <FileText className="h-5 w-5 text-red-600" />
    if (source?.includes('.docx') || source?.includes('.doc')) return <FileText className="h-5 w-5 text-blue-600" />
    if (source?.includes('.txt')) return <FileText className="h-5 w-5 text-gray-600" />
    if (source?.includes('.pptx')) return <FileText className="h-5 w-5 text-orange-600" />
    return <FileText className="h-5 w-5 text-gray-600" />
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75 modal-backdrop"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="inline-block w-full max-w-4xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-slate-800 shadow-xl rounded-2xl">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">Content Management</h2>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex space-x-1 mb-6 bg-slate-700 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab('upload')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'upload'
                  ? 'bg-white text-primary-700 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Upload Files
            </button>
            <button
              onClick={() => setActiveTab('url')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'url'
                  ? 'bg-white text-primary-700 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Add URL
            </button>
            <button
              onClick={() => setActiveTab('list')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'list'
                  ? 'bg-white text-primary-700 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              My Content ({contentList.length})
            </button>
          </div>

          {/* Tab Content */}
          <div className="min-h-[400px]">
            {activeTab === 'upload' && (
              <FileUploadTab 
                onFileUpload={handleFileUpload}
                isUploading={isUploading}
              />
            )}

            {activeTab === 'url' && (
              <UrlSubmitTab 
                urlInput={urlInput}
                setUrlInput={setUrlInput}
                onSubmit={handleUrlSubmit}
                isSubmitting={isSubmittingUrl}
              />
            )}

            {activeTab === 'list' && (
              <ContentListTab 
                contentList={contentList}
                isLoading={isLoading}
                onDelete={handleDeleteContent}
                onRefresh={fetchContentList}
                getContentIcon={getContentIcon}
                formatFileSize={formatFileSize}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// File Upload Tab Component
function FileUploadTab({ onFileUpload, isUploading }) {
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileUpload(e.dataTransfer.files)
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileUpload(e.target.files)
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Upload Documents</h3>
        <p className="text-gray-600">
          Upload PDF, DOCX, TXT, PPTX, or CSV files to analyze their content
        </p>
      </div>

      {/* Drop Zone */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive ? 'dropzone-active' : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          multiple
          accept=".pdf,.docx,.doc,.txt,.pptx,.csv,.md"
          onChange={handleFileInput}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isUploading}
        />
        
        <div className="space-y-2">
          <Upload className="mx-auto h-8 w-8 text-gray-400" />
          <p className="text-lg font-medium text-gray-900">
            {isUploading ? 'Uploading...' : 'Drag and drop files here'}
          </p>
          <p className="text-gray-600">or click to select files</p>
          <p className="text-sm text-gray-500">
            Supports: PDF, DOCX, TXT, PPTX, CSV, MD (Max 10MB each)
          </p>
        </div>
      </div>

      {isUploading && (
        <div className="flex items-center justify-center space-x-2 text-primary-600">
          <div className="w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
          <span>Processing files...</span>
        </div>
      )}
    </div>
  )
}

// URL Submit Tab Component
function UrlSubmitTab({ urlInput, setUrlInput, onSubmit, isSubmitting }) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <Globe className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Add Web Content</h3>
        <p className="text-gray-600">
          Submit URLs to scrape and analyze web content
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Website URL
          </label>
          <input
            type="url"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="https://example.com/article"
            className="input-field"
            required
          />
        </div>

        <button
          type="submit"
          disabled={!urlInput.trim() || isSubmitting}
          className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? (
            <div className="flex items-center justify-center space-x-2">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Processing URL...</span>
            </div>
          ) : (
            'Add Content'
          )}
        </button>
      </form>

      <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
        <p className="text-sm text-blue-800">
          💡 <strong>Tip:</strong> The system will automatically extract and analyze the main content from the webpage, including articles, blog posts, and other text-based content.
        </p>
      </div>
    </div>
  )
}

// Content List Tab Component
function ContentListTab({ contentList, isLoading, onDelete, onRefresh, getContentIcon, formatFileSize }) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-2 text-gray-600">
          <div className="w-4 h-4 border-2 border-gray-600 border-t-transparent rounded-full animate-spin" />
          <span>Loading content...</span>
        </div>
      </div>
    )
  }

  if (contentList.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No content yet</h3>
        <p className="text-gray-600 mb-4">
          Upload files or add URLs to get started with personalized responses
        </p>
        <button
          onClick={onRefresh}
          className="btn-primary"
        >
          Refresh
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">
          Your Content ({contentList.length} items)
        </h3>
        <button
          onClick={onRefresh}
          className="btn-ghost text-sm"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-3">
        {contentList.map((item) => (
          <div key={item.content_id} className="card p-4">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1">
                {getContentIcon(item.metadata?.type, item.metadata?.filename || item.metadata?.url)}
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-gray-900 truncate">
                    {item.metadata?.title || item.metadata?.filename || item.metadata?.url}
                  </h4>
                  <p className="text-sm text-gray-600">
                    {item.metadata?.type === 'url' ? 'Web Content' : 'Document'}
                    {item.metadata?.size && ` • ${formatFileSize(item.metadata.size)}`}
                  </p>
                  <p className="text-xs text-gray-500">
                    Added {new Date(item.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              
              <button
                onClick={() => onDelete(item.content_id)}
                className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                title="Delete content"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
