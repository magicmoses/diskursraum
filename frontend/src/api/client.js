import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8001',
})

export const getOverview = () => api.get('/stats/overview').then(r => r.data)
export const getCrawlHistory = () => api.get('/stats/crawl-history').then(r => r.data)
export const getArticlesPerDay = () => api.get('/stats/articles-per-day').then(r => r.data)
export const getBiasOverTime = () => api.get('/stats/bias-over-time').then(r => r.data)
export const getTopics = () => api.get('/stats/topics').then(r => r.data)
export const getTrendingTopics = (daysBack = 7, topN = 20) =>
  api.get(`/topics/trending?days_back=${daysBack}&top_n=${topN}`).then(r => r.data)
export const getPublishingTimes = () => api.get('/stats/publishing-times').then(r => r.data)
export const getWeekdayActivity = () => api.get('/stats/weekday-activity').then(r => r.data)
export const getSourceDetails = () => api.get('/stats/source-details').then(r => r.data)
export const getSentimentPerSource = () => api.get('/stats/sentiment-per-source').then(r => r.data)
export const getSentimentPerBias = () => api.get('/stats/sentiment-per-bias').then(r => r.data)
export const getBiasFocus = (daysBack = 7) => api.get(`/stats/bias-focus?days_back=${daysBack}`).then(r => r.data)
export const getNeutralityCheck = () => api.get('/stats/neutrality-check').then(r => r.data)
export const getSourceDeepDive = (sourceId, daysBack = 30) =>
  api.get(`/stats/source-deep-dive/${sourceId}?days_back=${daysBack}`).then(r => r.data)
export const getLeftRightComparison = (daysBack = 14) =>
  api.get(`/stats/left-right-comparison?days_back=${daysBack}`).then(r => r.data)
export const getEmotionsPerBias = () => api.get('/stats/emotions-per-bias').then(r => r.data)
export const getEmotionsPerSource = () => api.get('/stats/emotions-per-source').then(r => r.data)
export const getEmotionTrends = (daysBack = 14) => api.get(`/stats/emotion-trends?days_back=${daysBack}`).then(r => r.data)
export const getLeftRightEmotions = () => api.get('/stats/left-right-emotions').then(r => r.data)
export const getTopicAnalysis = (topicId) =>
  api.get(`/topic/${topicId}`).then(r => r.data)
export const getTopicSummaries = () =>
  api.get('/topics/summaries').then(r => r.data)