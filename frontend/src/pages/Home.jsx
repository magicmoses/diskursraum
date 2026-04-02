import { useNavigate } from 'react-router-dom'

const TOPICS = [
  { id: 'migration', label: 'Migration & Asylum Policy', emoji: '🇩🇪', description: 'Debate on immigration and asylum in Germany' },
  { id: 'basic_income', label: 'Unconditional Basic Income', emoji: '💰', description: 'Should Germany introduce a universal basic income?' },
  { id: 'nuclear_energy', label: 'Nuclear Energy', emoji: '⚛️', description: 'Should nuclear power be part of Germany\'s energy mix?' },
  { id: 'military_service', label: 'Mandatory Military Service', emoji: '🪖', description: 'Should Germany reintroduce compulsory military service?' },
  { id: 'retirement_age', label: 'Retirement at 70', emoji: '👴', description: 'Should the retirement age be raised to 70?' },
  { id: 'speed_limit', label: 'Autobahn Speed Limit', emoji: '🚗', description: 'Should Germany introduce a general speed limit on the Autobahn?' },
  { id: 'euthanasia', label: 'Assisted Dying', emoji: '💉', description: 'Should assisted dying be legalized in Germany?' },
  { id: 'wealth_tax', label: 'Wealth Tax', emoji: '💸', description: 'Should Germany introduce a wealth tax for high earners?' },
  { id: 'ai_jobs', label: 'AI Replacing Jobs', emoji: '🤖', description: 'Will AI replace human workers — and who is most at risk?' },
  { id: 'ai_regulation', label: 'AI Regulation & Ethics', emoji: '🧠', description: 'How should AI be regulated in Europe?' },
]

export default function Home() {
  const navigate = useNavigate()

  return (
    <div className="space-y-8">

      {/* Header */}
      <div className="max-w-2xl">
        <h1 className="text-3xl font-bold mb-2">Consensus Analysis</h1>
        <p className="text-gray-400 leading-relaxed">
          Select a topic to analyze bridging statements — content that finds
          approval across ideologically distinct opinion clusters, not just
          within echo chambers.
        </p>
      </div>

      {/* Topic Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {TOPICS.map(topic => (
          <TopicCard
            key={topic.id}
            topic={topic}
            onClick={() => navigate(`/topic/${topic.id}`)}
          />
        ))}
      </div>

      {/* Footer Note */}
      <p className="text-gray-600 text-sm">
        Inspired by Taiwan's{' '}
        <a href="https://info.vtaiwan.tw/" target="_blank" rel="noopener noreferrer"
          className="text-gray-500 hover:text-gray-300 underline">
          vTaiwan
        </a>{' '}
        civic deliberation platform, the{' '}
        <a href="https://pol.is" target="_blank" rel="noopener noreferrer"
          className="text-gray-500 hover:text-gray-300 underline">
          Pol.is
        </a>{' '}
        bridging algorithm, and the book{' '}
        <a href="https://www.plurality.net/" target="_blank" rel="noopener noreferrer"
          className="text-gray-500 hover:text-gray-300 underline">
          Plurality
        </a>{' '}
        by Audrey Tang & E. Glen Weyl.
      </p>

    </div>
  )
}

function TopicCard({ topic, onClick }) {
  return (
    <button
      onClick={onClick}
      className="bg-gray-900 border border-gray-800 rounded-xl p-5 text-left hover:border-gray-600 hover:bg-gray-800 transition-all duration-200 group"
    >
      <div className="text-3xl mb-3">{topic.emoji}</div>
      <div className="font-semibold text-white mb-1 group-hover:text-blue-400 transition-colors">
        {topic.label}
      </div>
      <div className="text-gray-400 text-sm leading-relaxed">
        {topic.description}
      </div>
    </button>
  )
}