# 第三段交付记录

- 负责人：第三人（当前用户）。
- 状态：v2脚本、界面、音效和可审阅视频已完成并实际导出；当前版画面无数值占位，尚未完成全片总剪。
- 版本：`part03-animation-v2`，2026-10-21，当前分支`codex/part-03`。衔接基准为第一段v7（`e15dec7`）与第二段v4（`ffdd1bb`）；仅修改本段目录及对应任务文件。
- 本轮排版修订：删除睡眠余额下方的小字，包括余额不足状态下原有的说明；每门课程的睡眠与头发费用改为卡片最右侧两行右对齐，字号从28增至38并加粗，课程名称和详情为右侧费用留出独立空间。
- 视频链接：随当前分支提交的[1080×2376审阅视频](previews/part03-animation-v2.mp4)与[GitHub查看地址](https://github.com/fzyvvrmy-blip/1111video/blob/codex/part-03/parts/03-midterm-ending/previews/part03-animation-v2.mp4)；该文件与已检查的原尺寸导出逐字节一致，约5MB。另有本地[原始导出](renders/part03-animation-v2/part03-draft-1080x2376.mp4)与[540×1188预览](renders/part03-animation-v2/part03-preview-540p.mp4)，均30fps、30秒、900帧。原尺寸视频为审阅版，低分辨率版本仅供预览，尚未完成全片总剪。
- 可编辑源文件：[剧情脚本v2](脚本v2.md)、[文案与数值](source/animation-v2.json)、[动画工程](scripts/render-animation.py)、[锁屏SVG](source/lockscreen-v2.svg)、[锁屏重建](scripts/render-lockscreen-v2.py)、[实际导出检查](scripts/inspect-export.py)、[第二段数据快照](source/part02-state-v4.json)、[图标及样式来源](source/ui-v2.json)。
- 启动或渲染：仓库根目录执行`python3 parts/03-midterm-ending/scripts/render-animation.py`，再执行`python3 parts/03-midterm-ending/scripts/inspect-export.py`检查实际编码。所有工程路径相对定位，完整说明见[README](README.md)。
- 首尾帧：[开始黑帧](keyframes/animation-v2/01-black-start.png)、[结尾文字](keyframes/animation-v2/08-ending.png)、[结束黑帧](keyframes/animation-v2/09-black-end.png)。[实际编码审阅图](keyframes/animation-v2/review-encoded-v2.jpg)包含通知、展开、订单、签收余额、两次失败、P/F提醒及结尾。
- 音轨：[通知轨](renders/part03-animation-v2/notifications.wav)、[操作及扣款轨](renders/part03-animation-v2/operations.wav)、[混音](renders/part03-animation-v2/preview-mix.wav)，均48kHz双声道PCM；MP4为48kHz双声道AAC。短点按音与第二段的干脆轻触风格对齐。没有人声或背景音乐，配乐交总剪。
- 锁屏：本段[10月22日版本](assets/lockscreen-v2-oct22.png)与[11月2日版本](assets/lockscreen-v2-nov02.png)，均1080×2376。按第二段v4的紫色校门布局重建，校门路径和配色来自其工程；两张图只在日期、星期、周次区域产生差异，背景、19:11、电量53%及控件像素保持一致。第二段原锁屏保存在`assets/part02-v4/lockscreen-oct22-reference.png`作对照。
- 课程与扣款：完整沿用第二段十门、31学分、18小时睡眠费用，先用后付后从6小时开始签收。前四单分别扣1、1、1、2小时，余额6→5→4→3→1；头发剧情数值200→180→150→120→80根。待签收10→9→8→7→6。第五单为大学物理B(2)，需2小时而仅剩1小时，失败不扣款；返回后从同一订单申请退课。花卉鉴赏保留2学分、早八精品。
- P/F及周次：用户明确确认P/F还有1天、10月22日为第六周；按周一开周推到11月2日为第八周。当前画面中已显示实际文字，无X、待核对或通用课程订单占位。
- 界面：封面和线条SVG图标直接复用第二段资源；使用清华紫`#660099`、高亮紫`#8600ca`、相同五项导航、29消息角标与系统三键。仅“我的课表”高亮，签收订单与选课车分开。头像复用小五同学共同素材。
- 依赖与字体：本机已有Python 3、ImageMagick、Fontconfig、PyCairo、PyGObject、librsvg、Pango/PangoCairo、FFmpeg（libx264/AAC），导出检查使用已有Pillow，未安装新依赖。前两段实际使用Microsoft YaHei；本环境缺少该字体，实际采用第二段声明的后备Noto Sans CJK SC，最终字体逐像素一致仍需统一渲染环境。
- 验证：两种尺寸的视频均完整解码通过，已核对30fps、900帧、30秒和48kHz双声道AAC；解码后的首尾帧全部RGB通道均为0。已实际查看开始、通知展开、余额、返回同一大学物理订单、退课失败、原日P/F及结尾编码帧。通知音轨峰值约0.247、操作及混音约0.323，均未削波。[检查记录](keyframes/animation-v2/export-check.json)保留元数据、抽帧位置与逐单余额。
- 分支与公共文件：未合并、改写或推送其他分支，未改`main`、`shared/`、公共规范或`assets/handoff/`。旧版共同锁屏、原始生成图、v1配置/关键帧/视频保留；当前动画改用本段v2素材，旧配置占位不属于本版。
- 待完成：独立音轨的团队共享地址；三段正式采用的锁屏、字体和整体剪辑。三段独立时长合计约76.1秒，本段暂保留30秒供剪辑。所有费用已按第二段当前草案落入画面，第二段将来改数值时需重新同步；头发数值为本段补充剧情设定。
