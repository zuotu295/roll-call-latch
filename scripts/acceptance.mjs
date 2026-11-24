import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { deploy } from './deploy.mjs';
import { read, signer, submit } from './studionet.mjs';

const sponsor = await signer(process.env.STUDIONET_PRIVATE_KEY);
const observer = await signer();
const {address,evidence} = await deploy(sponsor);
const transactions = {deploy:evidence};
const send = async (label,client,method,args,error) =>
  transactions[label] = await submit(client,address,method,args,label,error);
const rule = (key) => read(address,'get_rule',[key]);

await send('bindPassing',sponsor,'bind',['publish-summary',2024,2,210]);
await send('bindFailed',sponsor,'bind',['enable-followup',2024,100,200]);
assert.equal((await rule('publish-summary')).state,'PENDING');
assert.equal((await rule('enable-followup')).state,'PENDING');
await Promise.all([
  send('activate',observer,'settle',['publish-summary']),
  send('close',sponsor,'settle',['enable-followup']),
]);
const activated = await rule('publish-summary');
const closed = await rule('enable-followup');
assert.deepEqual(activated,{year:2024,roll:2,min_yea:210,state:'ACTIVATED',evidence:{yea:213,nay:200,result:'Passed'}});
assert.equal(closed.state,'CLOSED');
assert.equal(closed.evidence.result,'Failed');
assert.ok(closed.evidence.yea>=closed.min_yea,'This vote should demonstrate the independent official outcome guard');
await send('rejectResettle',observer,'settle',['publish-summary'],/No pending rule/);
assert.deepEqual(await rule('publish-summary'),activated);
assert.deepEqual(await rule('enable-followup'),closed);
const equivalence = {activate:JSON.stringify(activated.evidence),close:JSON.stringify(closed.evidence)};
const readback = [{method:'get_rule',args:['publish-summary'],result:activated},
                  {method:'get_rule',args:['enable-followup'],result:closed}];
const path = 'contracts/roll_call_latch.py';
const bytes = await readFile(new URL('../' + path,import.meta.url));
const source = {path,sha256:createHash('sha256').update(bytes).digest('hex')};
console.log('EVIDENCE',JSON.stringify({address,transactions,activated,closed,source,equivalence,readback}));
