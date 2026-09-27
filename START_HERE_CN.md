# TicketRoute 本地运行操作说明

更新：2026 年 9 月 27 日。按你的选择，本次在你自己的电脑运行。
这是 **PE6201 个人 Final Project：TicketRoute**，与保险理赔 AR/A2 完全独立。

你目前报告余额约 US$8。本次先做小预算费用检查，再决定完整评估能否在剩余额度内完成。
你现在只需要：把新的费用检查启动文件放进原项目文件夹 → 启动 → 输入课程密钥 → 发回结果 ZIP。
我负责检查真实结果、分析指标、完善报告、更新独立 GitHub 仓库，以及准备最终演示步骤。
以下主要按 **Mac** 写，Windows 方法在文末。

## 1. 下载和解压

1. 下载聊天里提供的 `TicketRoute_Final_Project_2026-09-27.zip`。
2. 双击 ZIP，解压得到 `TicketRoute` 文件夹，把整个文件夹放到桌面。
3. 如果之前已经解压，继续使用原来的 `TicketRoute` 文件夹，不要重新覆盖。
4. 下载本次提供的 **CHECK_COST_MAC.command**，放进 `TicketRoute` 文件夹，与 `app.py` 在同一层。这次使用这个新入口，它会显式覆盖旧的 12 美元设置。

保持整个文件夹完整，不要放进保险理赔项目。如果你已经开始过真实评估，请保留原文件夹，不要用新解压的文件夹覆盖它。

## 2. 在 Mac 上启动

1. 接上电源并保持联网，运行期间保持电脑上盖打开。
2. 同时按 **Command + 空格**，输入 **终端** 或 **Terminal**，按回车。
3. 在终端粘贴下面这行，**先不要按回车**：

   ```text
   caffeinate -i bash
   ```

4. 在 `bash` 后面按一下空格键。
5. 从 `TicketRoute` 文件夹，把 **CHECK_COST_MAC.command** 拖进终端窗口。终端会自动填入文件路径，原文件不会被移动。
6. 现在按回车。程序会自动进入正确的文件夹并开始检查。

`caffeinate -i` 会在程序运行期间防止 Mac 因闲置而睡眠，仍需保持上盖打开。
用这个方法即可，不需要调整文件权限，也不需要先输入文件夹路径。

## 3. 先看检查结果，再输入 API Key

开始会显示 `Checking the project before any paid call...`。检查通过会看到类似 `Ran 27 tests` 和 `OK`。
这些检查不调用付费模型。如果没有通过，先不要输入密钥，按第 5 部分处理。

随后程序会显示：

```text
Paste the course OpenRouter key here (hidden; not saved):
```

此时才把**课程提供的 OpenRouter API Key**粘贴到这个终端窗口，按回车。

- 粘贴时屏幕不显示字符，也不显示星号，这是正常的；不要因为看不见而重复粘贴。
- 这里要的是 OpenRouter 密钥，不是 GitHub 密码或 ChatGPT 登录密码。
- 密钥只在这次运行中使用，程序不把它写入项目文件。
- 不要把密钥发进聊天，也不要截图发回。

## 4. 先做小预算费用检查

这次入口把程序费用停线设为 **US$0.10**，只运行验证阶段，保留原有 100 条结果。
它先做原定的 5 条接口检查，正常后继续少量验证调用，直到小预算停线触发。
由于每次请求前还预留 US$0.05，实际已记录费用通常在约 US$0.05 附近就停止；这不是平台账户级硬限额。

看到下面这句是本次检查的预期结束方式，不表示程序坏了：

```text
STOPPED: Project spending cap reached. All completed predictions are saved.
```

然后会生成 `TicketRoute_Results.zip`。把它发回，我会据真实账单、输入/输出 token 和缓存命中情况估算剩余费用。
这次小批量的结果会被后续完整评估复用，不需要重复购买同一批预测。

正式继续时使用专门的 `CONTINUE_WITH_7USD_MAC.command`，费用停线为 **累计 US$7**，包含这次费用检查，不会在重新启动时清零。
按目前约 US$8 的余额预留约 US$1；如果余额另有消耗，这个余量也会变化。7 美元停线不能保证完整评估一定跑完。
先把费用检查结果发回，不要现在运行旧的 `START_HERE_MAC.command` 开始整批评估，也不要自行提高预算。

## 5. 把结果发回来；出错怎样处理

