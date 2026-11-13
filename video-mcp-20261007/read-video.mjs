import {Client} from './upstream/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import {StdioClientTransport} from './upstream/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.dirname(fileURLToPath(import.meta.url));
const source=process.argv[2] ?? JSON.parse(readFileSync(path.join(root,'allowed-files.json'),'utf8'))[0];
const mode=process.argv[3] ?? 'analyze';
if(!['info','analyze'].includes(mode))throw new Error('Usage: node read-video.mjs [absolute-approved-video-path] [info|analyze]');
const transport=new StdioClientTransport({command:process.execPath,args:[path.join(root,'launch.mjs')],env:{PATH:'/usr/bin:/bin'},stderr:'pipe'});
const client=new Client({name:'local-video-cli',version:'1.0.0'});
try{
 await client.connect(transport);
 const name=mode==='info'?'video_info':'video_analyze';
 const args=mode==='info'?{source,response_format:'json'}:{source,detail:'detailed',max_frames:30,mode:'interval',language:'zh',skip_ocr:true,inline_images:true,response_format:'json'};
 const result=await client.callTool({name,arguments:args},undefined,{timeout:180000});
 const output=path.join(root,'evidence',`cli-${mode}-${Date.now()}-${process.pid}.json`);
 writeFileSync(output,JSON.stringify(result,null,2),{flag:"wx"});
 if(result.isError){console.error(result.content?.filter(x=>x.type==='text').map(x=>x.text).join('\n'));process.exitCode=1;}
 else{
 const s=result.structuredContent;
 console.log(JSON.stringify({success:true,tool:name,rawResult:output,info:s?.info??s,transcript:s?.transcript,frames:s?.frames,inlineCount:s?.inlineCount,warnings:s?.warnings,limitations:'ASR文字不是直接听音；图片是时间采样；没有连续视频输入。'},null,2));
 }
}finally{await client.close();}
