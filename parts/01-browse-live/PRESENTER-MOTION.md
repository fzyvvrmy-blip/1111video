# 老板动态与口型制作

## v6声音修订（当前使用）

用户要求热情的中年男销售、大卖场“号外号外”的声音。人物外形继续采用三十岁左右的两张v4参考图。新一轮生成移除了旧康康音频，原生生成新男声和同步说话表演；完整指令与任务记录见assets/bookseller-motion-v2-job.json，原片为previews/bookseller-motion-v2.mp4。

新台词：“号外号外！双十一学分大甩卖！花卉鉴赏，两学分，早八精品！看一看，挑一挑！三、二、一，上链接！”要求厚实的胸腔共鸣、中低男声、略带颗粒感、带笑意的有力吆喝。语音识别核对到一遍完整台词，实际声线观感与逐字口型仍需用户试听观看。

使用源片0–15秒，原速从全局6.3秒播放，20.05秒出现课程卡，21.3秒结束。图像与声音共用裁切起点，滤波放宽为80–7000Hz保留男声低频，不变调。旧素材与下方v5制作记录保留作对照。

用户明确要求：三十岁左右的老板必须连续活动并对上台词口型。v4只完成界面动效和人物外形参考，不满足这一要求，不能作为人物视频成品。

## 已有输入

- 身份、服装、集市和喇叭参考：assets/bookseller-megaphone-v4.png。
- 举书姿态与教材参考：assets/bookseller-book-v4.png。同一人物，不能在中途换脸。
- 干声：audio/bookseller-lipsync-driver-v1.wav，48kHz、单声道、16bit，约9.255秒。来自已有Windows康康临时配音；未加喇叭滤波、未再压缩时长。它是首轮口型试做输入，尚不是已确认的正式声音。
- 台词：花卉鉴赏！两学分！早八精品，美育好课！看一看，挑一挑！三，二，一，上链接！

## 连续表演

老板站在原来的集市书摊后，面对直播镜头，用喇叭热情招呼顾客。表情、眨眼、头部和肩膀自然连贯，嘴巴跟随输入干声实际发音开合。喇叭放在嘴边偏下，嘴部始终清楚可见。招呼声中，空出的手从摊面拿起花卉鉴赏教材，举到胸前，向镜头展示封面；书不挡脸，手指和封面稳定。倒数时稍稍前倾，最后一句说完，手势朝画面下方示意，课程卡随着“上链接”出现。之后保持自然呼吸和轻微动作，留出交接余量。镜头保持固定，不添加UI、字幕、手机边框、配乐或新人物。

先检查服务能否把自定义照片、中文干声和动作提示一起使用；若只有讲话功能，不能把结果称为已实现拿书动作。动作与口型的生成质量须实际检查，不能保证一次生成成功。

可用的动作提示：

> Use the supplied reference as the identity, outfit, market stall and prop reference. The same Chinese male bookseller, around 30 years old, speaks enthusiastically to a live camera, with accurate Mandarin lip sync driven by the supplied audio. Keep his mouth visible, with the megaphone held slightly below and beside it. Natural blinking, subtle head and upper-body motion. With his free hand, pick up the flower appreciation book from the stall and show its cover at chest height without covering his face. During the final countdown, lean forward slightly and gesture downward on the last phrase. Preserve facial identity, the apron, market background and book design. Fixed camera, continuous performance. No captions, UI, music or scene cuts. Do not generate additional speech.

## 接回手机界面

小窗与全屏必须使用同一条人物视频、同一个播放时刻；点击弹满不重播、不冻结人物。语音在小窗开始后自然进入，展开后接着说。用实际音轨定位倒数和“上链接”的位置，再调整课程卡出现时间，不靠变速强塞进原7.5秒。喇叭滤波在口型生成之后处理，保留时长；若换正式声音，应重新生成或同步口型。

人物原片已保存为previews/bookseller-motion-v1.mp4；render.mjs和presenter-video.mjs负责连续视频及同源语音合成。原片、输入干声、指令和合成预览均保存在工程内。

## v5历史记录

插件连接未成功；改走用户已登录的HeyGen网页。用户开启Chrome文件读取权限后，已上传参考图和干声并生成15秒人物片段，使用一次已有免费机会。完整输入、任务链接和指令见assets/bookseller-motion-v1-job.json。

原片包含连续说话和举书动作，后半段重复了一遍末尾台词。v5只使用源片0–10.2秒，保留第一遍完整内容；小窗从6.3秒进入，16.5秒结束，课程卡从14.6秒出现。口型细节与最终声音仍需观看反馈。

功能依据：https://help.heygen.com/en/articles/10034438-how-to-get-started-with-photo-avatars