回到同一个 `TicketRoute` 文件夹，找到 **TicketRoute_Results.zip**，上传到当前聊天。
名字中带 **Results** 的才是运行结果，不是最初下载的项目 ZIP。

| 看到的情况 | 你需要做什么 |
| --- | --- |
| 出现 `Project spending cap reached` | 这是本次费用检查的预期停止点，发回 `TicketRoute_Results.zip` |
| 出现 `STOPPED`、`ERROR`、`FAILED` 或 HTTP 错误 | 发回结果 ZIP 和错误部分截图；先不要重跑 |
| 没有生成结果 ZIP | 只发错误部分截图，不要截图密钥 |
| 暂时没有新进度，但没有错误 | 继续等待，单次请求可能较慢 |
| 意外断网、关机或关掉窗口 | 保留原文件夹和 `results`，把已有 ZIP 或报错发回，由我判断如何继续 |
| 提示 `Python 3.10 or newer is needed` | 按下面安装 Python，再用同一个文件夹重做第 2 部分 |

需要安装 Python 时，打开 https://www.python.org/downloads/macos/ ，选择稳定版本的 **macOS installer**，下载后按默认步骤安装。
需要 Python 3.10 或更新版本，不需要另装 pip 包、Git 或编程软件。
如果出现安装 Apple 开发者命令行工具的提示，可以先取消，改用 Python 官方安装包。
如随后出现 `CERTIFICATE_VERIFY_FAILED`，把报错发回，不要自行关闭证书验证。

## 6. 结果交回后由我继续处理

我会核对评估是否完整、缓存及费用是否一致，然后完成最终指标、错误分析、最多 1,200 词的 trade-off report、独立仓库里的最终证据和演示脚本。
你不需要先自己算指标或改报告。

如果要查看本地演示，在新终端输入 `bash`、一个空格，再拖入 **OPEN_DEMO_MAC.command** 并按回车。
网页地址是 `http://127.0.0.1:8765`。默认是已记录的真实试测回放，不代表刚刚重新调用了模型。
正式录屏等完整结果核对后再进行，我会提供具体展示顺序和讲解稿。

本人录制、学校账号登录及 NTULearn 提交需要你本人完成，我会协助整理和检查材料。
目前完整真实评估及录屏尚未完成，报告仍是草稿，不能直接当最终稿提交。

## 7. 老师要求的依据

| 原始文件 | 已核对的要求 |
| --- | --- |
| Project Proposal Watchouts，第 3 页，提交前检查第 4 项 | “Your repository will run on someone else’s machine.” |
| Assessment Timeline，第 1 页，第 4 项 | Problem statement、最多 1,200 词的商业与技术权衡分析、GitHub 可运行代码、演示录像 |
| Class 6 C3，第 14–15 页 | 个人 Final Project 截止 **2026 年 10 月 4 日 23:59，新加坡时间** |

现有 Final Project 文档没有写“所有评估必须由学生本人在本地完成”。本次按你的偏好本地运行，同时保留老师要求的可移植运行能力。
单独的完整 Project Rubric 和教师个人 feedback 仍未找到，提交前还需核对学校最终提交页面。
截止日期使用后续 Class 6 C3 的更新，不使用早期 Timeline 的旧日期。AR/A2 的规则不移到这份个人项目。

独立仓库：https://github.com/raymondtu1230-sudo/PE6201-Final-TicketRoute
仓库目前为私有，提交前还要核对老师是否能访问。

## Windows 用户

如果你使用 Windows，不用上面的 Mac 命令：

1. 右键项目 ZIP → **全部解压**，打开解压后的 `TicketRoute` 文件夹。
2. 点击文件资源管理器顶部地址栏，输入 `cmd`，按回车。
3. 输入 `py -3 --version` 并回车，确认至少为 3.10。若找不到 `py`，从 https://www.python.org/downloads/windows/ 安装稳定版 Python 3。
4. 输入 `py -3 -m unittest discover -s tests -v` 并回车，只有看到 `OK` 才继续。
5. 输入 `py -3 scripts/run_project.py --prompt-for-key --stage validation --budget-usd 0.10` 并回车。
6. 按第 3 至 5 部分输入密钥、等待并交回结果。电脑接电，并在系统电源设置中暂时设置运行期间不睡眠，完成后恢复原设置。

Windows 方法使用同一套 Python 程序；当前没有在你的 Windows 电脑上实测。遇到报错直接把错误部分发回。
