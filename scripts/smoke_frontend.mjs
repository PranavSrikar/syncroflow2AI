// Browser smoke against built assets. Requires a stopped disposable backend.
import { chromium, expect } from '@playwright/test';
import fs from 'node:fs/promises';
const url=process.env.SYNCHROFLOW_PRODUCTION_URL || 'http://127.0.0.1:3037';
const api=process.env.SYNCHROFLOW_TEST_API || 'http://127.0.0.1:8001/api/v1';
const json=async(path,method='GET')=>{const r=await fetch(api+path,{method});if(!r.ok)throw new Error(await r.text());return r.json()};
if((await json('/sumo/status')).connected)throw new Error('Preserving active simulation: use a stopped backend');
const browser=await chromium.launch({channel:process.env.SYNCHROFLOW_BROWSER_CHANNEL || 'msedge'});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[],failures=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('response',r=>{if(r.status()>=400)failures.push(`${r.status()} ${r.url()}`)});
let owned=false;
try{
  await page.goto(url);
  await expect(page.getByRole('button',{name:'start',exact:true})).toBeEnabled();
  await page.getByLabel('SUMO network').selectOption('vehicle');
  await page.getByLabel('SUMO controller').selectOption('hybrid');
  owned=true;
  await page.getByRole('button',{name:'start',exact:true}).click();
  await expect(page.getByTestId('simulation-state')).toHaveAttribute('data-status', 'running');
  await page.getByRole('button',{name:'pause',exact:true}).click();
  await expect(page.getByTestId('simulation-state')).toHaveAttribute('data-status', 'paused');
  for(let i=0;i<30;i++)await json('/sumo/step','POST');
  const state=await json('/sumo/status');
  await expect(page.getByRole('img',{name:'Live SUMO digital twin',exact:true})).toHaveAttribute('data-sim-time',String(state.telemetry.simTime));
  await expect(page.getByTestId('queue-north')).toContainText(String(state.telemetry.approaches.north.queued));
  await fs.mkdir('.checkpoints/phase6',{recursive:true});
  await page.screenshot({path:'.checkpoints/phase6/production-desktop.png'});
  await page.getByRole('button',{name:'stop',exact:true}).click();
  await expect(page.getByTestId('simulation-state')).toHaveAttribute('data-status', 'stopped');
  await page.getByRole('button',{name:'start',exact:true}).click();
  await expect(page.getByTestId('simulation-state')).toHaveAttribute('data-status', 'running');
  await page.getByRole('button',{name:'stop',exact:true}).click();
  await expect(page.getByTestId('simulation-state')).toHaveAttribute('data-status', 'stopped');
  expect(errors).toEqual([]);expect(failures).toEqual([]);
  const result={url,passed:true,errors,failures,navigation:await page.evaluate(()=>(performance.getEntriesByType('navigation')[0]).toJSON()),observedSimTime:state.telemetry.simTime,snapshotBytes:Buffer.byteLength(JSON.stringify(state)),qualifiedMAPPO:state.mappoStatus.operationalPolicyEnabled};
  await fs.writeFile('.checkpoints/phase6/production-smoke.json',JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
}finally{
  if(owned)await json('/sumo/stop','POST');
  await browser.close();
}
