import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';
const api = process.env.SYNCHROFLOW_TEST_API || 'http://127.0.0.1:8017/api/v1';
test.beforeEach(async ({ request }) => { await request.post(`${api}/sumo/stop`); await request.post(`${api}/forecast/enabled?enabled=false`); });
test.afterEach(async ({ request }) => { await request.post(`${api}/sumo/stop`); });

test('all navigation destinations render in live and synthetic modes without script errors', async ({ page }, info) => {
  test.setTimeout(90000);
  const errors: string[] = []; const failures: string[] = []; const inventory: unknown[] = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', e => { if (e.type() === 'error' && !e.text().includes('net::ERR')) errors.push(e.text()); });
  page.on('response', r => { if (r.status() >= 400) failures.push(`${r.status()} ${r.url()}`); });
  await page.goto('/');
  const sidebar = page.locator('aside nav');
  const destinations = await sidebar.locator('button').allTextContents();
  for (const mode of ['live', 'synthetic']) {
    if (mode === 'synthetic') await page.getByRole('button', { name: 'Switch to synthetic demonstration', exact: true }).click();
    for (let index = 0; index < 14; index++) {
      await sidebar.locator('button').nth(index).click();
      if (mode === 'synthetic' && index === 0) await expect(page.locator('canvas')).toBeVisible();
      else await expect(page.locator('main h1').first()).toBeVisible();
      inventory.push({ mode, destination: destinations[index], headings: await page.locator('main h1, main h2').allTextContents(), buttons: await page.locator('main button').allTextContents() });
    }
  }
  await info.attach('navigation-inventory', { body: JSON.stringify(inventory, null, 2), contentType: 'application/json' });
  expect(errors).toEqual([]); expect(failures).toEqual([]);
});

