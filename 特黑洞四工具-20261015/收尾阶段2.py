# coding: utf-8
from pathlib import Path
import json,hashlib,collections
D=Path(__file__).parent
P=D/'完整阅读覆盖.json';d=json.loads(P.read_text())
for name in ['lemo-opuscar','awesome-opus5-5-videos','pdoom-video','opus-video-prompts']:
 d['by_skill'][name]=dict(collections.Counter(r['status'] for r in d['files'] if '/'+name+'/' in r['path']))
d['status']='进行中，225份全文已读，589未读；不是全读PASS'
d['pmo_stage1_received']={'source':'PMO message in current thread','report_sha':'cc2041dd10c98bf324fd276eed41286eb085d7980f35ac1892111ae852e982de','accepted_as':'阶段材料，非全读PASS'}
P.write_text(json.dumps(d,ensure_ascii=False,indent=2))
report=D/'四工具研读与制作应用.md';old=report.read_text()
if hashlib.sha256(report.read_bytes()).hexdigest()=='cc2041dd10c98bf324fd276eed41286eb085d7980f35ac1892111ae852e982de':
 (D/'四工具研读与制作应用-B01-B04历史.md').write_bytes(report.read_bytes())
latest='''## 最新进度｜B05—B08续读

完整目标仍未完成。当前225份全文已读、1份lockfile结构检查、2份精确SHA重复映射、589份未读，共817；815独立内容仍有589未完成。本次增加130份全文和1份结构检查，未重复前95份，README为补齐原截断。

|工具|全文已读|结构检查|重复映射|未读|
|---|---:|---:|---:|---:|
|opus-video-prompts|22|0|0|0|
|awesome-opus5-5-videos|165|0|0|544|
|Lemo|22|0|2|35|
|PDoom|16|1|0|10|

awesome README已按0—63120字符六段补全。703 prompt按字典序读完前160份；每个案例独立笔记在B04—B07（前40/B04，41—75/B05，76—140/B06，141—160/B07）。元数据data/videos.json仍未全文读，不能把读取prompt数量当JSON全部字段完成。中文54案例笔记继续保留。

Lemo新增art-deco/ascii-crt/backrooms/blueprint四份完整STYLE，共8/43风格。PDoom新增cast/props/lyrics/clawd四份共享代码与第一章全部39823字符，全部共享src已读。package-lock独立结构检查47个package记录：实际锁定puppeteer-core25.11.0要求Node>=22.12.0，不能套用Lemo的Node>=20当四库通用运行要求；p5的LGPL-2.1与项目package的ISC声明分开。不执行安装，不声称漏洞或兼容性测试通过。

新增适用方法：
- `brainextends-606193.md`：同一hero封面沿搜索→选中→详情→变色→特写保持身份；底部persistent player提供稳定锚点。可改为同一份资料/交付文件贯穿，标题先退再换，镜头越界统一裁到圆润舞台。
- `archiveexplorer-560622.md`：九拍先线框锁布局时长，再用DESIGN皮肤；可用于减少04先精修再改结构。Jev选择标题是原作者流程，不在本轮调用；九拍不是所有内容必用。
- `apoorvjain25-309680.md`及`…-945542.md`：音符与回复/反弹共读同一事件数据，声画不会靠手填两套时间漂移。只借同步机制，保留原声和平台BGM偏好。
- `src/clawd.js:mood`：变化前.08秒闭眼，后.16秒睁眼，接.16—.4秒回弹；可借“预备→动作→落定”，不复制角色或夸张弹跳。
- `src/ch/c01_lab.js:partial/lossRide/sledAt`：按弧长长出线，图表线变成角色滑行地形，相机取过去.14秒路径位置形成跟随。适合把抽象下降趋势接到空间过程；不冒充真实数据/物理模拟。
- `blueprint/STYLE.md`：尺寸线和编号跟部件一起走；制图顺序逐层建立。`art-deco`双门闭合在live画面上换场，`ascii-crt`余辉由时间解析而非累计，`backrooms`焦点与OSD时序各自承载信息。画风不适合时只借因果和坐标方法。

不变边界：原媒体观看0；225是文本/源码阅读，不是看225视频。源文件只读，04在途v6不动、Skills未改、没有运行第三方代码/新建agent/轮询/新费用。

### 当前准确接续位置

1. awesome第161份 `references/library/prompts/cyrilxbt-149036.md` 第1行，继续至703；前160无需重读。
2. awesome `references/library/data/videos.json` 全部案例字段仍未覆盖，之后按完整对象分批读，不因已读prompt直接标JSON全读。
3. Lemo下一份 `references/library/styles/brick-toy/STYLE.md` 第1行；35份STYLE未读，逐文件查覆盖账本，不重读已读8种。
4. PDoom下一章 `references/library/src/ch/c02_chorus1.js` 字符0；余c02—c09八章和legacy两份共10文件。共享src、第一章不重读；lock已结构检查。

此为自然批次接续点，不是全读验收。下一批直接继续既有授权，保留唯一Owner，不让用户重复确认。PMO已明确收到首阶段SHA并仅接收为阶段材料；本批发送/接收/验收继续分别记录。

---

以下为B01—B04首阶段方法及历史覆盖，覆盖计数/断点以本节和完整阅读覆盖.json为准。

'''
old=old.replace('## 本阶段覆盖','## 首阶段覆盖（B01—B04，历史）',1)
old=old.replace('## 接续位置与未完成范围','## 首阶段接续记录（已被上方最新断点覆盖）',1)
old=old.replace('## 文件与回报','## 文件与回报',1)
header='# 四工具研读与制作应用\n\n'
old=old[len(header):] if old.startswith(header) else old
report.write_text(header+latest+old)
changes=[]
for r in d['files']:
 if hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()!=r['sha256']:changes.append(r['path'])
out={'stage':'B05-B08','status':'INCOMPLETE_CHECKPOINT','counts':d['counts'],'by_skill':d['by_skill'],'source_hashes_unchanged':not changes,'changed':changes,'media_viewed':0,'third_party_code_executed':False,'model_actual':'UNKNOWN','effort_actual':'UNKNOWN','speed_actual':'UNKNOWN','next':d['continuation']}
(D/'阶段2核验.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
files=[]
for p in sorted(D.iterdir()):
 if p.is_file() and (p.name.startswith(('B0','阶段2','四工具研读','完整阅读','收尾阶段2','记录已读'))):
  files.append({'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'purpose':'reading/review/resume; retain'})
(D/'阶段2文件记录.json').write_text(json.dumps(files,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False));print('report_sha',hashlib.sha256(report.read_bytes()).hexdigest())
