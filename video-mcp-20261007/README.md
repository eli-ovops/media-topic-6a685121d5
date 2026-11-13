# 自媒体本地视频读取入口

本地 MCP 实测通过；CLI可直接使用；项目配置已写入但本机CLI列表未加载它，原PMO实际CLI调用并查看6张画面的试用已通过；MCP自动加载仍未验证。未更改项目trust。

## 使用
最直接的方式：
```bash
/Users/USER/.local/nodejs/node-v22.16.0-darwin-arm64/bin/node /Volumes/EXTERNAL/自媒体/工具验证/video-mcp-20261007/read-video.mjs
```
默认分析当前批准原片。末尾传入明确原片路径和`info`可只核元数据。原始CLI回执写入evidence/cli-analyze-时间戳-PID.json，命令输出仅文字及图片路径，不打印图片base64；原PMO须用图片读取工具实际查看返回路径，并区分已看图数量和处理数量。
无需改变全局配置、信任设置或重启。CLI内部通过标准stdio连接已验收的MCP；无需旧会话已加载该工具。

本项目 `.codex/config.toml` 定义 `local_video_reader`。配置文件存在不代表旧会话已加载；平台加载后先检查工具是否实际出现。不为加载打断其他任务或重启整个应用。
先用 `video_info`，再 `video_analyze`（detail=detailed、max_frames=30、mode=interval、language=zh、skip_ocr=true）。动作细节用 `video_get_frame_burst`。只允许 `allowed-files.json` 中精确原片路径；用户指定新素材后才能增加。URL来源禁用，不写原媒体旁文件。

## 限制
画面是采样图，名义时间来自网格计算，不是逐帧精确定位；本轮30帧，默认内联6张，其余24张仅路径，实际查看后才能称已读。音频是整条音轨的ASR文字，不是模型直接听音；不能凭文字判断语气和情绪。ASR存在错词。本次试拍启动器设置GitHub/高性价比人生指南词表，仅用于这个已批准样本；换选题时要调整词表，不能把词表当音频证据。越界或无效ASR时间戳会被拒绝，全文保留并警告，不发明时间点。OCR本次禁用。
修复版缓存使用文件SHA-256，同路径内容变化会自动生成新音频/画面；已用同路径、同大小、同mtime而内容不同的样本回归验证。

## 证据与维护
见验收报告.md、evidence/acceptance.json、video_analyze.json、video_get_frame_burst.json、boundary-checks.json、typecheck.log。
固定上游commit：01e8a7dc5ffa3abf96b32d7aa56809a6e99d5ca5；whisper.cpp v1.9.5 / d1be6fde11ac6e0407606b4e42fe72d34add8037，许可随源码保留。
隔离修改：媒体精确白名单、禁用远程来源/云ASR/同目录字幕猜测、指定本机二进制及禁用OCR工具。launch.mjs仅启动读取服务，不暴露setup/install/sort入口。bin/avprobe是AVFoundation自编适配器，并非ffprobe官方实现。
项目撤销可将本项目server配置enabled=false；不删除原片、证据、模型和源码，不覆盖全局配置。
