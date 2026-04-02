import { useParams, useNavigate } from 'react-router-dom'

export default function TopicView() {
  const { topicId } = useParams()
  const navigate = useNavigate()

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate('/')}
        className="text-gray-400 hover:text-white text-sm flex items-center gap-2"
      >
        ← Back to Topics
      </button>
      <h1 className="text-3xl font-bold capitalize">
        {topicId.replace(/_/g, ' ')}
      </h1>
      <p className="text-gray-400">
        Cluster analysis coming soon...
      </p>
    </div>
  )
}