import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { abi } from 'genlayer-js';
import { read, reader, verify } from './studionet.mjs';

const file = (path) => readFile(new URL(path,import.meta.url),'utf8');
const evidence = JSON.parse(process.argv[2] ? await readFile(resolve(process.argv[2]),'utf8') : await file('../EVIDENCE.json'));
const lint = JSON.parse(await file('../LINT.json'));
const source = await file('../' + evidence.source.path);
assert.equal(Number(await reader.request({method:'eth_chainId'})),61999);
assert.equal(await reader.getContractCode(evidence.address),source);
assert.equal(createHash('sha256').update(source).digest('hex'),evidence.source.sha256);
assert.ok(lint.ok && lint.lint.ok && lint.validate.ok);

for (const [name, item] of Object.entries(evidence.transactions)) {
  const observed = await verify(item.hash,item.error);
  assert.equal(observed.execution,item.execution,name);
  const tx = await reader.getTransaction({hash:item.hash});
  assert.equal(tx.data?.contract_address ?? tx.to_address,evidence.address,name);
  const expected = evidence.equivalence[name];
  if (expected !== undefined) {
    const leader = tx.consensus_data.leader_receipt.find((row) => row.mode === 'leader');
    const outputs = Object.values(leader.eq_outputs ?? {});
    assert.equal(outputs.length,1,name);
    const raw = Buffer.from(typeof outputs[0] === 'string' ? outputs[0] : outputs[0].raw,'base64');
    assert.equal(raw[0],0,name);
    assert.equal(abi.calldata.decode(raw.subarray(1)),expected,name);
  }
}
for (const {method,args,result} of evidence.readback) {
  assert.deepEqual(await read(evidence.address,method,args),result);
}
console.log('Verified exact deployed source, lint record, finalized receipts, equivalence results and state.');
