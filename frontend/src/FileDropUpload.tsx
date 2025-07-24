import './App.css'
import axios from 'axios'
import {useRef, useState} from 'react'
import {Upload} from 'lucide-react'
const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL

import type {FileType} from './types'

function FileDropUpload({newFileUploaded}: {
  newFileUploaded: (newFile: FileType) => void
}) {
  const [showDropZone, setShowDropZone] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const handleUpload = async (file: File) => {
    const url = VITE_API_BASE_URL + '/api/v1/upload'
    const formData = new FormData()
    formData.append('file', file)
    setIsUploading(true)
    setShowDropZone(false)
    try {
      const response = await axios.post(url, formData)
      const responseObject = JSON.parse(response.data.reply)
      newFileUploaded(responseObject)
    } catch (error) {
      console.error('Error: ', error)
    } finally {
      setIsUploading(false)
    }
  }

  const onDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const files = event.dataTransfer.files
    if (files.length > 0) handleUpload(files[0])
  }

  const onFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (files && files.length > 0) handleUpload(files[0])
  }

  return (
    <div className='mt-4'>
      <button
        onClick={() => setShowDropZone(prev => !prev)}
        className="flex items-center gap-2 py-2 px-3 border-gray-600 bg-neutral-100 rounded cursor-pointer"
        disabled={isUploading}
      >
        <Upload size={18} />
        Upload File
      </button>
      {isUploading && (
        <div className='mt-3'>
          <span className="ml-3 text-blue-600">Uploading...</span>
        </div>
      )}

      {showDropZone && (
        <div
          onDragOver={e => e.preventDefault()}
          onDrop={onDrop}
          className="py-4 px-10 mt-3 border-2 border-dashed border-gray-500 text-center">
          Drop file here or{' '}
          <span
            onClick={() => fileInputRef.current?.click()}
            style={{textDecoration: 'underline', color: 'blue', cursor: 'pointer'}}>
            click to choose
          </span>
          <input
            ref={fileInputRef}
            type="file"
            style={{display: 'none'}}
            onChange={onFileSelect}
            disabled={isUploading}
          />
        </div>
      )}
    </div>
  )
}

export default FileDropUpload
