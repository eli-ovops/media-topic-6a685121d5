# FredTalk 2.0 全局安装与Codex接入

2026-10-14，用户明确授权。源码完整下载到 `/Users/USER/.codex/skill-repos/FredTalk`，7项Skill以全局链接注册，保留仓库结构使脚本能定位组件库。上游commit与各入口见安装核验.json。本地适配在仓库 CODEX-ELI-ADAPTER.md，各Skill入口已引用；Git保留未修改的上游原件。

已实测：全局Skill可读、脚本沿真实路径定位仓库、价格组件检索得到22项/返回3项，含价格落定/参数落定/套餐对比。未实测：完整视频渲染、音频粗剪、云渲染。未安装Node/Python依赖、未下载Release素材包、未启用云端。新Skills已被Codex可用目录识别。

首选流程：录音/字幕粗剪→逐句组件候选比较→真实内容关键帧→短动画和接缝→整片画面与声音审看。frame-smith补充圆润自然的运动设计，不改变冻结事实和用户批准门禁。作者品牌、配音、音乐、账号和横屏4K默认不移植到Eli。

Node22.16.0已有；默认Python3.9.6低于官方3.11要求，虽然当前检索通过，完整工具链尚待选用既有兼容运行环境验证。系统盘核到余约4.1GiB/98%；仓库427MiB，其中components276MiB/library85MiB/.git59MiB/skills4.1MiB，均为本次安装来源、组件或追溯用途，未清理。检索原件已从/tmp/fredtalk-catalog-check.json保存本目录。

版权：上游原创Skill/模板/代码MIT，第三方素材保持独立许可，查看仓库THIRD_PARTY_NOTICES及docs/license-scope.md。许可不是当前素材已全面验收。

指定FredTalk视频 https://v.douyin.com/T3DZlx_5f_4/ 已派原01，完成主动向PMO报告，不轮询。视频全文分析尚未验收，仓库说明不替代视频实读。千问Go04样片/05暂停条件保持。
