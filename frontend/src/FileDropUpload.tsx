import axios from 'axios'
const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL

function FileDropUpload() {
  const onDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const url = VITE_API_BASE_URL + '/api/v1/upload'
    const files = event.dataTransfer.files
    const formData = new FormData()
    formData.append('file', files[0])
    try {
      const response = await axios.post(url, formData)
      console.log(response)
    } catch (error) {
      console.error('Error: ', error)
    }
  }

  return (
    <div
      onDragOver={event => event.preventDefault()}
      onDrop={onDrop}
      style={{border: '2px dashed #888', padding: 40}}>
      Drop file here
    </div>
  )
}

export default FileDropUpload
