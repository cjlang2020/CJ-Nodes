# 微表情与 FACS 表演参考库｜Ai 角色表情提示词精华

> 用途：写作/生成视频提示词时，当用户提出「人物情绪」「剧情需要某种情绪」「表情不对/像假笑」「表演痕迹重」时，**查本文件取肌肉动作坐标**，不要直接写情绪词。
> 关联提示词：`H3-文戏-V1.txt` / `H3-文戏-V2.txt` / `H3-武戏-V1.txt`
> 素材来源：公众号文章《你的AI角色，没有演技》（mp.weixin.qq.com/s/54hiR0cG5uSuMr5yii93Nw）核心内容 + 按 FACS 标准做的坐标扩展。
> 原文完整 80 种表情提示词列表未随文发出，本文件第七、八节给出可用的等价坐标表。

---

## 零、一句话结论

**情绪词不是指令，肌肉动作才是指令。**

同一个「笑」，只有 **AU6（眼轮匝肌）+ AU12（颧大肌）同时出现**才是可信的真实微笑（杜兴式微笑，唯一被心理学界公认无法伪造的笑）；只有 AU12 就是典型的「礼貌性假笑」。

人类视觉对表情变化的探测阈值约 **100 毫秒（0.1 秒）**。一个不自然的眨眼、一次错误的嘴角弧度，就会触发**恐怖谷效应**。反过来，瞳孔微震、眼角自然弯曲几毫米、眼轮匝肌轻微收缩，观众能在毫秒级产生情感共鸣。

AI 生成表情「假」的根本原因：**用情绪标签（“愤怒”“开心”）当表情指令，而不是用肌肉动作坐标。**

---

## 一、为什么 AI 生成的表情总是「假」

1. **FACS（面部动作编码系统）**：心理学家 Paul Ekman 于 1970 年代建立，把人类面部表情分解为 **46 个独立动作单元（Action Units，AU）**，每个 AU 对应一块或一组特定肌肉的收缩。
2. **实证基础**：Ekman 和 Friesen 在巴布亚新几内亚对福尔人（Fore people）做跨文化表情识别实验，证实六种基本情绪的识别具有跨文化一致性。
3. **阈值**：0.1 秒。错误弧度 → 恐怖谷。
4. **致命错误**：直接写情绪标签，缺少肌肉动作、缺少时序、缺少幅度、缺少负面规避。

**典型病症**：主角从第一帧到最后一帧挂着同一副表情（嘴角微扬、眼神空洞）——第三场吵架在笑、第七场告白在笑、第十一场挨了一巴掌还在笑。不是模型不行，是提示词里根本没写「表情变化」。

---

## 二、微表情提示词「五层架构」

从宏观到微观逐层锁定（实测于即梦 Seedance 2.0、文心 ERNIE 4.5 Turbo VL、Wan 2.2 等）：

| 层 | 名称 | 内容 | 关键点 |
|---|---|---|---|
| 第一层 | **身份锚定** | 年龄、脸型、五官特征、肤质 | 锚定越清晰，模型对面部的渲染精度越高。东亚人脸结构：**种族 + 年龄 + 脸型 + 5 个以上面部特征（眼睛、鼻子、嘴唇、眉毛、下颌）** |
| 第二层 | **情绪基调** | 用「视觉具象化」替代抽象词 | ❌「开心」 ✅「眼部周围肌肉轻微收紧，眼角出现细微放射状纹路；嘴角向斜上方提拉，露出不超过 6 颗上牙」 |
| 第三层 | **肌肉动作描述** | 核心层，精确到 FACS 单元 | 需包含 **部位 + 动作方向 + 动作幅度** |
| 第四层 | **时序编排** | 拆成多个时间窗口（time window），逐窗独立描述 | 表情是动态过程，不是静态图片 |
| 第五层 | **环境配合** | 环境光方向、镜头景别、氛围色温 | 直接影响表情呈现效果 |

**第一层示例**：
> 东亚女性，25岁，鹅蛋脸，单眼皮但眼裂偏长，鼻梁中等不算高，唇形偏薄，眉毛偏细呈自然弯月形，下颌线清晰但不锋利。

**第二层对照**：

