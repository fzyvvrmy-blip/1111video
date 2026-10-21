# 老板动态与口型制作

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

输出保留原始人物视频、干声、处理后音轨以及手机界面合成预览。人物生成视频还未得到，尚未接入render.mjs；本文件不是已完成的视频。

## 当前阻塞

已查到可安装的HeyGen人物视频插件，但当前没有安装并连接，也没有可调用的视频/口型模型。待连接后检查其实际接口，先生成一段动作与中文口型测试，再合成整段。不要把静态图切换或画面缩放当作人物动画。

功能依据：https://help.heygen.com/en/articles/10034438-how-to-get-started-with-photo-avatars
