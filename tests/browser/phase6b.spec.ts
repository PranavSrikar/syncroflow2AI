import {test,expect} from '@playwright/test';
import fs from 'node:fs/promises';
const api=process.env.SYNCHROFLOW_TEST_API || 'http://127.0.0.1:8017/api/v1';
test.afterEach(async({request})=>{await request.post(`${api}/sumo/stop`)});
test('dashboard fits target screens with four KPIs, visible safety and non-overlapping controls',async({page,request})=>{
  await request.post(`${api}/sumo/stop`);
  await page.goto('/');
  expect((await request.post(`${api}/sumo/start?scenario=pedestrian&controller=hybrid&paused=true&seed=95`)).ok()).toBeTruthy();
  for(let i=0;i<30;i++)expect((await request.post(`${api}/sumo/step`)).ok()).toBeTruthy();
  await expect(page.getByRole('img',{name:'Live SUMO digital twin',exact:true})).toHaveAttribute('data-sim-time','30');
  await fs.mkdir('.checkpoints/phase6b',{recursive:true});const results=[];
  for(const [width,height] of [[1366,768],[1920,1080]]){
    await page.setViewportSize({width,height});
    await expect(page.locator('.sf-metric')).toHaveCount(4);
    await expect.poll(()=>page.locator('[data-scope=dashboard]').evaluate(el=>el.scrollHeight<=el.clientHeight+1)).toBe(true);
    const map=await page.locator('.sf-network-map').boundingBox();const dock=await page.getByLabel('Simulation operations').boundingBox();const safety=await page.locator('.sf-events-card').boundingBox();
    expect(map!.height).toBeGreaterThan(280);expect(map!.y+map!.height).toBeLessThanOrEqual(dock!.y);
    expect(dock!.y+dock!.height).toBeLessThan(height);expect(safety!.y+safety!.height).toBeLessThanOrEqual(dock!.y);
    await expect(page.getByRole('heading',{name:'Why this signal?',exact:true})).toBeVisible();
    results.push({width,height,map,dock,safety});
    await page.screenshot({path:`.checkpoints/phase6b/after-${width}.png`});
  }
  const map=page.getByRole('img',{name:'Live SUMO digital twin',exact:true});const before=await map.getAttribute('viewBox');
  await page.getByLabel('Zoom in digital twin',{exact:true}).click();await expect(map).not.toHaveAttribute('viewBox',before!);
  await page.getByRole('button',{name:'Road IDs',exact:true}).click();await expect(page.getByRole('button',{name:'Road IDs',exact:true})).toHaveAttribute('aria-pressed','true');
  await fs.writeFile('.checkpoints/phase6b/responsive-layout.json',JSON.stringify(results,null,2));
});

test('controller tabs expose actual traces and implemented model boundaries',async({page,request})=>{
  await request.post(`${api}/sumo/stop`);
  expect((await request.post(`${api}/sumo/start?scenario=vehicle&controller=hybrid&paused=true&mpc_budget_ms=1000`)).ok()).toBeTruthy();
  for(let i=0;i<12;i++)await request.post(`${api}/sumo/step`);
  const state=await(await request.get(`${api}/sumo/status`)).json();
  await page.goto('/');await page.locator('[data-nav=math_models]').click();
  await expect(page.getByText(`Exact policy: ${state.controllerDiagnostics.policy}`,{exact:true})).toBeVisible();
  await page.getByRole('tab',{name:'Architecture',exact:true}).click();
  await expect(page.getByText('Independent safety supervisor',{exact:true})).toBeVisible();
  await page.getByRole('tab',{name:'Models & assumptions',exact:true}).click();
  await page.getByText('Finite-candidate constrained MPC',{exact:true}).click();
  await expect(page.getByText(/It does not solve a continuous quadratic programme/)).toBeVisible();
});

test('synthetic reset asks for confirmation and cancel preserves the paused run',async({page})=>{
  await page.goto('/');await page.getByRole('button',{name:'Switch to synthetic demonstration',exact:true}).click();
  const pause=page.getByTitle('Pause Simulation',{exact:true});if(await pause.count())await pause.click();
  await page.getByTitle(/Step Simulation Clock/).click();
  const readTime=()=>page.evaluate(async()=>{const path=performance.getEntriesByType('resource').map(e=>e.name).filter(n=>new URL(n).pathname==='/src/services/trafficProvider.ts').at(-1)!;return (await import(/* @vite-ignore */ path)).trafficProvider.getEngine().getState().simTime});
  const before=await readTime();expect(before).toBeGreaterThan(0);
  page.once('dialog',async dialog=>{expect(dialog.message()).toContain('Reset synthetic demonstration');await dialog.dismiss()});
  await page.getByTitle('Reset Simulation',{exact:true}).click();expect(await readTime()).toBe(before);
});