| ❌ 抽象写法 | ✅ 视觉具象化写法 |
|---|---|
| 「开心」 | 眼部周围肌肉轻微收紧，眼角出现细微放射状纹路；嘴角向斜上方提拉，露出不超过 6 颗上牙 |
| 「愤怒」 | 眉毛下压、眉心出现纵向褶皱，眼轮匝肌收紧，下颌咬合肌硬化 |
| 「悲伤」 | 上眼睑轻微下垂，嘴角水平拉长后下沉，鼻翼无扩张 |

**第三层示例**：
> 颧大肌收缩，将嘴角向耳侧方向提拉约 5 毫米；眼轮匝肌外侧收紧，眼角下弯；上唇提肌轻微收缩，露出上排牙齿不超过 4 颗。

**第四层示例**：
> 从 0 到 0.5 秒，眼睛先睁大；0.5 到 1.2 秒，瞳孔轻微收缩，嘴角向下沉；1.2 到 1.8 秒，嘴唇闭合，下颌收紧。

**第五层示例**：
> 侧面 45 度冷光从上往下打，制造鼻翼和下颌的锐利阴影；相机中景，焦点锁在眼部。

> ⚠️ **与「参考图零描述原则」的冲突裁定**：ComfyUI 工作流中用户传入参考图时，第一层「身份锚定」必须**整层跳过**（不得描述五官/脸型/发质/服饰），省下的文字预算全部投入第三层肌肉动作与第四层时序。微表情写的是「肌肉怎么动」，不是「长什么样」，不违反零描述原则。

---

## 三、五要素公式与解剖级术语表

### 3.1 五要素公式

**面部部位 + 变化方向 + 力度程度 + 时间节奏 + 负面规避**

缺任何一个维度，AI 都可能自行发挥。

**案例：压抑的怒火**

| 维度 | 内容 |
|---|---|
| 部位 + 方向 + 力度 | 降口角肌收缩，嘴角下压约 3 毫米；眼轮匝肌下半部收缩，下眼睑轻微上移；咬肌紧张，下颌线明显硬化 |
| 时间节奏 | 从第 1 秒开始持续，直到对话结束 |
| 负面规避 | 无夸张皱眉、无咬牙切齿、无面部潮红（避免卡通化崩坏） |

### 3.2 解剖级术语速查表（直接抄「提示词写法」那一列）

| 部位 | 肌肉名称 | AU | 收缩效果 | 提示词写法 |
|---|---|---|---|---|
| 嘴角 | 颧大肌 Zygomaticus Major | AU12 | 嘴角向耳侧上提 | Zygomaticus major contracted, pulling lip corners up and outward |
| 嘴角 | 降口角肌 Depressor Anguli Oris | AU15 | 嘴角向下沉 | Depressor anguli oris active, corners of lips pulling downward |
| 眼睛 | 眼轮匝肌 Orbicularis Oculi | AU6/AU7 | 眼角收紧、眼尾纹路 | Orbicularis oculi tensed, crow's feet appearing at lateral canthus |
| 下颌 | 咬肌 Masseter | — | 下颌线硬化 | Masseter tensed, jawline sharply defined |
| 眉毛 | 皱眉肌 Corrugator Supercilii | AU4 | 眉间纵纹 | Corrugator contracted, vertical lines between brows |
| 眼眶 | 上睑提肌 Levator Palpebrae | AU5 | 上眼睑抬起 | Levator palpebrae engaged, upper eyelid lifted |
| 嘴唇 | 口轮匝肌 Orbicularis Oris | AU23/AU24 | 嘴唇闭合/抿紧 | Orbicularis oris tightened, lips pressed into a thin line |
| 鼻翼 | 鼻肌 Nasalis | AU9 | 鼻翼扩张/扇动 | Nasalis active, nostrils subtly flaring |
| 前额 | 额肌 Frontalis | AU1/AU2 | 眉毛上抬、额头横纹 | Frontalis contracted, horizontal forehead wrinkles appearing |

**用法**：把「提示词写法」一列直接塞进表情描述，比写「他生气了」有效一百倍。

### 3.3 常用 AU 编号补充对照（撰写坐标表时使用）

