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
    degree_centrality 0.8
    betweenness_centrality 0.0
    community 0
  ]
  node [
    id 4
    label "afd"
    name "AfD"
    bias "far-right"
    color "#009EE0"
    degree_centrality 0.0
    betweenness_centrality 0.0
    community 1
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
    weight 0.9731
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 0
    target 2
    weight 0.9684
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 0
    target 3
    weight 0.9716
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 0
    target 5
    weight 0.9687
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 1
    target 2
    weight 0.975
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 1
    target 3
    weight 0.9658
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 1
    target 5
    weight 0.9722
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 2
    target 3
    weight 0.9666
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 2
    target 5
    weight 0.9733
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
  edge [
    source 3
    target 5
    weight 0.9682
    topics "migration"
    topics "energy_transition"
    topics "retirement"
    topics "wealth_tax"
    topics "digitalization"
  ]
]
