import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { PARTY_NAMES, TOOLTIP_STYLE } from '../../constants/colors'

const PARTY_HEX = {
  cdu_csu: '#E8E8E8',
  spd:     '#E3000F',
  gruene:  '#1AA037',
  fdp:     '#FFED00',
  afd:     '#009EE0',
  linke:   '#BE3075',
}

const TOPIC_LABELS = {
  migration:        'Migration',
  energy_transition:'Energiewende',
  retirement:       'Rente',
  wealth_tax:       'Vermögen',
  digitalization:   'Digitalisierung',
}

export default function ForceGraph({ data, year }) {
  const svgRef    = useRef(null)
  const [activeTopic, setActiveTopic] = useState(null)
  const [tooltip, setTooltip]         = useState(null)

  const yearKey  = String(year)
  const graphData = data?.graphs_by_year?.[yearKey]

  useEffect(() => {
    if (!graphData || !svgRef.current) return

    const el    = svgRef.current
    const width = el.clientWidth || 700
    const height = 420

    const svg = d3.select(el)
    svg.selectAll('*').remove()

    let rawNodes, rawEdges
    if (activeTopic && graphData.topic_subgraphs?.[activeTopic]) {
      const sub = graphData.topic_subgraphs[activeTopic]
      rawNodes  = sub.nodes
      rawEdges  = sub.edges
    } else {
      rawNodes = graphData.nodes
      rawEdges = graphData.edges
    }

    if (!rawNodes?.length) return

    const nodes = rawNodes.map(n => ({ ...n }))
    const edges = rawEdges.map(e => ({ ...e }))

    const weights    = edges.map(e => e.weight)
    const wMin       = d3.min(weights) ?? 0.94
    const wMax       = d3.max(weights) ?? 1.0
    const strokeW    = d3.scaleLinear().domain([wMin, wMax]).range([1, 5])

    const maxBC      = d3.max(nodes, n => n.betweenness_centrality ?? 0) || 0.01
    const nodeRadius = d3.scaleSqrt().domain([0, maxBC]).range([14, 26])

    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(n => n.id)
        // higher similarity → shorter rest length
        .distance(d => 200 - (d.weight - 0.94) * 3000)
        .strength(0.7))
      .force('charge', d3.forceManyBody().strength(-280))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide(34))

    const g = svg.append('g')

    const link = g.append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('style', d => `stroke: var(--border-hover); stroke-width: ${strokeW(d.weight)}; stroke-opacity: 0.55; cursor: default`)
      .on('mouseenter', (event, d) => {
        const src = PARTY_NAMES[d.source.id ?? d.source]
        const tgt = PARTY_NAMES[d.target.id ?? d.target]
        setTooltip({ x: event.clientX, y: event.clientY, text: `${src} – ${tgt}\nÄhnlichkeit: ${d.weight.toFixed(4)}` })
      })
      .on('mousemove', event => setTooltip(t => t ? { ...t, x: event.clientX, y: event.clientY } : null))
      .on('mouseleave', () => setTooltip(null))

    const nodeG = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .style('cursor', 'default')
      .call(
        d3.drag()
          .on('start', (ev, d) => { if (!ev.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
          .on('drag',  (ev, d) => { d.fx = ev.x; d.fy = ev.y })
          .on('end',   (ev, d) => { if (!ev.active) sim.alphaTarget(0); d.fx = null; d.fy = null })
      )

    nodeG.append('circle')
      .attr('r', d => nodeRadius(d.betweenness_centrality ?? 0))
      .attr('fill', d => PARTY_HEX[d.id] ?? '#8B9BAF')
      .attr('fill-opacity', 0.9)
      .attr('stroke', '#1E2023')
      .attr('stroke-width', 2)
      .on('mouseenter', (event, d) => {
        const score = data?.bridging_timeseries?.stable_parties?.[d.id]?.[yearKey]
          ?? data?.bridging_timeseries?.afd?.[yearKey]
        setTooltip({
          x: event.clientX, y: event.clientY,
          text: `${PARTY_NAMES[d.id] ?? d.name}\nBridging: ${score != null ? score.toFixed(4) : '—'}`,
        })
      })
      .on('mousemove', event => setTooltip(t => t ? { ...t, x: event.clientX, y: event.clientY } : null))
      .on('mouseleave', () => setTooltip(null))

    nodeG.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', d => nodeRadius(d.betweenness_centrality ?? 0) + 13)
      .attr('style', 'fill: var(--text-secondary); font-family: var(--font-mono); font-size: 11px; pointer-events: none')
      .text(d => PARTY_NAMES[d.id] ?? d.name)

    sim.on('tick', () => {
      link
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
      nodeG.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    return () => sim.stop()
  }, [graphData, activeTopic, year, data])

  if (!graphData) return (
    <div style={{ height: '420px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)' }}>
      Keine Graphdaten für {year}
    </div>
  )

  return (
    <div style={{ position: 'relative' }}>
      <div style={{ display: 'flex', gap: '1px', marginBottom: 'var(--space-3)', background: 'var(--border)' }}>
        {[{ id: null, label: 'Alle Themen' }, ...Object.entries(TOPIC_LABELS).map(([id, label]) => ({ id, label }))].map(({ id, label }) => (
          <button
            key={id ?? 'all'}
            onClick={() => setActiveTopic(id)}
            style={{
              padding: 'var(--space-2) var(--space-3)',
              background: activeTopic === id ? 'var(--bg-elevated)' : 'var(--bg-surface)',
              border: 'none',
              color: activeTopic === id ? 'var(--text-primary)' : 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              fontSize: 'var(--text-xs)',
              cursor: 'pointer',
              transition: 'background 100ms',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <svg
        ref={svgRef}
        style={{ width: '100%', height: '420px', display: 'block', background: 'var(--bg-surface)', border: '1px solid var(--border)' }}
      />

      {tooltip && (
        <div style={{
          ...TOOLTIP_STYLE,
          position: 'fixed',
          left: tooltip.x + 12,
          top: tooltip.y - 8,
          padding: 'var(--space-2) var(--space-3)',
          pointerEvents: 'none',
          zIndex: 200,
          whiteSpace: 'pre-line',
          lineHeight: 1.6,
        }}>
          {tooltip.text}
        </div>
      )}
    </div>
  )
}