| AU | 名称 | 视觉结果 |
|---|---|---|
| AU1 | 额肌内段上提 Inner Brow Raiser | 眉内侧上抬，眉呈「八」字形，眉心出现纵向皱褶起点 |
| AU2 | 额肌外段上提 Outer Brow Raiser | 眉毛整体上抬，额头出现横向纹路 |
| AU4 | 皱眉肌 Brow Lowerer | 眉头下压内聚，眉间纵向褶皱 |
| AU5 | 上睑提肌 Upper Lid Raiser | 上眼睑抬起，眼裂增大，虹膜上方露出眼白 |
| AU6 | 颊肌/眼轮匝肌外侧 Cheek Raiser | 颧部隆起，下眼睑上抬，眼尾出现放射状纹路 |
| AU7 | 眼轮匝肌收紧 Lid Tightener | 眼睑收紧，眼裂变窄，下眼睑上移 |
| AU9 | 鼻肌 Nose Wrinkler | 鼻翼上提皱起，鼻梁出现横纹 |
| AU10 | 提上唇肌 Upper Lip Raiser | 上唇上提，鼻唇沟加深，露上齿 |
| AU12 | 颧大肌 Lip Corner Puller | 嘴角向斜上方（耳侧）提拉 |
| AU13 | 颊肌 Cheek Puffer | 面颊鼓起 |
| AU14 | 颊提肌 Dimpler | 嘴角内收，出现酒窝式收紧 |
| AU15 | 降口角肌 Lip Corner Depressor | 嘴角下沉，嘴形拉长 |
| AU16 | 降下唇肌 Lower Lip Depressor | 下唇下压外翻 |
| AU17 | 颏肌 Chin Raiser | 下巴上抬隆起，下唇推起 |
| AU18 | 口轮匝肌 Lip Puckerer | 嘴唇收拢前噘 |
| AU20 | 笑肌/颈阔肌 Lip Stretcher | 嘴角水平横向拉开（恐惧式咧嘴） |
| AU23 | 口轮匝肌 Lip Tightener | 嘴唇抿紧变薄 |
| AU24 | 口轮匝肌 Lip Pressor | 双唇压紧闭合 |
| AU25 | 双唇分开 Lips Part | 上下唇自然松开（不说话时的微张） |
| AU26 | 下颌下落 Jaw Drop | 下颌放松下垂，嘴成椭圆 |
| AU27 | 口部拉伸 Mouth Stretch | 下颌大张，口部横向拉伸（吼/惊叫） |
| AU28 | 唇内收 Lip Suck | 嘴唇内收吸住 |
| AU43 | 闭眼 Eyes Closed | 双眼完全闭合 |
| AU45 | 眨眼 Blink | 单次自然眨眼 |

**关键组合**：
- **AU6 + AU12**（+AU25 下颌放松）= 杜兴式真实微笑；**只有 AU12** = 礼貌假笑。
- **AU1 + AU2 + AU4** = 「恐惧的眉毛」：额肌上提同时皱眉肌收缩，水平与垂直两个方向的**对抗拉力**，真人脸上极罕见 —— AI 生成必须显式约束，否则往往塌成「面无表情」。
- **AU4 + AU7 + AU25** = 压抑的怒火；**+AU10 + AU27** = 爆发大吼。

---

## 四、时序编排：AI 懂帧，不懂故事

**最容易忽略、但决定成败的一步。**

AI 理解的是「在 t=0.0 到 t=5.3 秒之间，角色面部发生了哪些变化」。若不主动拆成时间序列，AI 会用默认的**匀速渐变**——这是最不自然的演法，因为**真实人类表情从不匀速**。

**正确做法**：把一段表情拆成多个「时间窗口（time window）」，每个窗口 2–4 秒，独立描述。

**案例：绝望后冷静**

| 时间段 | 肌肉变化 | 心理对应 |
|---|---|---|
| 0–1 秒 | 眼轮匝肌完全放松，但视线仍锁定前方。上下眼睑距离略微增大——瞳孔充分暴露，目光失去聚焦点。鼻翼收缩，呼吸不规律。 | 创伤应激中的「解离状态」 |
| 1–2.5 秒 | 额肌轻微收缩，眉头上扬不超过 3 毫米。眼神逐渐从「涣散」转为「固定」——视线锁定在某一点，瞳孔轻微收缩。 | 「认知重评估」——大脑正在重新解释事件 |
| 2.5–4 秒 | 降口角肌收缩，嘴角下移约 2 毫米。下颌骨轻微前移，咬肌收紧。唇部闭合——嘴唇之间的缝隙消失。 | 进入「无情绪」的静默态 |
| 4–6 秒 | 嘴角恢复平直，下颌放松。目光低垂。呼吸恢复正常节律。 | 面部肌肉逐块恢复静息态 |

