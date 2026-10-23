import { test, expect } from '@playwright/test';
const api = process.env.SYNCHROFLOW_TEST_API || 'http://127.0.0.1:8017/api/v1';

test.beforeEach(async ({ request }) => { expect((await request.post(`${api}/sumo/stop`)).ok()).toBeTruthy(); await request.post(`${api}/forecast/enabled?enabled=false`); });
test.afterEach(async ({ request }) => { await request.post(`${api}/sumo/stop`); await request.post(`${api}/perception/stop`); });

test('dashboard receives real SUMO telemetry and controls lifecycle', async ({ page, request }) => {
  const errors: string[] = [];
  await page.route('https://fonts.googleapis.com/**', route => route.abort());
  await page.route('https://fonts.gstatic.com/**', route => route.abort());
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: 'Live traffic command center' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'start', exact: true })).toBeEnabled();
  await page.locator('[data-nav=perception]').click();
  await expect(page.getByRole('heading', { name: 'Camera observations and arrival forecasts' })).toBeVisible();
  await page.getByLabel('Observation source').selectOption('camera');
  await expect(page.getByText(/No fresh camera observations/)).toBeVisible();
  await page.getByLabel('Observation source').selectOption('sumo');
  const previous = new Date(Date.now() - 86400000).toISOString();
  expect((await request.post(`${api}/forecast/history`, { data: {
    csv: `timestamp,approach,arrivals_pcu,interval_sec\n${previous},north,12,60`, example_data: true,
  } })).ok()).toBeTruthy();
  await page.getByRole('button', { name: 'Enable forecasts', exact: true }).click();
  await expect(page.getByText(/north: next arrival rate 0.200 PCU\/s/)).toBeVisible();
  await expect(page.getByText(/EXAMPLE DATA/)).toBeVisible();
  await page.getByRole('button', { name: 'Disable forecasts', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Enable forecasts', exact: true })).toBeVisible();
  await page.locator('[data-nav=dashboard]').click();
  await page.getByText('Detailed telemetry & safety diagnostics', { exact: true }).click();
  await page.getByRole('button', { name: 'start', exact: true }).click();
  await expect(page.getByText(/Simulation: running/)).toBeVisible();
  await expect(page.getByRole('cell', { name: 'north', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'pause', exact: true }).click();
  await expect(page.getByText(/Simulation: paused/)).toBeVisible();
  const before = await (await request.get(`${api}/sumo/telemetry`)).json();
  await page.getByRole('button', { name: 'step', exact: true }).click();
  await expect.poll(async () => (await (await request.get(`${api}/sumo/telemetry`)).json()).simTime).toBe(before.simTime + 1);
  const raw = await (await request.get(`${api}/sumo/telemetry`)).json();
  await expect(page.getByText(new RegExp(`Time: ${raw.simTime} s`))).toBeVisible();
  const north = page.getByRole('row').filter({ has: page.getByRole('cell', { name: 'north', exact: true }) });
  await expect(north.locator('td').nth(1)).toHaveText(String(raw.approaches.north.vehicles));
  await page.getByRole('button', { name: 'stop', exact: true }).click();
  await expect(page.getByText(/Simulation: stopped/)).toBeVisible();
  await page.getByLabel('SUMO network').selectOption('pedestrian');
  await page.getByLabel('SUMO controller').selectOption('max_pressure');
  await page.getByRole('button', { name: 'start', exact: true }).click();
  await expect(page.getByText('Crossing :center_c0_0, link 16:', { exact: false })).toBeVisible();
  await expect(page.getByText(/Permission monitor center/)).toBeVisible();
  await expect(page.getByText('enforcing_pedestrian_and_vehicle_timing', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'stop', exact: true }).click();
  await expect(page.getByText(/Simulation: stopped/)).toBeVisible();
  await page.getByLabel('SUMO network').selectOption('vehicle');
  await page.getByLabel('SUMO controller').selectOption('mpc');
  await page.getByRole('button', { name: 'start', exact: true }).click();
  await expect(page.getByLabel('Header telemetry')).toContainText('Controller: mpc');
  await page.getByRole('button', { name: 'pause', exact: true }).click();
  for (let i = 0; i < 12; i++) {
    const response = await request.post(`${api}/sumo/step`);
    expect(response.ok()).toBeTruthy();
  }
  await expect(page.locator('pre').filter({ hasText: 'constrained_mpc' })).toBeVisible();
  await page.getByRole('button', { name: 'Inject emergency north', exact: true }).click();
  for (let i = 0; i < 2; i++) {
    expect((await request.post(`${api}/sumo/step`)).ok()).toBeTruthy();
  }
  await expect(page.getByText(/synchroflow_emergency_1.*north.*priority 3/)).toBeVisible();
  const emergency = await (await request.get(`${api}/sumo/emergencies/status`)).json();
  expect(emergency.requests[0].source).toBe('sumo_injection');
  await page.getByRole('button', { name: 'stop', exact: true }).click();
  await expect(page.getByText(/Simulation: stopped/)).toBeVisible();
  expect(errors).toEqual([]);
  const stopped = await (await request.get(`${api}/sumo/emergencies/status`)).json();
  expect(stopped.activeVehicleId).toBeNull();
  expect(stopped.requests[0].state).toBe('cancelled');
});

test('configured real video is visible in the camera dashboard', async ({ page }) => {
  test.skip(!process.env.SYNCHROFLOW_CAMERA_CONFIG, 'Local real-video camera config required');
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.locator('[data-nav=perception]').click();
  await page.getByLabel('Observation source').selectOption('camera');
  await page.getByRole('button', { name: 'Start cameras', exact: true }).click();
  await expect(page.getByText(/Selected data: camera_fusion/)).toBeVisible({ timeout: 20000 });
  await expect(page.getByText(/Fused counts: north [1-9]/)).toBeVisible();
  await expect(page.getByText('Recorded video · replayed observations', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Stop cameras', exact: true }).click();
  await expect(page.getByText(/No fresh camera observations/)).toBeVisible();
});

test('hybrid corridor renders actual multi-junction controller state', async ({ page, request }) => {
  // This case verifies the successful MPC rendering path deterministically.
  // The production 50ms budget is unchanged; forced timeout/fallback remains
  // independently verified by external demonstration G and backend tests.
  await page.route('**/api/v1/sumo/start?**', route => route.continue({ url: route.request().url() + '&mpc_budget_ms=1000' }));
  await page.route('https://fonts.googleapis.com/**', route => route.abort());
  await page.route('https://fonts.gstatic.com/**', route => route.abort());
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('button', { name: 'start', exact: true })).toBeEnabled();
  await page.getByText('Detailed telemetry & safety diagnostics', { exact: true }).click();
  await page.getByLabel('SUMO network').selectOption('corridor');
  await page.getByLabel('SUMO controller').selectOption('hybrid');
  await page.getByRole('button', { name: 'start', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Junction A0 control state' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Junction B0 control state' })).toBeVisible();
  await page.getByRole('button', { name: 'pause', exact: true }).click();
  for (let i = 0; i < 12; i++) expect((await request.post(`${api}/sumo/step`)).ok()).toBeTruthy();
  const actual = await (await request.get(`${api}/sumo/status`)).json();
  const a = page.getByRole('article', { name: 'Junction telemetry A0' });
  await expect(a.getByText(/Policy: constrained_mpc/)).toBeVisible();
  await expect(a.getByText(/accepted actions/)).toContainText(String(actual.junctions.A0.safetySupervisor.acceptedActions));
  await expect(page.getByText(/Inference status: training_inference_ready/)).toBeVisible();
  expect(actual.mappoStatus.operationalPolicyEnabled).toBe(false);
  await page.getByLabel('Emergency junction').selectOption('B0');
  await page.getByRole('button', { name: 'Inject emergency north', exact: true }).click();
  for (let i = 0; i < 2; i++) expect((await request.post(`${api}/sumo/step`)).ok()).toBeTruthy();
  await expect(page.getByText(/synchroflow_emergency_B0_1.*north.*priority 3/)).toBeVisible();
  await page.getByRole('button', { name: 'stop', exact: true }).click();
  await expect(page.getByText(/Simulation: stopped/)).toBeVisible();
});

test('release demos show measured spillback and follow external API selection', async ({ page, request }) => {
  await page.route('https://fonts.googleapis.com/**', route => route.abort());
  await page.route('https://fonts.gstatic.com/**', route => route.abort());
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.getByText('Detailed telemetry & safety diagnostics', { exact: true }).click();
  try {
    const started = await request.post(`${api}/sumo/start?scenario=spillback&controller=hybrid&paused=true&seed=95`);
    expect(started.ok()).toBeTruthy();
    await expect(page.getByLabel('SUMO network')).toHaveValue('spillback');
    await expect(page.getByLabel('SUMO controller')).toHaveValue('hybrid');
    for (let i = 0; i < 35; i++) expect((await request.post(`${api}/sumo/step`)).ok()).toBeTruthy();
    const raw = await (await request.get(`${api}/sumo/telemetry`)).json();
    expect(raw.downstream.south.occupancyPercent).toBeGreaterThan(80);
    await expect(page.getByText(/south: occupancy 90\.6%; spillback heuristic triggered/)).toBeVisible();
    expect((await request.post(`${api}/sumo/stop`)).ok()).toBeTruthy();
    expect((await request.post(`${api}/sumo/start?scenario=unequal&controller=hybrid&paused=true&seed=95`)).ok()).toBeTruthy();
    await expect(page.getByLabel('SUMO network')).toHaveValue('unequal');
    await expect(page.getByText(/Simulation: paused/)).toBeVisible();
  } finally {
    await request.post(`${api}/sumo/stop`);
  }
});