test('synthetic controls change authoritative engine state and preserve scenario overrides', async ({ page }) => {
  test.setTimeout(90000);
  const state = () => page.evaluate(async () => {
    const modulePath = performance.getEntriesByType('resource').map(entry => entry.name).filter(name => new URL(name).pathname === '/src/services/trafficProvider.ts').at(-1) ?? '/src/services/trafficProvider.ts';
    const { trafficProvider } = await import(/* @vite-ignore */ modulePath);
    const s = trafficProvider.getEngine().getState();
    return { time: s.simTime, playing: s.isRunning, speed: s.timeScale, weather: s.weather, camera: s.cameraPreset, scenario: s.scenario, signals: s.signals, vehicles: s.vehicles };
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Switch to synthetic demonstration', exact: true }).click();
  if ((await state()).playing) await page.getByTitle('Pause Simulation', { exact: true }).click();
  for (const [name, preset] of [['STREET','street'], ['TOP DOWN','top_down'], ['AERIAL','aerial']]) {
    await page.getByRole('button', { name, exact: true }).click();
    await expect.poll(async () => (await state()).camera).toBe(preset);
  }
  for (const weather of ['Day','Night','Monsoon','Fog']) {
    await page.getByRole('button', { name: weather, exact: true }).click();
    await expect.poll(async () => (await state()).weather).toBe(weather.toLowerCase());
  }
  await page.getByRole('button', { name: '5x', exact: true }).click();
  await page.getByTitle('Resume Simulation', { exact: true }).click();
  await expect.poll(async () => (await state()).time).toBeGreaterThan(0);
  await page.getByTitle('Pause Simulation', { exact: true }).click();
  const before = (await state()).time;
  await page.getByTitle(/Step Simulation Clock/).click();
  await expect.poll(async () => (await state()).time).toBeGreaterThan(before);
  await page.getByRole('button', { name: 'Inject Ambulance', exact: true }).click();
  expect((await state()).signals.isPreemptActive).toBe(true);
  page.once('dialog', dialog => dialog.accept());
  await page.getByTitle('Reset Simulation', { exact: true }).click();
  await page.locator('aside nav button').filter({ hasText: 'Scenario Laboratory' }).click();
  await page.getByPlaceholder('Search 25 scenarios...').fill('Monsoon');
  await page.getByRole('button').filter({ hasText: '06. Monsoon' }).click();
  await expect(page.getByLabel('north inflow vehicles per hour')).toHaveValue(String((await state()).scenario.arrivalRates.north));
  await page.getByLabel('north inflow vehicles per hour').fill('2350');
  await page.getByRole('button', { name: 'Apply Parameter Overrides' }).click();
  expect((await state()).scenario.arrivalRates.north).toBe(2350);
  await page.locator('aside nav button').filter({ hasText: 'Pedestrian Actuation' }).click();
  const count = (await state()).signals.pedestrianSignals.north.waitingCount;
  await page.getByRole('button', { name: 'Press Pedestrian Pushbutton (NORTH)' }).click();
  expect((await state()).signals.pedestrianSignals.north.waitingCount).toBe(count + 1);
  page.once('dialog', dialog => dialog.accept());
  await page.locator('aside').getByTitle('Reset Synthetic Demonstration Clock', { exact: true }).click();
  await expect(page.getByText('REGISTERED (ACTUATED)', { exact: true })).toHaveCount(0);
});

test('history upload, manual weather, forecast settings and live export use real API state', async ({ page, request }) => {
  await page.goto('/');
  await page.locator('[data-nav=prediction]').click();
  await page.getByText('Historical CSV and weather configuration', { exact: true }).click();
  await page.getByLabel('Historical arrival CSV', { exact: true }).fill(`timestamp,approach,arrivals_pcu,interval_sec\n${new Date(Date.now()-86400000).toISOString()},north,18,60`);
  await page.getByLabel('CSV is demonstration data').check();
  await page.getByRole('button', { name: 'Upload history CSV', exact: true }).click();
  await page.getByRole('button', { name: 'Enable forecasts', exact: true }).click();
  await expect(page.getByText(/north: next arrival rate 0.300 PCU/)).toBeVisible();
  await page.getByLabel('Prediction horizon', { exact: true }).selectOption('120');
  await expect(page.getByText(/horizon 120 s/)).toBeVisible();
  await expect(page.getByRole('img', { name: 'north forecast uncertainty', exact: true })).toBeVisible();
  await page.getByLabel('Weather provider', { exact: true }).selectOption('manual');
  await page.getByRole('button', { name: 'Apply weather configuration', exact: true }).click();
  await page.getByLabel('Manual rainfall mm/h').fill('12');
  await page.getByRole('button', { name: 'Set manual weather', exact: true }).click();
  await expect(page.getByText('Weather: 12 mm/h.', { exact: true })).toBeVisible();
  const config = await (await request.get(`${api}/forecast/config`)).json();
  expect(config.enabled).toBe(true); expect(config.weather_provider).toBe('manual');
  await page.locator('aside button').filter({ hasText: 'Scientific Data Export' }).click();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download live snapshot JSON' }).click();
  const download = await downloadPromise; const path = await download.path();
  const data = JSON.parse(await readFile(path!, 'utf8'));
  expect(data.source).toBe('sumo_traci'); expect(data.snapshot.connected).toBe(false);
});

test('browser benchmark, exports, educational selectors and legacy acknowledgement are functional', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Switch to synthetic demonstration', exact: true }).click();
  const navigate = (name: string) => page.locator('aside nav button').filter({ hasText: name }).click();
  await navigate('Controller Benchmark Lab');
  await page.getByLabel('Benchmark seed').fill('0');
  await expect(page.getByLabel('Benchmark seed')).toHaveValue('0');
  await page.getByRole('button', { name: 'Run Comparative Benchmark', exact: true }).click();
  await expect(page.locator('tbody tr')).toHaveCount(7);
  const csvPending = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export CSV', exact: true }).click();
  const csvDownload = await csvPending;
  const csv = await readFile((await csvDownload.path())!, 'utf8');
  expect(csv).toContain(',0,60,');
  await navigate('Traffic Prediction Center');
  await page.locator('main select').selectOption('30');
  await expect(page.locator('main select')).toHaveValue('30');
  await navigate('Network Coordination');
  await page.locator('main select').selectOption('18');
  await expect(page.locator('main select')).toHaveValue('18');
  await navigate('V2I');
  for (const name of ['map','bsm','spat']) await page.getByRole('button', { name, exact: true }).click();
  await navigate('Safety Supervisor');
  await page.getByRole('button').filter({ hasText: 'Emergency & Police Dispatcher' }).click();
  await navigate('Provider & Remote API Config');
  await page.getByRole('button').filter({ hasText: 'Stage 2: Remote Python FastAPI Backend' }).click();
  await page.getByRole('button', { name: 'Test Command Dispatch & Ack', exact: true }).click();
  await expect(page.getByText(/Confirmed acknowledgement:/)).toBeVisible();
  await page.getByRole('button').filter({ hasText: 'Local Deterministic Engine' }).click();
  await navigate('Scientific Data Export');
  const jsonPending = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download Benchmark JSON', exact: true }).click();
  const jsonDownload = await jsonPending;
  const data = JSON.parse(await readFile((await jsonDownload.path())!, 'utf8'));
  expect(data.metadata.source).toBe('synthetic_browser_engine');
});

test('command errors are shown and disconnected websocket disables live controls', async ({ page, request }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'start', exact: true })).toBeEnabled();
  await page.route('**/api/v1/sumo/start?**', r => r.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({ detail: 'Audit rejection' }) }));
  await page.getByRole('button', { name: 'start', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Audit rejection');
  expect((await (await request.get(`${api}/sumo/status`)).json()).connected).toBe(false);
  await page.unroute('**/api/v1/sumo/start?**');
  await page.getByRole('button', { name: 'start', exact: true }).click();
  await expect(page.getByTestId('simulation-state')).toHaveAttribute('data-status', 'running');
  await page.getByRole('button', { name: 'stop', exact: true }).click();
  await expect(page.getByTestId('simulation-state')).toHaveAttribute('data-status', 'stopped');
  await page.getByRole('button', { name: 'start', exact: true }).click();
  await expect.poll(async () => (await (await request.get(`${api}/sumo/status`)).json()).running).toBe(true);
  await page.getByRole('button', { name: 'stop', exact: true }).click();
  await page.routeWebSocket('**/sumo/ws', socket => socket.close());
  await page.reload();
  await expect(page.getByRole('button', { name: 'start', exact: true })).toBeDisabled();
  await expect(page.getByLabel('Header telemetry')).toContainText('disconnected');
});