> 这套「按秒拆解」的写法，比一句「他绝望了」精准一万倍。

**时序写法通用骨架**（可直接套用）：
- `[0–0.4s]` 起始态：镜头切进时的静息面部 + 当前手部动作
- `[0.4–1.2s]` 第一变化：最先动的永远是**眼睛**（视线/眼睑），其次是眉
- `[1.2–2.5s]` 主变化：嘴角/下颌/咬肌，幅度 2–5 毫米
- `[2.5s–末尾]` 回落或维持：肌肉逐块恢复静息态，或把某个 AU 保持到镜头结束
- 每个窗口之间必须有**非匀速**差异（先快后慢、或先停后动）

---

## 五、进阶技巧：克制比爆发更难写

AI 最擅长「爆发」（训练数据里充满夸张表情），最不擅长「克制」。

**实测：提示词中加入 `subtle` / `slight`（微妙的、轻微的）能显著抑制卡通化倾向。**

| ❌ 错误写法 | ✅ 正确写法 |
|---|---|
| "He is sad." | A subtle expression of sadness. Eyes slightly unfocused, corners of the mouth relaxed but not lifted, a barely noticeable tension in the masseter. No exaggerated frown, no crying, no redness around the eyes. |
| AI 大概率生成：哭丧脸，嘴角下拉、眉头紧锁、眼睛泛红——表演痕迹过重 | AI 生成：一张「收着演的」悲伤脸 |

**权重调节法：用你不想要的负面词做排除约束**

```
no exaggerated expression
no wide open mouth
no raised eyebrows
no extreme frown
no tears
```

这类约束对 **Kling 和 Seedance 2.0** 的稳定性提升最明显，约 **30%–40%**。

**负面规避清单（按情绪挑 2–4 条即可，不要全堆）**：
| 情绪 | 常配的负面规避 |
|---|---|
| 悲伤 | no exaggerated frown / no crying / no redness around the eyes / no trembling lips |
| 愤怒 | no cartoon anger / no bared teeth / no facial flushing / no bulging eyes |
| 惊讶 | no wide open mouth / no exaggerated jaw drop / no raised eyebrows beyond 3mm |
| 恐惧 | no screaming / no trembling / no wide-eyed cartoon fear |
| 快乐 | no grin from ear to ear / no teeth fully visible / no crinkled cartoon eyes |
| 克制（通用） | no theatrical expression / no exaggerated micro-movements / no sudden pose change |

---

## 六、不同工具的实操差异

### 6.1 即梦 Seedance 2.0
- 最优做法：**按时间窗口逐秒描述，同时指定关键帧**（如「第 3 秒时眼睛开始移动，第 4.5 秒时完成视线切换」）→ 生成连续平滑动态。
- 提示词总长度建议 **300–500 tokens**。
- 识别 FACS 术语（如 Zygomaticus major）**表现稳定**。
- ⚠️ **一次性堆叠超过 6 个动作单元时，响应准确率明显下降**。建议每段只聚焦 **3–5 个肌肉群**；分镜脚本按帧设计，不要一次给整段动作指令。

### 6.2 文心 ERNIE 4.5 Turbo VL
- 底层架构对连续性时序编码支持有限，更适配 **「关键帧到关键帧」** 转换模式（擅长按起止两张图插值中间过程，不擅长纯文本长序列推演）。
- 最优做法：**直接用解剖级动词替代情绪词**，按帧标签描述：
  > `[0s-1.2s]: subtle eyebrow lift → [1.3s-2.8s]: slow blink`
- 生成前确认「动作平滑度」不低于 **70%**，否则微动作容易跳变或卡顿。

### 6.3 通用原则
- **连续两个以上微动作必须用逗号或句号明确分隔**。堆叠无标点短语（`smiling eyes crinkling head tilting`）会被模型解析为三个独立特征而非协同表达，导致输出混乱。
- 不同模型 FACS 术语兼容性不同：Seedance 2.0 对「颧大肌 Zygomaticus major」更准，ERNIE 对「降口角肌 Depressor anguli oris」更稳。**建议针对所用模型做术语对照测试**。

---

## 七、九类常用表情坐标清单（原文）

