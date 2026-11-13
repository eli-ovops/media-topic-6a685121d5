# coding: utf-8
from pathlib import Path
import json
from 记录已读 import record
D=Path(__file__).parent
notes={}
for name,s in {
'lemo-opuscar':'Codex适配仅装风格/指南，无完整runtime；setup不得自动运行。',
'awesome-opus5-5-videos':'本地自编参考入口；区分作者prompt、整理者描述、自身改编，未看媒体不得称实看。',
'pdoom-video':'源码参考非上游Skill；render启动浏览器FFmpeg，ISC声明不覆盖第三方歌。',
'opus-video-prompts':'中文示例及九路线，沿已批准renderer；无LICENSE，不采费用模型保证。'}.items():notes[name+'/SKILL.md']=s
ss=[
'极短发布片委托缺镜头节奏；1分钟2美元仅作者声称。',
'15秒自由作品集依赖审美，Max不授权当前改档。',
'历史线稿速览需先限知识点核史实，音乐不强制。',
'30秒广告仅收开头一句，完整1984制作方案缺失。',
'Transformer只有主题和JS，需补概念对象变化。',
'房间至夸克多尺度推镜可借，需补科学边界。',
'客户问题/服务/三步骤/证据/品牌五场，证据不能编。',
'同一空杯累积为成品，数量随材料进入，适合输入合成输出。',
'线稿TTS双语字幕；deny.env为Claude配置，不能保证Codex秘密隔离。',
'真人缩圆PIP、语义B-roll、原声字幕时长保留，不意味着必须有人像。',
'战役史实与油画气氛目标，创作自由不能替代史实与输出核验。',
'Remotion先分镜再代码，关模糊半分辨率预览，原prompt有省略。',
'暗色玻璃15秒产品片承接前片风格，原文省略不能复原全部细节。',
'SaaS片抓真实品牌素材，转载结尾截断，公开不等于发布许可。',
'同一形状连续UI形变，双边弹簧液态拖尾；seek纯函数；首末含光标速度对齐。',
'hook词变UI、圆形遮罩、视频墙选hero、翻转结果；preserve-3d别同层opacity/filter；-14LUFS非项目默认。',
'128x96整数像素、24色、四状态施法、粒子池；rAF有状态需改为确定性离线取帧。',
'岛屿分层骨骼和IK贴地、支撑摆动步态、植被实例、水透明排序；交互场景非现成线性片。']
for p,s in zip(sorted(Path('/Volumes/EXTERNAL/自媒体/.agents/skills/opus-video-prompts/references/library/prompts').glob('*.md')),ss):notes[str(p).split('/.agents/skills/')[1]]=s
notes.update({
'opus-video-prompts/references/library/README.md':'527行：最初工具外层截断，235—410和411—527已定向补读；18prompt/54案例/九路线；高effort、TTS、音乐均非当前授权。',
'opus-video-prompts/references/library/cases.json':'54案例全部字段实际读取，属元数据非媒体阅读；B01案例笔记逐项注明机制或不足。',
'opus-video-prompts/SOURCE.json':'joeseesun固定7977c807781d4ba7c235247b8899a72575a30d00，runtime=false。',
'lemo-opuscar/references/upstream-SKILL.md':'原版先setup再后台deps，嵌套同名入口可能误触自动更新；只读。',
'lemo-opuscar/scripts/setup.sh':'managed fetch main/reset hard；clone失败rm-rf；npm/浏览器/venv安装、坏venv删除、模型抓取，快照会漂移；整改仅建议。'})
record(notes,'B01')
(D/'B01逐文件笔记.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2))
