# coding: utf-8
from pathlib import Path
import json,re
from 记录已读 import record
notes={
'pdoom-video/references/library/src/ch/c01_lab.js':'全文字符0—39823分两批实际读；partial按折线弧长出线，图中LOSS曲线变可滑地形，sledAt分hop/slide/teeter/fall/land；相机跟过去.14秒位置形成滞后，咖啡抛物线落点共TOSS拍；走廊门按ROUTES开合角色逐次放大，牙口irisShape闭合交下一章。未渲染不得说动作顺滑。',
'lemo-opuscar/references/library/styles/backrooms/STYLE.md':'45—60秒4:3手持found footage，空间重复/规则/OSD时间跳动叙事；灯光DataTexture近邻和局部雾；VHS非CRT，OSD不受畸变；focus近拉才模糊，视纸需镜头平行；无score不是强制本项目配乐规则。',
'lemo-opuscar/references/library/styles/blueprint/STYLE.md':'一张蓝图2D制图顺序中心线→外形→细节→剖面→尺寸→标注；弧长draw-on，注解绑定移动部件，斜投影深度从0变.5；线宽随zoom^.65，纸/墨/fx/字幕分buffer，爆炸图避页眉；不能拿蓝图示意当工程验算。'}
record(notes,'B08')
D=Path(__file__).parent
(D/'B08逐文件笔记.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2))
P=D/'完整阅读覆盖.json';d=json.loads(P.read_text());n=len(re.findall(r'\[\d+(?:\.\d+)?,\s*\d+(?:\.\d+)?,\s*"',Path('/Volumes/EXTERNAL/自媒体/.agents/skills/pdoom-video/references/library/src/lyrics.js').read_text()))
for r in d['files']:
 if r['path'].endswith('/pdoom-video/references/library/src/lyrics.js'):r['summary']=f'{n}条歌词时间区间全部读取，来自源字幕而非词级听音；不复述歌词，不把隐喻当科学事实。'
 if r['path'].endswith('/awesome-opus5-5-videos/references/library/README.md'):
  r.pop('remaining',None);r['read_char_ranges']=[[0,12000],[12000,24000],[24000,36000],[36000,48000],[48000,60000],[60000,63120]]
d['continuation']={'next_path':'/Volumes/EXTERNAL/自媒体/.agents/skills/awesome-opus5-5-videos/references/library/prompts/cyrilxbt-149036.md','next_range':'prompt161 line1 onward; first160 complete; data/videos.json remains unread','other_next':{'lemo':'styles/brick-toy/STYLE.md line1; art-deco/ascii-crt/backrooms/blueprint plus four previous full read','pdoom':'src/ch/c02_chorus1.js char0; c01 and all shared src full read, lock structure checked'},'target':'all 815 independent SHA contents and mappings for817 files','do_not_touch':'04 v6/skills/shared state','reported_completion':False}
P.write_text(json.dumps(d,ensure_ascii=False,indent=2));print('lyric_intervals',n)