### 7.1 快乐
| 变体 | 核心 AU | 视觉特征 | 提示词关键句 |
|---|---|---|---|
| 开怀大笑 | AU6 + AU12 + AU25（下颌放松） | 眼轮匝肌收紧，颧大肌强力上提，口轮匝肌放松 | Orbicularis oculi tight, zygomaticus major fully contracted, mouth slightly open, 6-8 upper teeth exposed |
| 含蓄微笑 | AU12（轻微） | 颧大肌轻微收缩，无眼轮匝肌参与 | Zygomaticus major subtly contracted, lip corners lifted slightly, no orbital tightening |

### 7.2 愤怒
| 变体 | 核心 AU | 视觉特征 | 提示词关键句 |
|---|---|---|---|
| 压抑的怒火 | AU4 + AU7 + AU25 | 皱眉肌下拉，眼轮匝肌收紧，口轮匝肌抿紧 | Corrugator active, brows lowered and drawn together; orbicularis oris tightened; masseter tensed, jawline defined |
| 爆发大吼 | AU4 + AU10 + AU25 + AU27 | 皱眉下压，提上唇肌上提露齿，口轮匝肌完全张开 | Corrugator contracted; levator labii superioris raised; mouth wide open with teeth fully visible |

### 7.3 悲伤
| 变体 | 核心 AU | 视觉特征 | 提示词关键句 |
|---|---|---|---|
| 啜泣 | AU1 + AU4 + AU15 | 额肌内段上提，皱眉肌收缩，降口角肌下沉 | Frontalis (inner) raised; corrugator contracted; depressor anguli oris active, lip corners pulled downward |
| 含泪强忍 | AU1 + AU2 + AU7 + AU15 | 额肌整体上提，眼轮匝肌收紧抑制泪液，降口角肌微收缩 | Frontalis raised; orbicularis oculi tightened (holding back tears); depressor anguli oris mildly contracted |

### 7.4 惊讶
| 变体 | 核心 AU | 视觉特征 | 提示词关键句 |
|---|---|---|---|
| 震惊 | AU1 + AU2 + AU5 + AU25 + AU27 | 额肌和上睑提肌同时上提，眼轮匝肌放松眼裂最大，下颌打开 | Frontalis and levator palpebrae fully engaged; eyes wide open; jaw dropped |

### 7.5 恐惧
| 变体 | 核心 AU | 视觉特征 | 提示词关键句 |
|---|---|---|---|
| 极度恐惧 | AU1 + AU2 + AU4 + AU5 + AU25 + AU27 | 额肌上提 + 皱眉下拉（矛盾共存），上睑提肌上提，口轮匝肌放松 | Frontalis raised while corrugator contracted; levator palpebrae elevated; mouth open; lips retracted horizontally |

> **补充说明**：AU1 + AU2 + AU4 在 FACS 中记为「恐惧的眉毛」——额肌上提同时皱眉肌收缩，产生水平和垂直两个方向的对抗拉力。这种肌肉拮抗在真人脸上非常罕见，但在 AI 生成中需要明确约束，否则容易产生「面无表情」的平庸结果。

---

## 八、扩展坐标表：50+ 表情（弱 / 中 / 强）

> 本节为按 FACS 标准推导的扩展表（**非原文**），用于覆盖原文提到的「完整 80 种表情」。**英文关键句可直接复制，中文为解释**。每段只取 3–5 个 AU，别整行照抄。

### 8.1 快乐类
| 表情 | AU | 英文关键句（可抄） |
|---|---|---|
| 开怀大笑（强） | AU6+AU12+AU25 | Orbicularis oculi tight, zygomaticus major fully contracted, mouth open, 6-8 upper teeth exposed |
| 纯真大笑（中） | AU6+AU12 | Zygomaticus major and orbicularis oculi contracting together, cheek raised, small crow's feet |
| 含蓄微笑（弱） | AU12 | Zygomaticus major subtly contracted, lip corners lifted ~2mm, no orbital tightening |
| 窃笑 | AU12+AU14+AU24 | Lip corners pulled in and up, slight dimpler, lips pressed, chin tilted down |
| 得意坏笑 | AU12（单侧）+AU4（微量） | One lip corner pulled up higher than the other, one brow slightly lowered |
| 讨好笑 | AU12+AU6（弱）+AU1 | Lip corners lifted while inner brows raised slightly, eyes softened, head slightly lowered |
| 温柔笑 | AU6（弱）+AU12（弱）+AU25 | Gentle cheek raise, small lip corner lift, lips slightly parted |
| 苦笑 | AU12（弱）+AU15+AU4 | Lip corners pulled up while sagging downward at the outer edges, brows slightly drawn |
| 欣慰笑 | AU6+AU12（弱）+AU1 | Cheeks raised, small lip corner lift, inner brows raised as if exhaling |
| 如释重负 | AU1+AU2+AU25+AU12（弱） | Brows briefly lifted, shoulders drop, lips part on an exhale, small smile settling |

