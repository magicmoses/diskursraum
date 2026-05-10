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
  digitalization:   'Digitalisierung',
  work_transition:  'Arbeit',
  defense:          'Verteidigung',
  family_children:  'Familie',
  education:        'Bildung',
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

    // Guided initial X positions by political orientation
    const INIT_X = {
      linke: 0.08, gruene: 0.22, spd: 0.38,
      cdu_csu: 0.62, fdp: 0.78, afd: 0.92,
    }

    const bs = data?.bridging_timeseries
    const getBridging = id => id === 'afd'
      ? (bs?.afd?.[yearKey] ?? 0)
      : (bs?.stable_parties?.[id]?.[yearKey] ?? 0)

    const nodes = rawNodes.map(n => ({
      ...n,
      x: (INIT_X[n.id] ?? 0.5) * width,
      y: height / 2 + (Math.random() - 0.5) * 40,
    }))
    const edges = rawEdges.map(e => ({ ...e }))

    const weights  = edges.map(e => e.weight)
    const wMin     = d3.min(weights) ?? 0.12
    const wMax     = d3.max(weights) ?? 0.74
    const strokeW  = d3.scaleLinear().domain([wMin, wMax]).range([1, 5])

    const allBS    = nodes.map(n => getBridging(n.id))
    const maxBS    = Math.max(...allBS, 0.001)
    const nodeRadius = id => 14 + (getBridging(id) / maxBS) * 12

    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(n => n.id)
        .distance(d => 60 + (1 - d.weight) * 360)
        .strength(d => 0.4 + d.weight * 0.5))
      .force('charge', d3.forceManyBody().strength(-320))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide(38))

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
      .attr('r', d => nodeRadius(d.id))
      .attr('fill', d => PARTY_HEX[d.id] ?? '#8B9BAF')
      .attr('fill-opacity', 0.9)
      .attr('stroke', '#1E2023')
      .attr('stroke-width', 2)
      .on('mouseenter', (event, d) => {
        const score = getBridging(d.id)
        setTooltip({
          x: event.clientX, y: event.clientY,
          text: `${PARTY_NAMES[d.id] ?? d.name}\nBridging: ${score != null ? score.toFixed(4) : '—'}`,
        })
      })
      .on('mousemove', event => setTooltip(t => t ? { ...t, x: event.clientX, y: event.clientY } : null))
      .on('mouseleave', () => setTooltip(null))

    nodeG.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', d => nodeRadius(d.id) + 13)
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
