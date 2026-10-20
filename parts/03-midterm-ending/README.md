# 第三段 · 期中签收与结尾

已完成共同壁纸、无通知的10月22日锁屏，以及一版30秒的第三段动画初稿。初稿已实际渲染为带音效的MP4；费用、余额、P/F天数、周次及部分订单内容仍有占位，尚不作为最终交付。

## 文件

| 文件 | 用途 |
| --- | --- |
| `../../assets/handoff/lockscreen-wallpaper.png` | 1080×2376，不含UI的共同壁纸 |
| `../../assets/handoff/lockscreen-oct22.png` | 1080×2376，19:11、10月22日星期四，无通知 |
| `source/lockscreen-oct22.svg` | 可编辑锁屏源文件，时间、日期、状态栏、底部控件为独立组 |
| `assets/wallpaper-generated-v1.png` | 内置 image_gen 生成的原始壁纸，846×1860，未覆盖 |
| `source/wallpaper-prompt.md` | 完整生成提示词和素材处理记录 |
| `scripts/render-lockscreen.py` | 本地重建两张交接PNG，不调用生成API |
| `source/animation-v1.json` | 动画初稿的文案、占位字段、订单内容及输出参数 |
| `scripts/render-animation.py` | 可编辑动画工程，含布局、运动、转场、声音合成和视频输出 |
| `keyframes/animation-v1/` | 已实际生成的关键静帧，包含11月2日锁屏初稿及视频首尾黑帧 |

## 重新渲染

在仓库根目录执行：

```bash
python3 parts/03-midterm-ending/scripts/render-lockscreen.py
```

脚本按自身位置定位文件，源文件只使用相对路径。会重建上述两张交接PNG，不修改原始生成图。

本次环境使用已有的 Python 3、ImageMagick 6（`convert`）、Fontconfig（`fc-match`）、PyGObject、PyCairo 和 librsvg 2.52。没有安装新依赖。系统依赖缺失时，可用支持SVG及中文字体的图形编辑器打开SVG，再以1080×2376导出。

时间及状态栏使用 DejaVu Sans；日期、解锁提示使用 Noto Sans CJK SC。本次锁屏采用这两套字体，全片字体仍待三人统一；调整字体后须重新检查文字位置。

## 动画初稿与重新渲染

初稿从黑屏中的通知声开始，原壁纸亮起并显示11月2日。通知逐条进入、把先前通知向下推，顶部卡片轻压后展开为我的课程中的待签收订单。连续签收时卡片变灰、列表上移，扣款音和提示衔接起来；余额不足后从同一订单申请退课，出现失败弹窗。画面熄灭后回到原来的10月22日锁屏，只落下一张P/F提醒，最后淡去并显出结尾文字。未增加人物内心字幕。

在仓库根目录执行：

```bash
# 输出1080×2376、30fps初稿，再生成540×1188、30fps预览
python3 parts/03-midterm-ending/scripts/render-animation.py

# 只输出小尺寸节奏预览
python3 parts/03-midterm-ending/scripts/render-animation.py --preview

# 只检查版式，不编码视频
python3 parts/03-midterm-ending/scripts/render-animation.py --stills-only
```

渲染前需已有上述两张共同PNG，缺失时先运行静帧脚本。新增动画所用依赖为本机已有的 Pango/PangoCairo、ffmpeg（libx264、AAC）；继续使用 Cairo/PyGObject 和 ImageMagick，没有新增安装依赖，也不依赖视频生成服务或配音服务。

修改 `source/animation-v1.json` 可以调整文案、日期、P/F占位和订单内容。页面布局、缓动、片长内的动作安排在 `scripts/render-animation.py` 中。静态壁纸与日期、通知、列表、弹窗相互独立，方便继续编辑。

本次实际输出（均为本地文件，非团队共享链接）：

- [原尺寸动画初稿](renders/part03-animation-draft-v1/part03-draft-1080x2376.mp4)：1080×2376、30fps、30秒，900帧，H.264 + AAC。
- [小尺寸预览](renders/part03-animation-draft-v1/part03-preview-540p.mp4)：540×1188、30fps、30秒。仅作预览。
- [通知音轨](renders/part03-animation-draft-v1/notifications.wav)：48kHz、单声道PCM，普通提示音与集中通知；由脚本原创合成。
- [操作与扣款音轨](renders/part03-animation-draft-v1/operations.wav)：48kHz、单声道PCM，轻触、签收扣款与失败提示；由脚本原创合成。
- [预览混音](renders/part03-animation-draft-v1/preview-mix.wav)：以上两轨合成，不含背景音乐或人声。

`renders/`按仓库规则被Git忽略；源文件和关键帧保留，运行脚本可重建视频及音轨。团队交接时仍需把视频和音轨上传到团队约定位置，再在DELIVERY中登记实际可访问链接。

## 初稿占位与已核对项

- 已核对导出为1080×2376、30fps、30秒；并从编码后的MP4抽帧查看开头、通知展开、订单滚动、余额不足、退课失败、回原日和结尾。通知进入待签收订单，底部只高亮我的课表。
- 沿用壁纸v1、19:11、小五头像和53%电量；日期按11月2日→10月22日切换。11月2日画面明确保留“第八周【待核对】”。
- 费用和余额均保留【X】，余额条收缩仅示意耗尽；实际逐单扣款数字和余额计算尚待接入第二人的费用表。没有向共享状态写入未经确认的数字。
- 四类明确任务使用大纲内容。其余两条通用课程订单在配置中标为 `placeholder: true`，待替换为确认内容；六件通知是本次动画示例，不代表十门课的订单清单已经确定。
- P/F剩余天数为【X】。三十秒为本次初稿节奏，后续与前两段合片时可调整，无平均分段时长要求。
- 两条音轨均为实际生成的声音，样本检查无削波；音色、音量和整体节奏仍可随画面修改。背景音乐留给总剪统一加入。

## 与第二、三段的接口

- 第二段支付后使用 `lockscreen-oct22.png`，随后熄屏至完全黑屏。
- 第三段从该黑屏中的通知声开始；11月2日复用同一张壁纸和时钟坐标，修改日期层并加入通知卡。11月2日锁屏初稿已导出到 `keyframes/animation-v1/lockscreen-nov02-draft.png`，周次未确认，暂不登记为已定稿的共同交接图。
- 时钟基线 `(540, 432)`，日期基线 `(540, 522)`；SVG坐标和导出像素一一对应。通知卡建议从 `y=650` 开始，横向边距沿用统一规范。
- 第三段结尾回到同一张10月22日锁屏，再叠加一张P/F提醒；共同静帧保持无通知。
- 静帧无帧率；动画初稿已按共同规范输出30fps。PNG与MP4分别登记，不将静帧当作视频成品。

## 共享文件变更与后续PR说明

本次新增 `assets/handoff/lockscreen-wallpaper.png` 和 `assets/handoff/lockscreen-oct22.png`，未改动原有参考图或公共规范。影响《协作与交接规范》的“第二段与第三段”：第二段的支付后锁屏、第三段的11月2日亮屏及最终回到原日，应共同使用壁纸v1。

这两张图是首个可用版本；合并评审时需要第二人同步使用，后续替换须说明版本。P/F剩余天数【X】、第八周、费用和余额口径继续保留待确认，不写入当前静帧。
