# Two-junction coordination scenario

SUMO 1.28 network generation command:

```
netgenerate --grid --grid.x-number 2 --grid.y-number 1 --grid.length 250 --grid.attach-length 150 --tls.set A0,B0 --default.lanenumber 1 --output-file corridor.net.xml
```

Two four-arm intersections share a 250 m bidirectional corridor. Six external Poisson flows use an explicit SUMO seed. Route demand is simulated, not recorded traffic. Each agent recommends hold/release preferences to the existing constrained MPC. Actual timing writes go through its independent signal supervisor. The scenario is for research training/evaluation; no trained coordination policy is enabled in the operational dashboard.