### 8.2 愤怒类
| 表情 | AU | 英文关键句（可抄） |
|---|---|---|
| 压抑的怒火（弱） | AU4+AU7+AU24 | Corrugator slightly contracted, lid tightening, lips pressed thin, no teeth |
| 阴沉冷笑 | AU12（单侧）+AU4+AU7 | One lip corner lifted, brows lowered, lid tightened, jaw relaxed |
| 不耐烦怒视 | AU4+AU7+AU15 | Brows drawn, lid tightened, lip corner depressed, gaze fixed |
| 憋着一股火 | AU4+AU17+AU24 | Brows lowered, chin raised, jaw tight, lips pressed, nostril slightly flared |
| 咬牙切齿 | AU4+AU10+AU23+AU26 | Brows lowered, upper lip raised, teeth pressed together, jaw set |
| 爆发大吼（强） | AU4+AU10+AU25+AU27 | Corrugator contracted, upper lip raised, mouth wide open, teeth fully visible |
| 冷淡 | AU4（微）+AU15+AU43（半） | Brows almost flat with slight draw, lip corners level-to-down, eyelids half lowered |
| 怒极反笑 | AU12+AU6+AU4 | Lip corners and cheeks raised while the brows stay lowered — smile does not reach the eyes |

### 8.3 悲伤类
| 表情 | AU | 英文关键句（可抄） |
|---|---|---|
| 含泪强忍 | AU1+AU2+AU7+AU15 | Frontalis raised, orbicularis oculi tightened holding back tears, lip corners mildly depressed |
| 啜泣 | AU1+AU4+AU15+AU25 | Inner brows raised, corrugator contracted, lip corners pulled down, lips parted |
| 失声痛哭 | AU1+AU4+AU15+AU25+AU27 | Brows raised and drawn, deep mouth opening, lip corners strongly depressed |
| 低头落泪 | AU1+AU15+AU43 | Inner brows raised, head lowered, lip corners down, eyes closed |
| 麻木 | AU15+AU43（半）+AU17 | Face nearly at rest, lip corners depressed ~1mm, eyelids half lowered, chin slightly raised |
| 自嘲苦笑 | AU12（弱单侧）+AU15+AU1 | One lip corner dragged up, inner brow raised, gaze dropped |
| 失神 | AU43（半）+AU25+放松 | Eyes half closed and unfocused, lips slightly parted, no muscle tension in the face |
| 悔恨自责 | AU1+AU4+AU7+AU15 | Inner brows raised and drawn, lid tightened, lip corners depressed, head bowed |

### 8.4 惊讶类
| 表情 | AU | 英文关键句（可抄） |
|---|---|---|
| 轻度的意外 | AU1+AU2+AU5（弱） | Brows briefly lifted 2mm, eyes slightly widened, mouth closed |
| 难以置信 | AU1+AU2+AU4+AU25 | Brows raised while inner brows drawn, eyes held open, lips parted |
| 震惊 | AU1+AU2+AU5+AU25+AU26 | Frontalis and levator palpebrae fully engaged, eyes wide open, jaw dropped |
| 惊喜 | AU1+AU2+AU5+AU6+AU12 | Eyes and brows lifted, then cheeks and lip corners rise together |
| 被吓一跳 | AU1+AU2+AU5+AU7+AU27 | Brows flash up, eyes widen then tighten, mouth opens abruptly, head pulls back |

