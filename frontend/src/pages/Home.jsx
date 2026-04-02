import { useNavigate } from 'react-router-dom'

const TOPICS = [
  { id: 'migration', label: 'Migration & Asylpolitik', emoji: '🇩🇪', description: 'Debatte über Einwanderung und Asyl in Deutschland' },
  { id: 'basic_income', label: 'Grundeinkommen', emoji: '💰', description: 'Sollte Deutschland ein bedingungsloses Grundeinkommen einführen?' },
  { id: 'nuclear_energy', label: 'Atomkraft', emoji: '⚛️', description: 'Sollte Kernenergie Teil des deutschen Energiemix sein?' },
  { id: 'military_service', label: 'Wehrpflicht', emoji: '🪖', description: 'Sollte Deutschland die allgemeine Wehrpflicht wieder einführen?' },
  { id: 'retirement_age', label: 'Rente mit 70', emoji: '👴', description: 'Sollte das Renteneintrittsalter auf 70 angehoben werden?' },
  { id: 'speed_limit', label: 'Tempolimit Autobahn', emoji: '🚗', description: 'Sollte Deutschland ein generelles Tempolimit auf der Autobahn einführen?' },
  { id: 'euthanasia', label: 'Sterbehilfe', emoji: '💉', description: 'Sollte aktive Sterbehilfe in Deutschland legalisiert werden?' },
  { id: 'wealth_tax', label: 'Vermögenssteuer', emoji: '💸', description: 'Sollte Deutschland eine Vermögenssteuer für Hochvermögende einführen?' },
  { id: 'ai_jobs', label: 'KI ersetzt Jobs', emoji: '🤖', description: 'Wird KI menschliche Arbeit ersetzen — und wen trifft es zuerst?' },
  { id: 'ai_regulation', label: 'KI Regulierung', emoji: '🧠', description: 'Wie sollte KI in Europa reguliert werden?' },
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