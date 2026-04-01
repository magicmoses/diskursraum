import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8001',
})

export const getOverview = () => api.get('/stats/overview').then(r => r.data)
export const getCrawlHistory = () => api.get('/stats/crawl-history').then(r => r.data)
export const getArticlesPerDay = () => api.get('/stats/articles-per-day').then(r => r.data)
export const getBiasOverTime = () => api.get('/stats/bias-over-time').then(r => r.data)
export const getTopics = () => api.get('/stats/topics').then(r => r.data)