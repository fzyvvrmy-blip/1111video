# 第三段：期中签收与结尾

当前版本为 `part03-animation-v2`，30秒，1080×2376、30fps，带通知、点按、扣款与失败音效。按第一段v7和第二段v4调整，十门课程、31学分、18小时睡眠费用与第二段一致。当前画面中的占位已补齐；P/F还有1天，10月22日第六周、11月2日第八周。自然连贯的剧情说明见[脚本v2](脚本v2.md)。

## 可编辑文件

| 文件 | 用途 |
| --- | --- |
| `source/animation-v2.json` | 当前文案、十门订单、睡眠/头发费用、日期、周次和视频参数 |
| `source/part02-state-v4.json` | 第二段`ffdd1bb`的只读数据快照，供课程及费用核对 |
| `source/ui-v2.json` | 第二段的调色板、原始SVG图标路径、字体声明和来源 |
| `source/lockscreen-v2.svg` | 紫色校门锁屏，可编辑壁纸、日期、时钟、周次及底部控件 |
| `scripts/render-lockscreen-v2.py` | 从SVG与当前配置重建两张本段锁屏PNG |
| `scripts/render-animation.py` | 页面、动效、自动计算余额、音效与MP4编码 |
| `scripts/inspect-export.py` | 实际MP4解码检查、黑帧/音轨核对与编码后审阅图 |
| `assets/part02-v4/` | 从第二段独立HTML提取的十门封面及锁屏对照图 |
| `keyframes/animation-v2/` | 当前关键帧；`review-encoded-v2.jpg`来自实际编码后的视频 |

课程费用、余额与角标通过同一份数据计算。睡眠余额6→5→4→3→1小时，头发余额200→180→150→120→80根，待签收10→9→8→7→6。第五次大学物理签收需2小时，失败时不扣款；返回后从同一订单申请退课。渲染前会检查与第二段快照一致、十门总费用正确、余额不为负、失败原因成立，以及日期和周次的推导。

当前排版已删掉睡眠余额下方的小字。课程卡片最右侧用两行38像素加粗文字分别显示睡眠、头发费用，两行右对齐；课程名称与详情保留在左侧，和右侧费用分开。

## 运行与渲染

在仓库根目录执行；脚本按自身位置定位素材，不依赖当前工作目录。

```bash
# 只重建本段的两张锁屏，不写公共handoff目录
python3 parts/03-midterm-ending/scripts/render-lockscreen-v2.py

# 导出1080×2376、30fps视频，同时生成540×1188预览
python3 parts/03-midterm-ending/scripts/render-animation.py

# 只导出540×1188预览
python3 parts/03-midterm-ending/scripts/render-animation.py --preview

# 只检查版式，不编码视频
python3 parts/03-midterm-ending/scripts/render-animation.py --stills-only

# 重新渲染后检查两种尺寸的实际视频，导出审阅图及检查记录
python3 parts/03-midterm-ending/scripts/inspect-export.py
```

沿用原有Python 3、ImageMagick、Fontconfig、PyCairo、PyGObject、librsvg、Pango/PangoCairo及FFmpeg（libx264/AAC）；导出检查使用环境已有的Pillow。未安装新依赖，不需要网络或生成平台登录。头像由仓库共同参考图读取，其余新版素材都在本段目录。

前两段实际使用Microsoft YaHei；本环境缺少该字体，采用第二段声明的后备字体Noto Sans CJK SC，当前锁屏与页面均使用它。字号、颜色、线条图标、导航位置与第二段对齐；字体逐像素一致仍取决于三段是否在同一字体环境渲染。

## 实际输出

- [随分支提交的原尺寸审阅视频](previews/part03-animation-v2.mp4)：与下方已检查的1080×2376导出逐字节一致，约5MB，供GitHub审阅。
- [1080×2376视频](renders/part03-animation-v2/part03-draft-1080x2376.mp4)：30fps、30秒、900帧，H.264/AAC。
- [540×1188预览](renders/part03-animation-v2/part03-preview-540p.mp4)：30fps，仅供预览。
- [通知轨](renders/part03-animation-v2/notifications.wav)、[操作及扣款轨](renders/part03-animation-v2/operations.wav)、[混音](renders/part03-animation-v2/preview-mix.wav)：48kHz双声道PCM，无人声与配乐；视频使用AAC。
- [逐单余额记录](renders/part03-animation-v2/receipt-ledger.json)、[编码检查](renders/part03-animation-v2/qa.json)。

视频和音轨渲染目录`renders/`仍被Git忽略。本次按用户要求推送一版，在本段`previews/`中保留一份约5MB的原尺寸审阅视频，并通过本段`.gitignore`仅放行这个文件；源文件、必要素材和关键帧一并提交。独立音轨可由命令重建，团队共享音轨地址尚未登记。

## 衔接与范围

本版改用第二段v4的紫色校门风格，11月2日和回到10月22日的背景、时钟、电量、控件完全相同，仅日期、星期和周次变化。P/F提醒只出现一次，位于10月22日第六周的锁屏上。第一段主推的大学物理B(2)、4学分在本段对应失败签收订单，封面与第二段一致。

只修改`codex/part-03`里的本段目录和对应`tasks/03-期中与结尾.md`。未合并其他分支，未覆盖`shared/`、公共规范或`assets/handoff/`。第二段原工程不受影响；正式合片时需统一采用的锁屏版本、实际字体与整体时长。三段目前独立时长相加约76.1秒，仍需总剪调整。

v1的原始生成壁纸、SVG、配置、关键帧与已渲染视频保留，属于历史初稿；其中的旧占位不是当前版本。`scripts/render-lockscreen.py`仍只负责旧版共同静帧，当前动画不调用它。
