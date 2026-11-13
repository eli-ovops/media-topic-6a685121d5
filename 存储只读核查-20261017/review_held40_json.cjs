// Parse inert JSON literals from webpack artifacts. Never evaluates bundle code.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const root = __dirname;
const evidence = JSON.parse(fs.readFileSync(path.join(root, 'held40-review-evidence.json'), 'utf8'));
const acorn = require(path.join(evidence.bundles[0].project, 'node_modules/acorn'));
const hash = (s) => crypto.createHash('sha256').update(s).digest('hex');
const versions = new Map(), records = [], errors = [], uncovered = [];
function same(a,b) { return JSON.stringify(a) === JSON.stringify(b); }
function subset(a,b) {
  if (a === null || typeof a !== 'object') return same(a,b);
  if (b === null || typeof b !== 'object' || Array.isArray(a) !== Array.isArray(b)) return false;
  if (Array.isArray(a)) return same(a,b);
  return Object.keys(a).every(k=>Object.prototype.hasOwnProperty.call(b,k) && subset(a[k],b[k]));
}
function decode(node) {
  if (node.type === 'Literal' && (node.value === null || ['string','number','boolean'].includes(typeof node.value))) return node.value;
  if (node.type === 'UnaryExpression' && node.operator === '-' && node.argument.type === 'Literal' && typeof node.argument.value === 'number') return -node.argument.value;
  if (node.type === 'ArrayExpression') return node.elements.map(decode);
  if (node.type === 'ObjectExpression') {
    const obj = Object.create(null);
    for (const prop of node.properties) {
      if (prop.type !== 'Property' || prop.computed || prop.kind !== 'init' || prop.method || prop.shorthand) throw new Error('Unsupported JSON property');
      const key = prop.key.type === 'Identifier' ? prop.key.name : prop.key.value;
      Object.defineProperty(obj, key, {value: decode(prop.value), enumerable: true});
    }
    return obj;
  }
  if (node.type === 'CallExpression' && node.callee.type === 'MemberExpression' && !node.callee.computed && node.callee.object.name === 'JSON' && node.callee.property.name === 'parse' && node.arguments.length === 1 && node.arguments[0].type === 'Literal' && typeof node.arguments[0].value === 'string') return JSON.parse(node.arguments[0].value);
  throw new Error('Not an inert JSON expression: ' + node.type);
}
for (const bundle of evidence.bundles) {
  const localRecords = [];
  for (const artifact of bundle.artifact_files.filter(x => x.path.endsWith('.js'))) {
    const text = fs.readFileSync(artifact.path, 'utf8');
    if (hash(text) !== artifact.sha256) throw new Error('Artifact changed: ' + artifact.path);
    const pattern = /(?:^|\n);\/\/ ([^\r\n]+\.json)\r?\n/g;
    for (const match of text.matchAll(pattern)) {
      const moduleName = match[1];
      if (moduleName.includes('node_modules')) continue;
      const start = match.index + match[0].length;
      const declaration = /^(?:const|var|let)\s+[\w$]+\s*=\s*/.exec(text.slice(start, start+500));
      if (!declaration) {
        errors.push({bundle:bundle.path,artifact:artifact.path,module:moduleName,status:'UNSUPPORTED_DECLARATION'});
        continue;
      }
      try {
        const expressionStart = start + declaration[0].length;
        const expression = acorn.parseExpressionAt(text, expressionStart, {ecmaVersion:'latest'});
        const value = decode(expression);
        const serialized = JSON.stringify(value);
        const sourcePath = path.resolve(bundle.project, moduleName);
        const project = bundle.project.includes('Fred') ? 'fred' : 'qianwen';
        let currentValue = null, currentHash = null, status = 'CURRENT_JSON_MISSING';
        if (fs.existsSync(sourcePath)) {
          const st = fs.lstatSync(sourcePath);
          if (!st.isFile() || st.isSymbolicLink()) throw new Error('Source JSON is not a plain file');
          currentValue = JSON.parse(fs.readFileSync(sourcePath, 'utf8'));
          currentHash = hash(JSON.stringify(currentValue));
          status = currentHash === hash(serialized) ? 'SAME_STRUCTURED_VALUE' :
            (subset(value,currentValue) ? 'SUBSET_OF_CURRENT_JSON' : 'DIFFERENT_STRUCTURED_VALUE');
        }
        const rec = {bundle:bundle.path, artifact:artifact.path, module:moduleName, source_path:sourcePath,
          expression_start:expression.start, expression_end:expression.end, structured_sha256:hash(serialized),
          normalized_bytes:Buffer.byteLength(serialized), current_structured_sha256:currentHash, status,
          raw_expression_bytes:Buffer.byteLength(text.slice(expression.start,expression.end)),
          raw_expression_sha256:hash(text.slice(expression.start,expression.end)),
          value_type:Array.isArray(value)?'array':typeof value, top_keys:value && typeof value==='object'?Object.keys(value).slice(0,15):[],
          provenance:'acorn parsed literal only; JSON.parse on literal strings; bundle code never evaluated'};
        records.push(rec); localRecords.push(rec);
        const key = project + '/' + moduleName + '@' + rec.structured_sha256;
        if (!versions.has(key)) versions.set(key,{...rec,key,occurrences:[]});
        versions.get(key).occurrences.push({bundle:bundle.path,artifact:artifact.path,expression_start:expression.start,expression_end:expression.end});
      } catch (e) { errors.push({bundle:bundle.path,artifact:artifact.path,module:moduleName,status:'PARSE_ERROR',error:String(e)}); }
    }
  }
  for (const source of bundle.project_source_records) {
    const sourcePath = path.resolve(bundle.project, source.source);
    for (const ref of source.imports.filter(x=>x.startsWith('.') && x.endsWith('.json'))) {
      const expected = path.resolve(path.dirname(sourcePath),ref);
      if (!localRecords.some(x=>x.source_path===expected)) uncovered.push({bundle:bundle.path,source:source.source,reference:ref,resolved_path:expected});
    }
  }
}
const unique = [...versions.values()];
const result = {checked_at:new Date().toISOString(),read_only:true,deleted_count:0,archived_asset_count:0,
  records,unique_versions:unique,errors,uncovered_imports:uncovered,
  summary:{bundle_count:evidence.bundles.length,json_records:records.length,json_unique_versions:unique.length,
    json_unique_normalized_bytes:unique.reduce((n,x)=>n+x.normalized_bytes,0),
    json_unique_raw_expression_bytes:unique.reduce((n,x)=>n+x.raw_expression_bytes,0),
    json_status_counts:unique.reduce((o,x)=>(o[x.status]=(o[x.status]||0)+1,o),{}),
    historical_json_unique_versions:unique.filter(x=>x.status!=='SAME_STRUCTURED_VALUE').length,
    historical_json_normalized_bytes:unique.filter(x=>x.status!=='SAME_STRUCTURED_VALUE').reduce((n,x)=>n+x.normalized_bytes,0),
    unsupported_or_errors:errors.length,uncovered_import_count:uncovered.length}};
fs.writeFileSync(path.join(root,'held40-json-dependency-evidence.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result.summary));
for (const v of unique.filter(x=>x.status!=='SAME_STRUCTURED_VALUE')) console.log(JSON.stringify({module:v.module,sha256:v.structured_sha256,bytes:v.normalized_bytes,status:v.status,occurrences:v.occurrences.length}));
