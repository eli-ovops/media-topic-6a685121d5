# coding: utf-8
from pathlib import Path
from 记录已读 import record
import json
ss=[
'小队飞船拆目标组件并应对炮塔波次，玩法委托不是镜头；IP不可直接复用。',
'猫爪击实际发声音符，单时间线驱动画声；Canvas蜡笔纹理、可按t跳转。',
'仅说similar crypto，缺被参照版本；不能推导具体效果。',
'AIsa15秒动态图形自由委托，缺场景对象和事实输入。',
'蝴蝶逐帧纯函数与首末像素比较，六项机器门禁仍需人看；1820帧是作者声称。',
'未公开全文，仅文章省流解说原帖，视觉机制未知。',
'原帖说Opus+Remotion做CLIProxyAPI流程，SVG标签是remake栈，不能混作原作者实际栈。',
'解释celld为何值得用，一句主题缺输入素材与动作。',
'提示条→按钮→环→预览→toast闭环，同圆角形体多属性弹簧；输入打字按时间，文字独立遮罩。',
'金融像素关卡把消费/通胀/耐心具象化；原帖非完整prompt，不作投资建议。',
'原帖仅Remotion/Opus两词，无可复现方法。',
'Tron游戏仅题材一句，需原创视觉/玩法，非已授权IP。',
'星球海平面与太阳驱动大陆/夜灯；参数可交互，原帖未公开实现prompt。',
'涡扇沿气流逐阶段解释，再explode分离；压缩倍数/温度属待核科学说法。',
'PayBox logo10秒参考片委托，reference未安装，不能还原具体动作。',
'同PayBox词句另一原帖，语义重复但文件SHA不同，分别读并保留来源映射。',
'真实街景上叠像素爆炸/塔与地表坑，需原环境图授权，单HTML不等于无外部素材。',
'parts→geometry→rig→skin→named hierarchy宣称的建模链；只原帖、未取得完整prompt或工程。',
'编辑器里的驼鹿10秒故事，单HTML；无具体情节与相机。',
'30秒广告致敬1984并禁角标边框，仅方向不是可复制镜头。',
'10秒模型自我作品集，禁四角字框可减模板感，但无语义结构。',
'URL产品1分钟教育片+合成旁白，产品事实和TTS接口需另核。',
'5页平面图重建、15尺寸冲突先标出、层级家具；原帖测试数量与2天非本地证据。',
'手绘输入图+已有视频语法参考、声画匹配；不可照抄video-examples片。',
'漫画描成SVG矢量、活字实时改风格，须核漫画权利与多风格稳定性。',
'虚构惊悚剧20秒片头只给奖项质量形容，缺故事对象不能当具体方案。',
'火箭水压/点火/塔退/追踪/海滩9机位，时钟与max-q仪表作直播叙事；未经物理验证。',
'桌面→散热器拆开→芯片→晶体管→原子连续推，旁尺交代尺度；原帖非完整prompt。',
'机械眼72甲片+9叶虹膜，kick开甲/低音推镜/高频亮核心，音频不同频段驱动不同部件。',
'手机→光纤→机房→8GPU→晶体管→答复的来回路，需避免把固定8GPU当所有服务事实。',
'前12秒静默造音乐机、球落触发每块发声，最后聚成标题；静默与因果同源，非全片强制配乐。',
'20秒超智人人宣言，全画声代码只是制作范围，未给动作机制。',
'一人画路一人擦除的像素冲突，有跳/潜墨/吸攻击，完整prompt在外部评论未读。',
'白空间：效率方块封窗→静默→移除一块→彩光连锁恢复；英文源码提示末尾截在slo，缺失不补编。',
'日文余白同主题，要求窗图/光柱/地投影用同一图案并精确反映遮挡，30fps离线逐帧。',
'波斯文原帖说数据中心入服务器/GPU/芯片/电路/晶体管到硅原子，1小时仅作者说。',
'从代码库做1分钟产品promo，先取得真实能力/素材，未指定镜头。',
'15秒128BPM8小节，每小节1.875秒且画声代码，节拍计算一致不等于效果验收。',
'15秒履历showreel自由委托，缺具体结构，不推导高级效果。',
'心脏四腔四瓣血管传导、同步搏动和explode重组/hover标签，医学与蓝红氧合示意要核。']
pp=sorted(Path('/Volumes/EXTERNAL/自媒体/.agents/skills/awesome-opus5-5-videos/references/library/prompts').glob('*.md'))[:40]
assert len(pp)==len(ss)
notes={str(p).split('/.agents/skills/')[1]:s for p,s in zip(pp,ss)}
notes.update({
'awesome-opus5-5-videos/SOURCE.json':'固定92aee2f586ac0715cb3cbcb6384834f98a33383d，local adapter/runtime=false。',
'awesome-opus5-5-videos/references/library/LICENSE':'MIT保留版权/许可与无担保；独立作者视频及prompt权利仍由作者保留。',
'awesome-opus5-5-videos/references/library/.gitignore':'仅.DS_Store忽略条目。'})
record(notes,'B04')
(Path(__file__).parent/'B04逐案例笔记.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2))
