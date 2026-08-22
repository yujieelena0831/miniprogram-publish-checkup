# 小程序发布合规校验器

`miniprogram-publish-checkup` 是一个面向微信小程序发布阶段的通用 Agent Skill。

用户只需要提供微信小程序项目文件夹或 ZIP，它会尽可能自动判断这个包体是否具备提审、预览或上线条件；如果不能，会说明不能上线的原因、问题位置、修改方法和复验方式。

## 它解决什么问题

小程序能在开发者工具里运行，不代表它已经可以上线。正式提审前还可能遇到：

- 项目文件、页面或组件不完整；
- 路由、TabBar、图标或分包配置错误；
- 主包或分包体积超出限制；
- 测试地址、HTTP 地址、密钥或服务端文件被错误打包；
- 隐私声明与实际调用能力不一致；
- CloudBase、正式后端、域名或环境配置存在风险；
- 备案、服务类目、行业资质或审核材料尚未确认；
- 缺少真实编译、体验版、真机测试和上线回滚证据。

这个 Skill 将这些分散的检查整理成一套包体优先的发布检查流程。

## 使用方式

### 安装到兼容 Agent Skills 的客户端

同一个仓库可以安装到 Codex、Claude Code、WorkBuddy，以及其他支持 `SKILL.md` 的 Agent。选择自己客户端对应的 Skill 目录即可。

| Agent | 个人 Skill 目录 |
| --- | --- |
| Codex | `$HOME/.agents/skills/` |
| Claude Code | `~/.claude/skills/` |
| WorkBuddy | `~/.workbuddy/skills/`，也可以在界面中上传文件夹或 ZIP |

以 Codex 为例：

```bash
git clone https://github.com/yujieelena0831/miniprogram-publish-checkup.git \
  "$HOME/.agents/skills/miniprogram-publish-checkup"
```

Claude Code：

```bash
git clone https://github.com/yujieelena0831/miniprogram-publish-checkup.git \
  ~/.claude/skills/miniprogram-publish-checkup
```

WorkBuddy 可以把仓库克隆到其个人 Skill 目录，或者直接上传从仓库下载的文件夹/ZIP。

安装后，在任意兼容 Agent 中提供小程序文件夹或 ZIP，并用自然语言发送：

```text
请检查这个微信小程序是否可以提审上线。
如果不能，请告诉我原因、修改位置、具体做法和复验方法。
```

不要求用户记住 `$skill-name`、`/skill-name` 或其他平台调用语法。只要 Agent 支持根据 `description` 自动匹配 Skill，就能从自然语言请求触发；也可以按客户端提供的方式显式选择该 Skill。

用户不需要先填写检查表。Skill 会先检查包体，再根据检测到的技术架构和业务能力生成适用的检查项。

### 直接运行包体预检

需要 Python 3，无额外第三方依赖：

```bash
python3 scripts/inspect_package.py /path/to/miniprogram
```

ZIP 也可以直接检查：

```bash
python3 scripts/inspect_package.py /path/to/miniprogram.zip
```

需要结构化结果时：

```bash
python3 scripts/inspect_package.py /path/to/miniprogram.zip --json
```

## 检查范围

检查会根据项目实际情况选择适用规则，主要覆盖：

1. 项目身份、AppID、源码根目录与构建产物；
2. 压缩包安全性、目录层级与交付完整性；
3. 页面、分包、组件、资源、路由和 TabBar；
4. 主包、各分包、总体积和最大文件；
5. 测试地址、非 HTTPS 地址、密钥及敏感文件；
6. CloudBase、自建 HTTPS 后端或混合架构；
7. 隐私 API、权限、支付、定位、相机、麦克风、上传等能力；
8. 主体、备案、服务类目、资质及内容经营风险；
9. 编译、预览、体验版、真机和审核复现条件；
10. 正式发布、监控、备份、灰度与回滚准备。

完整判定模型见 [`references/package-only-decision.md`](references/package-only-decision.md)。

## 判断结果

Skill 使用三种顶层结论：

| 结论 | 含义 |
| --- | --- |
| `BLOCKED` | 包体中已经发现明确问题，应当修改后再提审或发布 |
| `PACKAGE_CHECK_PASSED_EXTERNAL_CONFIRMATION_REQUIRED` | 包体静态检查未发现阻断项，但仍需确认微信后台、编译、真机或运营证据 |
| `READY_FOR_SUBMISSION_OR_RELEASE` | 包体及所有必要外部证据均已验证，可以进入对应发布阶段 |

每个非通过项都会尽量包含：

- 发现了什么；
- 为什么会影响提审或上线；
- 证据及文件位置；
- 应该如何修改；
- 修改完成后如何复验。

## 能力边界

仅凭项目包体，无法直接证明微信公众平台中的私有状态，例如备案结果、已选服务类目、行业资质、隐私保护指引、服务器域名白名单和正式审核状态。

因此，Skill 不会把“包里看不到”当成“已经通过”。这些事项会被标记为 `UNKNOWN`，并转换成尽可能少且明确的后台确认动作。

静态检查也不能替代微信开发者工具的最终编译结果、体验版真机测试、平台审核或法律意见。平台限制和提交规则可能变化，执行时应以当前官方规则为准。

## Agent 兼容性

核心 Skill 不依赖 Codex、Claude Code 或 WorkBuddy 的专属命令。它通过 `SKILL.md` 提供流程，通过相对路径读取 `references/` 和 `scripts/`。

要完整执行自动检查，宿主 Agent 需要：

- 能读取用户提供的项目文件夹或 ZIP；
- 能执行 Python 3；
- 允许 Skill 调用本地脚本。

三个脚本只使用 Python 标准库。如果某个 Agent 不能执行本地命令，仍可以按照 `SKILL.md` 和参考资料人工检查，但必须把未执行的自动检查标记为 `UNKNOWN`，不能当成通过。

`agents/openai.yaml` 只是可选的 Codex 界面元数据。其他 Agent 可以忽略它，不影响核心检查流程。

## 项目结构

```text
miniprogram-publish-checkup/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── package-only-decision.md
│   ├── project-structure.md
│   ├── navigation-and-tabbar.md
│   ├── backend-cloudbase.md
│   ├── release-compliance.md
│   ├── debug-preview-upload.md
│   └── common-pitfalls.md
└── scripts/
    ├── inspect_package.py
    ├── audit_miniprogram.py
    └── estimate_package_size.py
```

## 安全原则

Skill 默认只进行检查和报告。未经用户明确授权，不会自动上传代码、提交审核、正式发布、修改生产配置或变更 CloudBase 资源。
