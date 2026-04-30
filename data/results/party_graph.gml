graph [
  node [
    id 0
    label "cdu_csu"
    name "CDU/CSU"
    bias "conservative-liberal"
    color "#000000"
    degree_centrality 0.8
    betweenness_centrality 0.0
    community 0
  ]
  node [
    id 1
    label "spd"
    name "SPD"
    bias "left-liberal"
    color "#E3000F"
    degree_centrality 0.8
    betweenness_centrality 0.0
    community 0
  ]
  node [
    id 2
    label "gruene"
    name "B&#252;ndnis 90/Die Gr&#252;nen"
    bias "left-liberal"
    color "#1AA037"
    degree_centrality 0.8
    betweenness_centrality 0.0
    community 0
  ]
  node [
    id 3
    label "fdp"
    name "FDP"
    bias "economic-liberal"
    color "#FFED00"
    degree_centrality 0.0
    betweenness_centrality 0.0
    community 1
  ]
  node [
    id 4
    label "afd"
    name "AfD"
    bias "far-right"
    color "#009EE0"
    degree_centrality 0.8
    betweenness_centrality 0.0
    community 0
  ]
  node [
    id 5
    label "linke"
    name "Die Linke"
    bias "left"
    color "#BE3075"
    degree_centrality 0.8
    betweenness_centrality 0.0
    community 0
  ]
  edge [
    source 0
    target 1
    weight 0.976
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 0
    target 2
    weight 0.9764
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 0
    target 4
    weight 0.9513
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 0
    target 5
    weight 0.9527
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 1
    target 2
    weight 0.9809
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 1
    target 4
    weight 0.9571
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 1
    target 5
    weight 0.9527
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 2
    target 4
    weight 0.9539
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 2
    target 5
    weight 0.9599
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 4
    target 5
    weight 0.9353
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
]
