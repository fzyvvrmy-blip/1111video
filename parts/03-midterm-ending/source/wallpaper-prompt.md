# 共同壁纸生成记录 · v1

- 方式：内置 `image_gen`，未使用CLI/API fallback。
- 生成日期：2026-10-20。
- 原始输出：`../assets/wallpaper-generated-v1.png`，846×1860。
- 交接输出：`../../../assets/handoff/lockscreen-wallpaper.png`，1080×2376。
- 适配方式：ImageMagick等比覆盖后居中裁切至目标画幅；未拉伸主体。原图宽高比与目标非常接近。
- 锁屏UI：使用独立SVG图层编写并由librsvg渲染，时间日期不由图像模型生成，便于精确修改与复用。

## 完整提示词

```text
Use case: stylized-concept
Asset type: shared smartphone lock-screen wallpaper for a Chinese university short film, portrait 1080×2376 (aspect ratio 5:11).
Primary request: create a polished, serene, minimal abstract purple phone wallpaper, completely without interface or typography.
Scene/backdrop: a very pale cool lavender background at the top and through the middle; softly lit translucent satin-like curved surfaces emerge from the lower third, sweep gently upward toward the lower right, and fade into deeper Tsinghua purple #660099 at the bottom. Only a few broad, graceful shapes, restrained depth, fine smooth gradients, crisp clean finish.
Composition: full-bleed flat digital wallpaper, extremely tall portrait format 5:11. Upper 28% must be almost uniform very light lavender for a large dark clock and date. Middle 30–72% must stay quiet and low-contrast to allow stacked notification cards to be overlaid later. Concentrate the sculptural folds near the bottom edges, no busy details. The same image must look calm at the beginning and anxious beneath course notifications later.
Color palette: pale lavender #F4EEFC, soft lilac, muted violet, and rich #660099 accents; follow the project's pale-purple and white phone interface.
Lighting/mood: soft diffused light, gentle dimensional shading, refined contemporary phone wallpaper, peaceful rather than flashy.
Constraints: wallpaper only; no text, no clock, no date, no icons, no notifications, no university emblem, no logos, no recognizable objects, no device frame, no hands, no mouse, no watermark. Opaque background. Aim for exact 1080×2376 pixels.
```
