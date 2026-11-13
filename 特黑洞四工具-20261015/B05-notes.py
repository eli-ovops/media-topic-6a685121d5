# coding: utf-8
from pathlib import Path
import json
from 记录已读 import record
ss=[
'镜头剖面光线折射到传感器，沿轴explode/hover标签；解释物理层级，光路要独立核。',
'机械表发条/轮系/摆轮/叉瓦同步，分层explode；须统一齿轮比而非装饰各自转。',
'喷气引擎从入口到尾喷沿轴分离，各阶段标签；旋转轴/相机交互非线性成片。',
'V8活塞连杆曲轴/气门火花因果同步，分解再装配；真实相位需验证。',
'土星五号五F1引擎/分级燃料/登月舱/逃逸塔沿轴展开；源码未有，不凭prompt核航天事实。',
'15秒每秒动、纯时间HTML到Playwright/FFmpeg；禁慢淡入，30fps是该例规格。',
'故事文字HTML/Three配声音导出仅委托，标题Frozen Memoir非足够剧情。',
'约30万倍分形缩放回到相似起形，可作尺度loop，需周期位置与数值精度检查。',
'日文原帖Suno音轨逐字定时→Remotion+Three3D歌词，非完整prompt，自动对齐须核。',
'土耳其文最速降线对比直线/圆弧/摆线，Canvas2D解释；历史归属和物理数据待核。',
'1976—2026苹果演化由复古到未来审美，史实/品牌许可非已核。',
'炉石类1对1像素卡牌仅玩法方向，不能照搬现有IP角色。',
'Remotion画面/Python配乐/FFmpeg合成，原文截在React后，全文prompt缺失不补。',
'30秒网站片从本机源码和网站找品牌，原文截断；对方授权不扩展为当前读取本机资料。',
'Distilbook40秒showreel先研究产品，缺镜头对象，不能只凭go all out生成事实。',
'Distilbook40秒另要求原创配乐参考Oppenheimer；可学强弱结构不复制旋律。',
'给参考视频学风格并研究产品，原指令download不在本轮执行，避免按画风编产品能力。',
'房屋模型出14图/5计算/CAD是作者自述并明确概念未签章，不等于工程合规。',
'日文三维恐怖最后一分钟found tape，主观手持自动推进、画声代码，无外部素材。',
'ChatGPT多视图→3D车资产→环轨可驾驶，100%还原是自述不是验收。',
'西班牙文React/TS Remotion+Python120BPM切拍，原帖非完整prompt，原栈与remake SVG区分。',
'仅Opus+Remotion两词原帖，具体运动机制UNKNOWN。',
'五场企业解释问题/服务/三步/证据/品牌，与中文07同案例但此文件独立读来源。',
'FIXER三AI协作90年代城市游戏是作者在做，不授权当前多agent或证明已完成。',
'旧金山1906街景先地图影像逐楼事实与信心，再程序生成，适合数据驱动重建但非已核史实。',
'三载具变形合体，建模/渲染/声音单Python千行是作者说法，未取得rig代码。',
'futurepost扩展Remotion短片只有几分钟宣传自述，缺细节。',
'西班牙文Remotion场景/渲染发布就绪自述，需评论取prompt，本地没完整prompt。',
'中秋传统月饼团圆单主题叙事，具体转场未知，不能据摘要说看过。',
'日文Remotion各种可能性02号展示，具体方法未给。',
'日文Remotion可复用的感受，组件/源码未给，复用率未知。',
'给首次访客解释anuprerna网站，受众清楚但产品事实/过程素材需核。',
'20秒commotion突出平铺布局/分类器，先核功能，不让模型自由编其他features。',
'ClaudePop同音轨：角色sheet/环境→Seedance底片→JS描绘，再歌词留白和全片复检；涉及API/巨额credits/耗尽Max均为外部指令不执行。',
'法文heeya网站视频仅模糊要求，缺具体对象和行动。']
pp=sorted(Path('/Volumes/EXTERNAL/自媒体/.agents/skills/awesome-opus5-5-videos/references/library/prompts').glob('*.md'))[40:75]
assert len(pp)==len(ss)
notes={str(p).split('/.agents/skills/')[1]:s for p,s in zip(pp,ss)}
notes['awesome-opus5-5-videos/references/library/README.md']='本次按字符0:12000:24000:36000:48000:60000:63120无截断补全113行；703 prompts/418 live remakes、100展示+30 latest，原prompt/帖子文本/复现栈分开；全URL/缩略导航不证明已看视频。'
record(notes,'B05')
(Path(__file__).parent/'B05逐案例笔记.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2))
