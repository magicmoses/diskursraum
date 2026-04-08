import { useNavigate } from 'react-router-dom'

const TOPICS = [
  {
    id: 'migration',
    label: 'Migration & Asylpolitik',
    emoji: '🌍',
    description: 'Einwanderung, Asylrecht und Integration — eines der polarisierendsten Themen Deutschlands'
  },
  {
    id: 'energy_transition',
    label: 'Energiewende',
    emoji: '⚡',
    description: 'Atomkraft, erneuerbare Energien und Klimapolitik — zwischen Versorgungssicherheit und Klimaschutz'
  },
  {
    id: 'retirement',
    label: 'Rente & Altersvorsorge',
    emoji: '👴',
    description: 'Rentenpolitik, Rentenalter und Generationengerechtigkeit als gesellschaftliche Dauerdebatte'
  },
  {
    id: 'wealth_tax',
    label: 'Vermögenssteuer & Umverteilung',
    emoji: '💸',
    description: 'Besteuerung großer Vermögen, Erbschaftssteuer und soziale Gerechtigkeit'
  },
  {
    id: 'digitalization',
    label: 'Digitale Transformation & KI',
    emoji: '🤖',
    description: 'Digitalisierung, Künstliche Intelligenz und gesellschaftlicher Wandel durch Technologie'
  },
]

export default function Home() {
  const navigate = useNavigate()

  return (
    <div className="space-y-8">

      {/* Header */}
      <div className="max-w-2xl">
        <h1 className="text-3xl font-bold mb-2">Consensus Analysis</h1>
        <p className="text-gray-400 leading-relaxed">
          Wähle ein Thema um Bridging Statements zu analysieren — Aussagen die
          über ideologisch unterschiedliche Meinungsgruppen hinweg Zustimmung finden.
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

      {/* Footer */}
      <p className="text-gray-600 text-sm">
        Inspired by Taiwan's{' '}
        <a href="https://info.vtaiwan.tw/" target="_blank" rel="noopener noreferrer"
          className="text-gray-500 hover:text-gray-300 underline">vTaiwan</a>{' '}
        and the{' '}
        <a href="https://pol.is" target="_blank" rel="noopener noreferrer"
          className="text-gray-500 hover:text-gray-300 underline">Pol.is</a>{' '}
        bridging algorithm.{' '}
        <a href="https://www.plurality.net/" target="_blank" rel="noopener noreferrer"
          className="text-gray-500 hover:text-gray-300 underline">Plurality</a>{' '}
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