### 8.5 恐惧类
| 表情 | AU | 英文关键句（可抄） |
|---|---|---|
| 不安 | AU1+AU4+AU7+AU24 | Inner brows raised and drawn, lid tightened, lips pressed |
| 心虚躲闪 | AU7+AU15+AU45（偏） | Lid tightened, lip corner depressed, gaze darting, blink rate increased |
| 焦虑 | AU1+AU4+AU7+AU24+AU9 | Brows raised and drawn, nostrils slightly flared, lips pressed, breathing visible |
| 胆怯 | AU1+AU2+AU15+AU24 | Brows raised, lip corners down, lips pressed, head pulled back |
| 吓呆 | AU1+AU2+AU5+AU25+AU26 | Brows up, eyes fully open with pupils exposed, jaw dropped, body frozen |
| 极度恐惧 | AU1+AU2+AU4+AU5+AU25+AU27 | Frontalis raised while corrugator contracted, eyes wide, mouth open, lips retracted horizontally |
| 后怕 | AU1+AU4+AU25+AU12（弱） | Inner brows raised, brief exhale through parted lips, small relieved smile |

### 8.6 傲慢类
| 表情 | AU | 英文关键句（可抄） |
|---|---|---|
| 轻蔑瞥视 | AU12（单侧）+AU4（微）+AU7 | One lip corner lifted, slight brow draw, lid tightened, gaze slid sideways |
| 不屑冷笑 | AU12（单侧）+AU15 | One lip corner pulled up, opposite corner depressed, nostrils flared |
| 居高临下 | AU4（微）+AU43（半）+AU17 | Chin raised, eyelids lowered, slight brow draw, gaze from above the line of sight |
| 鄙夷 | AU9+AU10+AU12（单侧） | Nose wrinkled, upper lip raised, one lip corner pulled up |
| 轻佻调戏 | AU12（单侧）+AU6+AU1 | One lip corner raised, cheek slightly raised, inner brow lifted, head tilted |

### 8.7 害羞类
| 表情 | AU | 英文关键句（可抄） |
|---|---|---|
| 不好意思 | AU12（弱）+AU1+AU45（偏） | Small lip corner lift, inner brow raised, gaze dropped, blink rate increased |
| 低头脸红 | AU15+AU45（半）+AU24 | Lip corners slightly down, eyelids lowered, lips pressed, head bowed |
| 慌乱躲闪 | AU5+AU7+AU45（频繁） | Eyes widened then blinking rapidly, gaze shifting, mouth slightly open |
| 偷瞄 | AU7+AU45（单侧半） | Lid tightened with gaze slid sideways toward the target, then quickly away |
| 尴尬 | AU1+AU12（弱）+AU14+AU24 | Inner brow raised, small forced smile, dimpler tightened, lips pressed |

### 8.8 困倦类
| 表情 | AU | 英文关键句（可抄） |
|---|---|---|
| 打哈欠 | AU25+AU26+AU27+AU43 | Jaw drops wide, eyes squeeze closed, brow raises, slow recovery |
| 眼皮沉重 | AU43（半）+AU7+AU15 | Eyelids at half mast with lid tightened, lip corners slightly down |
| 慵懒 | AU43（半）+AU12（微）+AU25 | Half-lidded eyes, faint lip corner lift, lips slightly parted, jaw slack |
| 无精打采 | AU15+AU43（半）+AU17 | Face at rest with lip corners down, eyelids lowered, chin raised slightly, no tension |

### 8.9 宠溺类
| 表情 | AU | 英文关键句（可抄） |
|---|---|---|
| 温柔注视 | AU6（弱）+AU12（弱）+AU43（半） | Cheeks slightly raised, small lip corner lift, lower eyelids slightly relaxed |
| 慈爱笑 | AU6+AU12（弱）+AU1 | Cheeks raised, lip corners lifted gently, inner brows raised |
| 宠溺调侃 | AU12（单侧）+AU6+AU1 | One lip corner raised, cheek raised, inner brow lifted, head tilted |
| 心疼 | AU1+AU4+AU7+AU15 | Inner brows raised and drawn, lid tightened, lip corners slightly down, gaze held on the other person |
| 深情凝视 | AU6（弱）+AU7（微）+AU25 | Eyes held steady on the target, slight lid softening, no expression change for several seconds |

---

## 九、眼神光（Catchlight）—— 像素级的灵魂缺口

AI 默认生成的眼神光**随机且散乱**，导致角色像在「发呆」：瞳孔里的高光点没有明确逻辑方向，更像两盏小灯泡而不是真实视觉反射。

