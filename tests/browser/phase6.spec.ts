import { test, expect } from '@playwright/test';
import fs from 'node:fs/promises';
const api=process.env.SYNCHROFLOW_TEST_API || 'http://127.0.0.1:8017/api/v1';
test.beforeEach(async({request})=>{await request.post(`${api}/sumo/stop`)});
test.afterEach(async({request})=>{await request.post(`${api}/sumo/stop`)});

test('digital twin positions, lane signals and queue cards match paused SUMO; analytics is observed',async({page,request},info)=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.setViewportSize({width:1440,height:1000});
  await page.goto('/');
  await expect(page.getByText('Your network, ready to observe',{exact:true})).toBeVisible();
  expect((await request.post(`${api}/sumo/start?scenario=pedestrian&controller=hybrid&paused=true&seed=95`)).ok()).toBeTruthy();
  for(let i=0;i<30;i++)expect((await request.post(`${api}/sumo/step`)).ok()).toBeTruthy();
  const state=await(await request.get(`${api}/sumo/status`)).json();const raw=state.telemetry;
  const map=page.getByRole('img',{name:'Live SUMO digital twin',exact:true});
  await expect(map).toHaveAttribute('data-sim-time',String(raw.simTime));
  const [x,y,w,h]=(await map.getAttribute('viewBox'))!.split(' ').map(Number);
  const inView=Object.entries(raw.vehicleDetails).filter(([,v]:[string,any])=>v.position[0]>=x && v.position[0]<=x+w && -v.position[1]>=y && -v.position[1]<=y+h);
  expect(inView.length).toBeGreaterThan(0);
  await expect(map.locator('[data-vehicle-id]')).toHaveCount(inView.length);
  for(const [id,v] of inView as [string,any][]){
    // IDs are compared through DOM attributes, avoiding selector escaping.
    const coordinates=await map.locator('[data-vehicle-id]').evaluateAll((nodes,id)=>nodes.filter(n=>n.getAttribute('data-vehicle-id')===id).map(n=>[n.getAttribute('data-world-x'),n.getAttribute('data-world-y')]),id);
    expect(coordinates).toEqual([[String(v.position[0]),String(v.position[1])]]);
  }
  for(const [id,light] of Object.entries(raw.trafficLights) as [string,any][]){
    for(let i=0;i<light.signalState.length;i++){
      const links=map.locator(`[data-signal-id="${id}-${i}"]`);
      if(await links.count())await expect(links.first()).toHaveAttribute('data-state',light.signalState[i]);
    }
  }
  await expect(page.getByTestId('queue-north')).toContainText(String(raw.approaches.north.queued));
  const rows=Object.values(raw.approaches) as any[];
  const count=rows.reduce((n,r)=>n+r.vehicles,0);
  const wait=rows.reduce((n,r)=>n+r.avgWaitTimeSec*r.vehicles,0)/count;
  await expect(page.locator('[data-metric="Approach vehicles"] strong')).toHaveText(`${count}veh`);
  await expect(page.locator('[data-metric="Vehicles in queue"] strong')).toHaveText(`${rows.reduce((n,r)=>n+r.queued,0)}veh`);
  await expect(page.locator('[data-metric="Current mean wait"] strong')).toHaveText(`${wait.toFixed(1)}s`);
  await expect(page.locator('[data-metric="Run throughput"] strong')).toHaveText(`${state.metrics.throughputVehiclesPerHour.toFixed(0)}veh/h`);
  await expect(page.getByText('MAPPO: Experimental — Not Qualified',{exact:true})).toBeVisible();
  await fs.mkdir('.checkpoints/phase6',{recursive:true});
  await page.screenshot({path:'.checkpoints/phase6/after-desktop.png',fullPage:false});
  await page.locator('[data-nav=analytics]').click();
  await expect(page.getByRole('img',{name:'Network queue',exact:true})).toBeVisible();
  await page.getByLabel('Analytics time window').selectOption('30');
  await expect(page.getByLabel('Analytics time window')).toHaveValue('30');
  await page.locator('[data-nav=pedestrian]').click();
  await expect(page.getByRole('heading',{name:'Protected crossing status',exact:true})).toBeVisible();
  await expect(page.getByText(/Required clearance:/).first()).toBeVisible();
  expect(errors).toEqual([]);
  const timings={...await page.evaluate(()=>({navigation:(performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming).toJSON(),domNodes:document.getElementsByTagName('*').length})),snapshotBytes:Buffer.byteLength(JSON.stringify(state)),observedVehicles:Object.keys(raw.vehicleDetails).length,renderedVehicles:inView.length};
  await info.attach('measured-browser-timing',{body:JSON.stringify(timings,null,2),contentType:'application/json'});
  await fs.writeFile('.checkpoints/phase6/browser-performance.json',JSON.stringify(timings,null,2));
});

test('network focus, responsive layouts, disconnected state and keyboard controls',async({page,request})=>{
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.goto('/');
  expect((await request.post(`${api}/sumo/start?scenario=corridor&controller=hybrid&paused=true`)).ok()).toBeTruthy();
  for(let i=0;i<12;i++)await request.post(`${api}/sumo/step`);
  await page.getByLabel('Digital twin junction').selectOption('B0');
  await expect(page.getByLabel('Digital twin junction')).toHaveValue('B0');
  await expect(page.getByText('Selected junction B0',{exact:true})).toBeVisible();
  const before=await page.getByRole('img',{name:'Live SUMO digital twin'}).getAttribute('viewBox');
  await page.getByLabel('Digital twin junction').selectOption('network');
  await expect(page.getByRole('img',{name:'Live SUMO digital twin'})).not.toHaveAttribute('viewBox',before!);
  for(const width of [1366,1024,768,390]){
    await page.setViewportSize({width,height:900});
    await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
    await expect.poll(()=>page.locator('main').evaluate(el=>el.scrollWidth<=el.clientWidth)).toBe(true);
    await expect(page.getByRole('img',{name:'Live SUMO digital twin'})).toBeVisible();
    await page.screenshot({path:`.checkpoints/phase6/after-${width}.png`});
  }
  await page.setViewportSize({width:1024,height:900});
  await page.getByRole('button',{name:'stop',exact:true}).focus();
  await page.keyboard.press('Enter');
  await expect.poll(async()=>(await(await request.get(`${api}/sumo/status`)).json()).connected).toBe(false);
  await page.routeWebSocket('**/sumo/ws',socket=>socket.close());
  await page.reload();
  await expect(page.getByRole('button',{name:'start',exact:true})).toBeDisabled();
  await expect(page.getByLabel('Header telemetry')).toContainText('disconnected');
});
