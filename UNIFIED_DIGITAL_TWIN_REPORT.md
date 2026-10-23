# Live digital twin implementation

The new live digital twin uses actual SUMO/TraCI observations in the main command center. The existing Three.js synthetic demonstration is retained as its own labelled mode. Shared visual conventions (dark roads, vehicle categories, signals and state colors) carry over, while a separate SVG renderer respects real SUMO network geometry rather than forcing vehicles into the browser model's idealized junction.

## Spatial contract and rendering

The existing adapter already supplied exact `vehicleDetails.position`, front-bumper heading, length/width, class/type, speed, lane ID and pedestrians. Added `networkGeometry` supplies lane centerline shapes/width and signalized-junction polygons/centers. Lane geometry is cached per adapter session. Network readers use the same coordinate frame, so A0/B0 and connecting corridor remain spatially aligned.

SVG maps `(x,y)` to `(x,-y)` with north up. SUMO angle is clockwise from north; vehicles are drawn rearward from their reported front bumper using true dimensions and heading. Signal circles are placed at actual incoming-lane endpoints, with one circle per controlled link; G/g/y/r retain distinct states. Multiple movements on the same endpoint may overlap; the phase strip and technical link-state string preserve every permission. Pedestrians use exact observed position. Emergency color uses SUMO `vehicleClass=emergency`, not an inferred type name.

The default single-junction view focuses within 135 metres of its actual center; Entire network shows all available lanes. Corridor selection can focus A0/B0 independently and changes the corresponding queue/diagnostic panel without changing simulation state. No invented vehicles, queue stacks or interpolated motion are drawn. The map marks observed simulation time and stale states. Missing geometry displays an explicit empty/aggregate fallback.

At most 1,500 vehicles in the current viewport are rendered; a disclosure states if more are omitted. Aggregate KPIs include all observed approach vehicles. Geometry is session-static; SVG updates on the 500ms stream rather than an unbounded animation loop. Histories are bounded to 120 distinct received simulation times.

## Decision and safety visibility

Why this signal? shows backend policy, selected controller, arrival-source influence, fallback reason, phase pressure and route-weighted receiving-supply heuristic. Fairness bars derive from existing phase service-age telemetry and report their precise meaning. Emergency/pedestrian panels show request states and crossing permissions/occupancy. Adaptive countdowns show `nextSwitch - simTime` from the last received snapshot, labelled as the current schedule that may be revised by the controller; no wall-clock countdown is fabricated.

MAPPO remains **Experimental — Not Qualified**. Hybrid retains supervised constrained MPC and Max-Pressure fallback. No safety supervision or algorithm logic changed.

## Evidence and limitations

Before: `.checkpoints/phase6/before-desktop.png`. After: `after-desktop.png`, `after-1366.png`, `after-1024.png`, `after-768.png`, `after-390.png`. Screenshots correspond to actual paused SUMO runs and are not design mockups. Test results and measured browser timings are in `UI_UX_TEST_RESULTS.md`.

Backend integration tests compare geometry against TraCI lane shapes/widths and every vehicle position/class across vehicle, pedestrian and corridor scenarios. Browser tests compare rendered data attributes with actual paused API values, signal-link states and north queue. These establish telemetry fidelity for tested fixtures, not a general real-road digital twin validation. Physical cameras, geographic maps, annotated video streaming, calibrated detector geometry and smooth sub-step interpolation are not claimed.
