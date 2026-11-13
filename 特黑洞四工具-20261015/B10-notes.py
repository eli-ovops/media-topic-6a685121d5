# coding: utf-8
from pathlib import Path
import json
from 记录已读 import record
ss={
'brick-toy':'宏观真实桌面/刚性ABS积木、弧线飞入按格吸附，角色12fps相机24；坍塌预模拟确定性，积木不squash；中性HDRI/软箱/AO/2x抗闪；可借拆解重建同零件，不复用商标人偶。',
'cel-anime-80s':'四层绘景/平色cel/自发光/录像CRT；色与emissive同移、角色剪影遮发光防穿透；角色12/8fps而机光雨24；held pose让光带变化，循环板制造速度；不把CRT噪点套清晰UI。',
'crayon-book':'压力alpha与页坐标纸齿控制蜡附着、颜料抵抗蜡显隐藏白字；描线→逐排涂色就是动作，12fpsboil与相机24分离；wash先角色后防淹没，纹理不屏幕固定。',
'engraving':'版刻以线密度成调，笔触中粗两端尖、三遍排线/交叉/暗部；放大roundel从主体飞往页边保leader，镜像铜版揭纸为正像；后上透明色，不把灰fill冒刻线。',
'game-show':'每轮一个可重复动词+判定，画声同beat事件表；豆形演员颜色身份不变，硬投影/粗描边无柔影；回顾缩成底部槽，cue回答加速；机器纯t，不套全片硬拍弹跳。',
'glass-product':'黑场条形灯而非杂HDRI，PMREM随帧重烘并dispose，玻璃透射内部需opaque；雾面变清/局部explode沿轴约40度可读；镜面先更新世界矩阵防上一帧，光guide发事件，未装工程不称复现。',
'halftone-dossier':'纸/点密度叠印/证据编号/章印一体，网点只尺寸表明深浅；点wipe最大半径覆盖网格对角防漏切，boil仅角色非文字/HUD；font先load、clipID全局唯一；案例卡若机械换页仍PPT，慎用。',
'hd-2d':'低分辨率精灵置真实3D像素贴图景，实灯投影/远小人物/移轴焦带；精灵踏帧但机灯60fps，灯level共驱发光和强度，焦带并入signedCoC不另blur；亮sprite需前fill，beam卡避免NaN污染。',
'hologram-hud':'暗底线框scan→锁部件→壳沿轴explode内件不动→leader/数值滚定→chip侧轨累计；滚值锁定才accent，文字独立暗plate；下镜whip须前段就开始，三层深度但HUD保持锐；scan视觉不等真实数据证据。'}
notes={'lemo-opuscar/references/library/styles/'+k+'/STYLE.md':v for k,v in ss.items()}
record(notes,'B10')
(Path(__file__).parent/'B10逐风格笔记.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2))
