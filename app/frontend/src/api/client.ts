import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000',
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg: string }) => d.msg).join(', ')
          : error.message ?? 'Error desconocido'
    return Promise.reject(new Error(message))
  },
)

export default client
