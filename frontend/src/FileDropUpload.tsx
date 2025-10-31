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
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const handleUpload = async (file: File) => {
    const url = VITE_API_BASE_URL + '/api/v1/upload'
    const formData = new FormData()
    formData.append('file', file)
    try {
      const response = await axios.post(url, formData)
      const responseObject = JSON.parse(response.data.reply)
      newFileUploaded(responseObject)
    } catch (error) {
      console.error('Error: ', error)
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
    <div>
      <button
        onClick={() => setShowDropZone(prev => !prev)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 12px',
          border: '1px solid #ccc',
          borderRadius: 4,
          background: '#f8f8f8',
          cursor: 'pointer'
        }}>
        <Upload size={18} />
        Upload File
      </button>

      {showDropZone && (
        <div
          onDragOver={e => e.preventDefault()}
          onDrop={onDrop}
          style={{
            border: '2px dashed #888',
            padding: 40,
            marginTop: 20,
            textAlign: 'center'
          }}>
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
          />
        </div>
      )}
    </div>
  )
}

export default FileDropUpload
