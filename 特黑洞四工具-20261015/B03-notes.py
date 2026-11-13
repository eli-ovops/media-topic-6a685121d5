# coding: utf-8
from 记录已读 import record
from pathlib import Path
import json
notes={
'lemo-opuscar/references/library/styles/dark-keynote/STYLE.md':'近黑三层面板和单accent；积累乱UI→沿弧线归类/吸附网格；源UI扩成转场、光扫只显扫过像素；2.5D近物模糊、条带投影重alpha会接缝；24fps/无淡出/每击声非本项目硬约束。',
'lemo-opuscar/references/library/styles/living-screencast/STYLE.md':'高分辨率重绘UI与低分辨率像素演员分两层；DOM每帧测量top-edge锚点，跟随光标推近/两窗甩镜；是重绘非真实录屏，不能作为实测证据；blur挂未变换wrapper。',
'lemo-opuscar/references/library/styles/swiss-motion/STYLE.md':'12列/24基线、单信号色与一个脱网格例外；clip reveal/knife cut/reflow按距离先后；.7,0,.2,1精确曲线无弹簧；旋转后停再标签，拼条overdraw1px消缝。',
'lemo-opuscar/references/library/styles/dataviz/STYLE.md':'一标记一事实，数据空间固定注解+memory zone防缩放碰撞；数值色阶不夸大；轴随单位出现、标记编码morph而非换页；相机同纸面；音高映射数值非装饰。',
'pdoom-video/references/library/src/core.js':'setup等待字体；renderAt(t)每次重置文字/相机/字幕状态并randomSeed(1000+floor(t*12))；toScreen统一镜头位置；irisShape向外扇形遮罩；flushLetters先强制brush合成再叠字，避免后景盖字。'}
record(notes,'B03')
(Path(__file__).parent/'B03逐文件笔记.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2))
ss=[
'一句话推理公司发布片，缺镜头细节；不把1分钟2美元作预算。',
'先评多版网站再汇预告，适合展示设计迭代，不把初版当定稿。',
'明确HyperFrames路线，可作发布片入口；未给对象运动细节。',
'AE可继续编辑工程比仅MP4多一层交付，Higgsfield调用需另授权。',
'先旁白再AE配画声，适合音频驱动分镜；未证全自动。',
'脚本/图/旁白/音乐跨工具汇总，应保留每项来源与许可。',
'输入产品到宣传片封装Skill可复用输入契约，效果未核。',
'先分镜再Remotion、单镜头返修减少整片重跑。',
'同品牌资产对比20秒AE卡点，不足以证明模型优劣。',
'五场客户问题到服务与证据，适合简短企业解释。',
'15秒作品集仅自由委托，Max不可当必要条件。',
'单形体UI循环与多子帧模糊，关键是首尾状态含光标速度。',
'交互镜头实验可解释焦段等参数；一次成型/费用仅作者声明。',
'Manim论文图解配本地TTS，需先确定图能说明的论点。',
'Remotion三分钟历史以SVG/Canvas配声，7400行非质量指标。',
'线稿历史一句话prompt，先核事实与范围。',
'线稿TTS双语字幕用于地理过程，近五分钟非推荐本期时长。',
'把地理模板换物理题体现结构复用，题解准确需独立验算。',
'空杯逐项添加到成品，步骤计数与测量同步。',
'Canvas相对论1395帧只是作者元数据，未看帧不能评价解释正确。',
'WebGL地形+Kokoro叙事战役，史实核查独立。',
'口播原声字幕保留，语义线稿跟随，不从30镜头推流畅。',
'JS解释Transformer只有主题，缺具体视觉机制，待后续原片才可评。',
'多尺度房间到夸克连续推镜，用尺度关联替代换页。',
'JS逐帧手绘叙事仅技术标签，具体角色动作UNKNOWN。',
'整数像素巫师四段施法状态机保持轮廓和有限色。',
'火星短片只知代码渲染，具体镜头机制UNKNOWN。',
'自传叙事配逐帧笔触，模型自述不能作为模型真实经历。',
'难题主题仅代码动画标签，故事推进UNKNOWN。',
'单HTML+HyperFrames、逐秒复检可借验收步骤。',
'角色截图+本地音频采样混合，需要分别核素材权。',
'雨滴叙事可作单主体旅程候选，但元数据未给画面细节。',
'水墨动画题材导航，具体水墨引擎与运镜UNKNOWN。',
'30秒2D分镜预览是规划产物，不等于最终动态片。',
'轨道世界纯JS仅实现路线，轨道曲线未知。',
'鱼草粒子齿轮大数量强调场景，性能及可读性不能据数量推断。',
'草图到物理模拟可解释结构受力，未核物理结果。',
'日文长规格像素跑酷本地无全文，不能代称提示词已完整读。',
'海岸画代码动效具体潮汐/笔触未知，后续需媒体核读。',
'旅行照片转丙烯画风需保留真实输入来源和输出样片。',
'Blender建模/剖面适合结构解释，当前不授权新工具运行。',
'10秒程序镜头加搭建延时分成成片与过程，token/费用不是保证。',
'Three岛屿交互按骨骼IK/路径/透明水写明确验收。',
'PDoom手绘纯时间九章、角色跨章回归，歌曲权另核。',
'LetMeGo由歌词音频到p5，人工反馈改角色证明仍有迭代。',
'角色图→视频底片→JS重绘是混合生成，非全代码零外部依赖。',
'Suno编曲演唱与Opus歌词画面是分工链，音乐许可需查。',
'歌词本身作主体竖屏适合文字节奏，具体排版未知。',
'Runway MCP纪录片调用外部生成，不属于纯代码绘制。',
'13素材挑段剪调色字幕，属剪辑不是从零生成。',
'46亿年案例只知代码动画，史实与画面未知。',
'群论案例只知代码动画，数学论证和对象动作未知。',
'原子弹主题只知标题和代码标签，不能推断具体镜头。',
'一句话MV只知主题入口，歌词/配乐/制作范围未知。']
cases=json.loads(Path('/Volumes/EXTERNAL/自媒体/.agents/skills/opus-video-prompts/references/library/cases.json').read_text())
assert len(cases)==len(ss)==54
for c,s in zip(cases,ss):c.update(reading_note=s,media_viewed=False)
(Path(__file__).parent/'B01案例逐项笔记.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2))
