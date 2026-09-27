#!/bin/bash
cd "$(dirname "$0")" || exit 1

pause_and_exit() {
  local result_code="$1"
  read -r -p "按回车结束 / Press Return to close."
  exit "$result_code"
}

echo "TicketRoute — PE6201 个人 Final Project"
echo "统一启动入口 / Single starting point"
echo
if [ ! -f scripts/run_project.py ] || [ ! -f app.py ]; then
  echo "请先解压整个压缩包，保留这个文件与 app.py 在同一文件夹。"
  pause_and_exit 1
fi

if [ "$#" -eq 0 ]; then
  echo "1  第一次：小额费用检查（程序停线 US\$0.10）"
  echo "2  费用结果核对后：继续完整评估（累计程序停线 US\$7）"
  echo "3  完整结果核对后：打开本地演示（默认使用已有结果）"
  echo
  read -r -p "第一次请输入 1，再按回车 [默认 1]: " choice
  choice="${choice:-1}"
elif [ "$#" -eq 1 ]; then
  case "$1" in
    --cost-check) choice=1 ;;
    --continue) choice=2 ;;
    --demo) choice=3 ;;
    --offline) choice=offline ;;
    *) echo "请直接运行 START_HERE_MAC.command。"; pause_and_exit 1 ;;
  esac
else
  echo "请直接运行 START_HERE_MAC.command。"
  pause_and_exit 1
fi

case "$choice" in
  1|2|3|offline) ;;
  *) echo "未开始运行。请重新启动并输入 1、2 或 3。"; pause_and_exit 1 ;;
esac

if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
  echo "Python 3.10 or newer is needed."
  echo "请从 https://www.python.org/downloads/macos/ 安装稳定版 Python 3。"
  echo "安装后重新打开这个入口，不需要另装 Python 软件包。"
  pause_and_exit 1
fi

if [ "$choice" = 3 ]; then
  echo "正在打开本地演示。回放和关键词模式不需要 API Key。"
  echo "地址：http://127.0.0.1:8765；关闭演示时在此窗口按 Control+C。"
  python3 app.py --open-browser
  pause_and_exit "$?"
fi

echo "Checking the project before any paid call..."
if ! python3 -m unittest discover -s tests; then
  echo "离线检查未通过。请发回错误截图，先不要输入密钥。"
  pause_and_exit 1
fi

if [ "$choice" = offline ]; then
  python3 scripts/run_project.py --offline
  pause_and_exit "$?"
fi

echo
echo "仅在下方隐藏输入提示中粘贴课程 OpenRouter API Key，再按回车。"
echo "粘贴后不会显示字符或星号；不要重复粘贴。密钥不会写入项目文件。"
if [ "$choice" = 1 ]; then
  echo "本次只做小额费用检查：--stage validation --budget-usd 0.10"
  echo "已记录费用加 US\$0.05 预留超过停线时停止；这不是平台账户硬限额。"
  python3 scripts/run_project.py --prompt-for-key --stage validation --budget-usd 0.10
  result_code=$?
  echo
  echo "这一步出现 STOPPED: Project spending cap reached 是预期检查点。"
  echo "费用检查完成后，请先交回结果，不要马上选择 2。"
else
  echo "继续完整评估：--budget-usd 7.00；包含此前费用检查的已记录花费。"
  echo "保留并复用已完成结果；这个程序停线不保证 US\$7 内一定跑完。"
  python3 scripts/run_project.py --prompt-for-key --budget-usd 7.00
  result_code=$?
  echo
  if [ "$result_code" -eq 0 ]; then
    echo "完整评估已完成，请交回结果供核对。"
  else
    echo "完整评估已停止，请交回结果检查原因。先不要提高预算或重新运行。"
  fi
fi
echo "请把此文件夹内的 TicketRoute_Results.zip 上传回当前聊天。"
echo "如有其他错误，也请发回错误部分截图。若未生成 ZIP，只发错误截图。"
echo "保留整个文件夹和 results；后续仍使用这个入口。"
pause_and_exit "$result_code"