人眼处理眼神信息的神经通路**独立于面部识别系统**。大脑中存在专门的「眼神检测神经元」——当 AI 角色的眼神光指向明确方位时，观众会不由自主地跟随它寻找目标。这是进化本能，不需要学习。

**做法：在提示词中锁定眼神光坐标。** 如果角色注视远方目标，双眼反光点应同时指向右上方位（光源方向和视线方向一致）。

**写法**：
> Catchlight positioned at the upper-right corner of the pupil, indicating a light source from the upper-left. Both eyes share the same catchlight direction, creating visual convergence.

一句话，但在像素层面涉及至少 5–8 个像素的精准定位。

**检查点**：双眼高光方向一致（convergence）、高光点与场景主光方向不矛盾、未出现「两盏灯泡」式的无来源双高光。

---

## 十、操作指引：三步建成表情库

1. **第一步：建文档库** —— 按九大情绪分类建立独立章节，每类存放 3–5 个程度变体（**弱、中、强、收着演、放开了演**）。
2. **第二步：复制完整提示词** —— 使用时直接复制对应表情的完整提示词，替换角色名字即可。
3. **第三步：每帧备注表情编号** —— 在分镜脚本的「描述」列旁加一栏「表情编号」，**直接写 FACS 组合，不写情绪词**：
   - `AU6+AU12` = 真实的微笑
   - `AU1+AU2+AU4` = 恐惧前兆

**分镜表示例**：

| 分镜编号 | 景别 | 画面描述 | 表情编号 |
|---|---|---|---|
| 021 | 中景 | 陈建国看到儿子的短信，手机没放下 | AU1+AU4+AU15（额肌内段 + 皱眉肌 + 降口角肌） |
| 022 | 特写 | 他盯着屏幕，拇指悬在输入框上方 | AU7+AU25（眼轮匝肌收紧 + 口轮匝肌放松） |

---

## 十一、成本与边界

- **代价**：提示词从 3 个词扩展到 200–300 个词，tokens 消耗增加 **5–10 倍**。按 API 计费，单次生成成本从约 0.5 元升至 3–5 元。
- **值得做的**：观众需要喜欢 / 恨 / 心疼的**核心角色**。表情不对，观众入不了戏，前面做的场景特效全白搭。
- **不值得做的**：旁白型角色、工具人。
- **不适合**：「大旁白 + 扁平人物」的漫剧团队；**适合**「角色驱动型」故事。
- **H3/ComfyUI 落地注意**：
  1. 每段提示词**聚焦 3–5 个肌肉群**（超过 6 个 AU 准确率下降）。
  2. 微表情只写**肌肉动作 + 时序**，绝不写五官长相 —— 与参考图零描述原则一致。
  3. 时长与时间戳必须铺满整条时间轴（见 `H3-文戏-V2.txt` 第三章与第九章）。
  4. 抽象情绪词（紧张/愤怒/悲伤/心虚/克制/潜台词）一律不出现在最终 Prompt，只作内部判断。

---

## 附：原文提到的「完整 80 种表情提示词列表」名称

| 大类 | 包含表情 |
|---|---|
| 快乐类 | 开怀大笑、含蓄微笑、窃笑、得意坏笑、讨好笑、温柔笑、苦笑、欣慰笑、如释重负 |
| 愤怒类 | 压抑的怒火、爆发大吼、怒极反笑、阴沉冷笑、不耐烦怒视、憋着一股火、咬牙切齿、冷淡 |
| 悲伤类 | 啜泣、含泪强忍、低头落泪、失声痛哭、麻木、自嘲苦笑、失神、悔恨自责 |
| 惊讶类 | 震惊、轻度的意外、难以置信、惊喜、被吓一跳 |
| 恐惧类 | 极度恐惧、不安、心虚躲闪、吓呆、后怕、胆怯、焦虑 |
| 傲慢类 | 不屑冷笑、居高临下、轻蔑瞥视、鄙夷、轻佻调戏 |
| 害羞类 | 低头脸红、慌乱躲闪、偷瞄、尴尬、不好意思 |
| 困倦类 | 打哈欠、眼皮沉重、慵懒、无精打采 |
| 宠溺类 | 温柔注视、慈爱笑、宠溺调侃、心疼、深情凝视 |

> 原文的逐条完整提示词未随文发布，第八节的扩展坐标表即为其等价替代。
