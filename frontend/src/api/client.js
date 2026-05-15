import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8001',
})

// ── Medienspiegel ─────────────────────────────────
export const getOverview          = () => api.get('/stats/overview').then(r => r.data)
export const getCrawlHistory      = () => api.get('/stats/crawl-history').then(r => r.data)
export const getArticlesPerDay    = () => api.get('/stats/articles-per-day').then(r => r.data)
export const getPublishingTimes   = () => api.get('/stats/publishing-times').then(r => r.data)
export const getWeekdayActivity   = () => api.get('/stats/weekday-activity').then(r => r.data)
export const getSourceDetails     = () => api.get('/stats/source-details').then(r => r.data)
export const getEmotionsPerBias   = () => api.get('/stats/emotions-per-bias').then(r => r.data)
export const getEditorialProfiles = (daysBack = 14) =>
  api.get(`/stats/editorial-profiles?days_back=${daysBack}`).then(r => r.data)
export const getTrendingTopics    = (daysBack = 7, topN = 20) =>
  api.get(`/topics/trending?days_back=${daysBack}&top_n=${topN}`).then(r => r.data)
export const getTopicAnalysis     = (topicId) =>
  api.get(`/topic/${topicId}`).then(r => r.data)

// ── Frag nach ─────────────────────────────────────
export const searchManifestos = (query, parties = [], years = []) =>
  api.get('/frag-nach/search', { params: {
    query,
    parties: parties.join(',') || 'all',
    years:   years.join(',')   || 'all',
    limit:   5,
  }}).then(r => r.data)

// ── Parteiprogramme ───────────────────────────────
export const getManifestoYear        = (year) =>
  api.get(`/manifestos/${year}`).then(r => r.data)
export const getHistoricalAnalysis   = () =>
  api.get('/manifestos/historical').then(r => r.data)
export const getCategoryDistribution = (year) =>
  api.get(`/manifestos/categories/${year}`).then(r => r.data)
