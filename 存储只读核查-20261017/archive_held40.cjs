// Extract approved inert source/data objects. No webpack artifact is executed.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const root = __dirname;
const read = p => JSON.parse(fs.readFileSync(p,'utf8'));
const planPath = path.join(root,'held40-preservation-plan.json');
const plan = read(planPath), pre = read(path.join(root,'held40-cleanup-preflight.json'));
const archive = plan.proposed_archive_directory;
const digest = b => crypto.createHash('sha256').update(b).digest('hex');
const assert = (ok,message) => { if(!ok) throw new Error(message); };
assert(digest(fs.readFileSync(planPath))===pre.plan_sha256,'Plan changed');
const acorn = require(path.join(pre.targets[0].project,'node_modules/acorn'));
const files = new Map(), maps = new Map(), artifacts = new Map();

function jsonLiteral(node) {
  if(node.type==='Literal' && (node.value===null || ['string','number','boolean'].includes(typeof node.value))) return node.value;
  if(node.type==='UnaryExpression' && node.operator==='-' && node.argument.type==='Literal' && typeof node.argument.value==='number') return -node.argument.value;
  if(node.type==='ArrayExpression') return node.elements.map(jsonLiteral);
  if(node.type==='ObjectExpression') {
    const obj=Object.create(null);
    for(const p of node.properties) {
      assert(p.type==='Property' && !p.computed && p.kind==='init' && !p.method && !p.shorthand,'Non-inert JSON property');
      Object.defineProperty(obj,p.key.type==='Identifier'?p.key.name:p.key.value,{value:jsonLiteral(p.value),enumerable:true});
    }
    return obj;
  }
  if(node.type==='CallExpression' && node.callee.type==='MemberExpression' && !node.callee.computed && node.callee.object.name==='JSON' && node.callee.property.name==='parse' && node.arguments.length===1 && node.arguments[0].type==='Literal' && typeof node.arguments[0].value==='string') return JSON.parse(node.arguments[0].value);
  throw new Error('Non-inert JSON expression: '+node.type);
}
function safeDestination(dest) {
  const resolved=path.resolve(dest);
  assert(resolved.startsWith(archive+path.sep),'Archive destination outside approved root');
  let current=archive;
  for(const part of path.relative(archive,path.dirname(resolved)).split(path.sep).filter(Boolean)) {
    current=path.join(current,part);
    if(fs.existsSync(current)) assert(fs.lstatSync(current).isDirectory() && !fs.lstatSync(current).isSymbolicLink(),'Archive parent not a plain directory');
    else fs.mkdirSync(current);
  }
  return resolved;
}
function put(dest,content,role,expectedHash) {
  const payload=Buffer.isBuffer(content)?content:Buffer.from(content,'utf8');
  const h=digest(payload);
  if(expectedHash) assert(h===expectedHash,'Extracted payload hash mismatch: '+dest);
  dest=safeDestination(dest);
  if(fs.existsSync(dest)) {
    assert(fs.lstatSync(dest).isFile() && !fs.lstatSync(dest).isSymbolicLink(),'Archive file identity/type changed');
    const existing=fs.readFileSync(dest);
    if(digest(existing)!==h) {
      // Only this task's deterministic, incomplete snapshot reports may change.
      const approved=plan.snapshots.find(s=>s.proposed_snapshot_path===dest);
      const prior=previousManifest?.files.find(x=>x.relative_path===path.relative(archive,dest));
      const ownGeneratedReport=['archive-readme','current-source-supplement-catalog'].includes(role) && prior && prior.sha256===digest(existing);
      assert(resuming && ((role==='version-snapshot-mapping' && approved) || ownGeneratedReport),'Will not overwrite an unknown archive asset');
      if(role==='version-snapshot-mapping') assert(JSON.stringify(JSON.parse(existing).original_snapshot)===JSON.stringify(approved),'Existing snapshot does not belong to this plan');
      const fd=fs.openSync(dest,'w');
      try{fs.writeFileSync(fd,payload);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
    }
  } else {
    const fd=fs.openSync(dest,'wx');
    try { fs.writeFileSync(fd,payload); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
  }
  assert(digest(fs.readFileSync(dest))===h,'Archive read-back hash mismatch');
  if(!files.has(dest)) files.set(dest,{relative_path:path.relative(archive,dest),bytes:payload.length,sha256:h,roles:[role]});
  else if(!files.get(dest).roles.includes(role)) files.get(dest).roles.push(role);
  return dest;
}
function srcBody(e) {
  for(const occurrence of e.occurrences) {
    if(!maps.has(occurrence.map)) maps.set(occurrence.map,read(occurrence.map));
    const m=maps.get(occurrence.map);
    for(let i=0;i<m.sources.length;i++) {
      if(m.sources[i]!==e.source || typeof m.sourcesContent[i]!=='string') continue;
      const body=m.sourcesContent[i];
      if(digest(Buffer.from(body))===e.sha256) return body;
    }
  }
  throw new Error('No source-map content matching approved version '+e.key);
}
function artifactText(p) {
  if(!artifacts.has(p)) {
    const raw=fs.readFileSync(p);
    const target=pre.targets.find(t=>p.startsWith(t.path+path.sep));
    assert(target,'Unknown artifact origin');
    const rel=path.relative(target.path,p);
    assert(target.tree[rel].sha256===digest(raw),'Artifact changed before extraction');
    artifacts.set(p,raw.toString('utf8'));
  }
  return artifacts.get(p);
}
const resuming=fs.existsSync(archive);
let owner, previousManifest=null;
if(resuming) {
  owner=read(path.join(archive,'archive-owner.json'));
  assert(owner.task==='held40-archive-cleanup-20261017' && owner.plan_sha256===pre.plan_sha256 && !fs.existsSync(path.join(root,'held40-archive-verification.json')) && !fs.existsSync(path.join(root,'held40-deletion-receipt.json')),'Existing archive has been verified or is outside this task');
  if(fs.existsSync(path.join(archive,'archive-manifest.json'))) {
    previousManifest=read(path.join(archive,'archive-manifest.json'));
    assert(previousManifest.plan_sha256===pre.plan_sha256,'Prior manifest belongs to a different plan');
  }
} else {
  fs.mkdirSync(archive,{recursive:true});
  owner={task:'held40-archive-cleanup-20261017',plan_sha256:pre.plan_sha256,created_at:new Date().toISOString(),source_scope:pre.authorization.exact_paths_csv};
}
assert(fs.realpathSync(archive)===archive && !fs.lstatSync(archive).isSymbolicLink(),'Archive root alias');
put(path.join(archive,'archive-owner.json'),JSON.stringify(owner,null,2)+'\n','ownership');

const sourceLookup=new Map(), jsonLookup=new Map(), partialLookup=new Map();
for(const e of plan.source_objects) {
  const body=srcBody(e);
  assert(Buffer.byteLength(body)===e.bytes,'Source length mismatch');
  put(e.proposed_path,body,e.historical_difference?'historical-source':'shared-source-dependency',e.sha256);
  sourceLookup.set(e.key,e.proposed_path);
}
for(const e of plan.json_objects) {
  const text=artifactText(e.artifact);
  const expression=acorn.parseExpressionAt(text,e.expression_start,{ecmaVersion:'latest'});
  assert(expression.end===e.expression_end,'JSON expression bounds changed');
  const raw=text.slice(expression.start,expression.end);
  const normalized=JSON.stringify(jsonLiteral(expression));
  assert(Buffer.byteLength(raw)===e.raw_expression_bytes && Buffer.byteLength(normalized)===e.normalized_bytes,'JSON extraction length mismatch');
  put(e.proposed_path,normalized,'structured-json-'+e.status,e.structured_sha256);
  put(e.proposed_raw_expression_path,raw,'raw-inert-json-expression',e.raw_expression_sha256);
  jsonLookup.set(e.key,e);
}
for(const e of plan.incomplete_media_evidence) {
  const raw=fs.readFileSync(e.paths[0]);
  assert(raw.length===e.bytes,'Incomplete-media length changed');
  put(e.proposed_path,raw,'incomplete-media-evidence-not-playable',e.sha256);
  for(const origin of e.paths) partialLookup.set(origin,e.proposed_path);
}
for(const e of plan.current_build_reference) {
  const raw=fs.readFileSync(e.source);
  put(e.proposed_path,raw,'current-build-reference-not-proven-historical',e.sha256);
}

const unresolved=[];
const supplements=[];
const supplementLookup=new Map();
const supplementDependencies=[];
// This current helper is imported in the historical text but omitted from its
// sourcemaps by webpack. Preserve it separately, never call it historical code.
const fredProject=pre.targets.find(t=>t.project.includes('Fred')).project;
const supplementSource=path.join(fredProject,'src/codex-vendor/components/FullscreenVideoWindow.tsx');
function preserveCurrentHelper(source) {
  if(supplementLookup.has(source)) return supplementLookup.get(source);
  assert(source.startsWith(path.join(fredProject,'src')+path.sep),'Supplement outside protected source scope');
  const st=fs.lstatSync(source);
  assert(st.isFile() && !st.isSymbolicLink() && st.size<1024*1024 && supplements.length<16,'Supplement scope/type limit');
  const bytes=fs.readFileSync(source), h=digest(bytes);
  const dest=path.join(archive,'current-source-supplements',h,path.basename(source));
  put(dest,bytes,'current-source-supplement-not-proven-historical',h);
  supplementLookup.set(source,dest);
  supplements.push({source,archive_path:dest,sha256:h,bytes:bytes.length,
    provenance:'Current preserved project helper; not proven to be the bundled historical version.'});
  const imports=[...bytes.toString('utf8').matchAll(/from\s*['"]([^'"]+)['"]/g)].map(m=>m[1]).filter(x=>x.startsWith('.'));
  for(const dependency of imports) {
    const resolved=path.resolve(path.dirname(source),dependency);
    const target=['','.tsx','.ts','.js','/index.tsx','/index.ts'].map(s=>resolved+s).find(x=>fs.existsSync(x) && fs.lstatSync(x).isFile());
    assert(target,'Current helper has an unresolved local import');
    supplementDependencies.push({source,dependency,archive_path:preserveCurrentHelper(target)});
  }
  return dest;
}
preserveCurrentHelper(supplementSource);
const sourceObjects=new Map(plan.source_objects.map(e=>[e.key,e]));
const jsonEntries=plan.json_objects;
for(const snap of plan.snapshots) {
  const sourcePaths={}, jsonPaths=[];
  for(const [source,key] of Object.entries(snap.source_mapping)) {
    assert(sourceLookup.has(key),'Snapshot source object missing');
    sourcePaths[source]=sourceLookup.get(key);
  }
  const snapshotJson= [];
  for(const e of snap.json_mapping) {
    const current=jsonEntries.find(v=>v.module===e.module && v.structured_sha256===e.structured_sha256 && v.occurrences.some(o=>o.bundle===snap.bundle));
    assert(current,'Snapshot JSON object missing');
    jsonPaths.push({module:e.module,archive_value:current.proposed_path,archive_raw_expression:current.proposed_raw_expression_path,status:e.status});
    snapshotJson.push(current);
  }
  const resolutions=[];
  for(const [source,key] of Object.entries(snap.source_mapping)) {
    const e=sourceObjects.get(key);
    for(const dependency of e.imports.filter(x=>x.startsWith('.'))) {
      const resolved=path.resolve(path.dirname(path.resolve(snap.original_project,source)),dependency);
      let target=null;
      if(dependency.endsWith('.json')) target=snapshotJson.find(x=>x.source_path===resolved)?.proposed_path;
      else {
        for(const suffix of ['', '.tsx','.ts','.js','/index.tsx','/index.ts']) {
          const found=Object.keys(snap.source_mapping).find(s=>path.resolve(snap.original_project,s)===resolved+suffix);
          if(found) { target=sourcePaths[found]; break; }
          if(supplementLookup.has(resolved+suffix)) {target=supplementLookup.get(resolved+suffix);break;}
        }
      }
      resolutions.push({source,dependency,archive_path:target});
      if(!target) unresolved.push({bundle:snap.bundle,source,dependency,resolved});
    }
  }
  const media=snap.public_reference_manifest.map(e=>({bundle_file_before_deletion:e.path,preserved_original:e.original,original_sha256:e.original_sha256,
    bundle_file_sha256:e.sha256,archived_difference_file:partialLookup.get(e.path)||null,status:e.status}));
  put(snap.proposed_snapshot_path,JSON.stringify({original_snapshot:snap,source_archive_paths:sourcePaths,json_archive_paths:jsonPaths,
    static_local_dependencies:resolutions,media_resolution:media,
    note:'Historical source/data snapshot. Provenance temp paths are deleted only after archive verification. Current original media stays in its project; no standalone render claimed.'},null,2)+'\n','version-snapshot-mapping');
}
assert(unresolved.length===0,'Unresolved static dependencies: '+JSON.stringify(unresolved));

const catalog=plan.source_objects.map(e=>({key:e.key,sha256:e.sha256,source:e.source,historical_difference:e.historical_difference,use:e.use,
  archive_path:e.proposed_path,original_occurrences:e.occurrences}));
put(path.join(archive,'source-catalog.json'),JSON.stringify(catalog,null,2)+'\n','source-catalog');
put(path.join(archive,'json-catalog.json'),JSON.stringify(plan.json_objects.map(e=>({key:e.key,module:e.module,source_path:e.source_path,
  status:e.status,structured_sha256:e.structured_sha256,raw_expression_sha256:e.raw_expression_sha256,
  archive_value:e.proposed_path,archive_raw_expression:e.proposed_raw_expression_path,original_occurrences:e.occurrences})),null,2)+'\n','json-catalog');
put(path.join(archive,'incomplete-media-catalog.json'),JSON.stringify(plan.incomplete_media_evidence,null,2)+'\n','incomplete-media-catalog');
put(path.join(archive,'current-source-supplement-catalog.json'),JSON.stringify(supplements,null,2)+'\n','current-source-supplement-catalog');
put(path.join(archive,'README.md'),`# Remotion历史版本归档（2026-10-17）

来自用户批准清理的40个临时包。正式原工程、Fred付费资料、333组件库和Skills均保留在原处。

- source-objects：53份源码版本，其中27份为相对当前工程不同的历史版本。精确内容由SHA定位，见source-catalog.json。
- json-objects和raw-json-expressions：30份打包配置/轨迹及原始惰性表达式；18份结构值不同、2份为当前值子集、10份结构值相同。裁剪值不能冒充作者原始完整JSON。
- snapshots：40份源码、JSON和素材对应关系。还原某个历史快照时先读对应文件，不要混用不同版本。
- incomplete-media-evidence：6份按SHA去重的未完成MP4，仅取证用途；原9条差异中4条为空壳、5条载荷是原件前段，不作为可播放素材调用。
- current-build-reference：当前工程的构建配置，仅参考；未证明历史依赖版本，未构建或渲染。
- current-source-supplements：另存${supplements.length}份当前辅助源码及其本地依赖，不冒充当时的历史版本。
- archive-manifest.json：每个归档文件的大小和SHA；本档案没有覆盖生产工程或改变默认制作风格。

临时包内2940份重复素材仍由原工程保存，snapshots记录原件绝对路径与SHA；本档案依赖这些保留原件，并非一个可独立播放或直接渲染的工程。

原始核查及后续删除回执位于：${root}。临时包来源路径是历史定位，不是删除后仍存在的文件链接。
`,'archive-readme');

const manifest={status:'ARCHIVED_STATIC_DEPENDENCY_CHECK_PASSED',archived_at:new Date().toISOString(),plan_sha256:pre.plan_sha256,
  logical_counts:{source_versions:53,json_versions:30,snapshot_mappings:40,incomplete_media_unique_files:6,current_build_reference_files:6,current_source_supplemental_files:supplements.length},
  supplemental_source_files:supplements,
  supplemental_dependency_resolutions:supplementDependencies,
  unresolved_static_dependencies:unresolved,source_temp_paths:pre.targets.map(x=>x.path),
  files:[...files.values()].sort((a,b)=>a.relative_path.localeCompare(b.relative_path)),
  executed_bundle_code:false,build_or_render_performed:false,
  limitations:['JSON values reflect observed bundled values, including tree-shaken subsets.','Current package manifests are reference only; historical runtime dependency identity UNKNOWN.','Static dependency and byte checks are not a build/render or continuous video review.']};
const manifestPath=path.join(archive,'archive-manifest.json');
if(previousManifest) assert(digest(fs.readFileSync(manifestPath))===digest(fs.readFileSync(path.join(root,'held40-archive-initial-build-manifest.json'))),'Prior manifest changed unexpectedly');
const fd=fs.openSync(manifestPath,previousManifest?'w':'wx');
try{fs.writeFileSync(fd,JSON.stringify(manifest,null,2)+'\n');fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
console.log(JSON.stringify({status:manifest.status,archive,file_count:files.size+1,payload_bytes:[...files.values()].reduce((n,x)=>n+x.bytes,0),logical_counts:manifest.logical_counts,unresolved_static_dependencies:unresolved.length}));
