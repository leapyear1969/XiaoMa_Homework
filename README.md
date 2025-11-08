# 每日作业生成器

该项目是一个基于 Tkinter 的桌面小工具，可以一键生成包含语文、数学、英语练习的 PDF 作业单，方便家长或老师为孩子安排每日练习。应用会根据题库与随机算法自动出题，并按当前日期命名生成的文件。

<img width="591" height="249" alt="image" src="https://github.com/user-attachments/assets/666d87e3-0da6-4425-bb24-3dc281ed9ffc" />

<img width="878" height="1186" alt="image" src="https://github.com/user-attachments/assets/6a24070e-8829-44a9-86d7-795b5ae7357e" />

## 2025/10/21 为了避免彩色墨盒消耗不均匀，增加彩色字体库，这样保证了消耗的均匀。
```python
colors = [
    {"name": "Graphite Gray", "hex": "#333333", "rgb": (51, 51, 51)},
    {"name": "Gray Blue", "hex": "#4A586E", "rgb": (74, 88, 110)},
    {"name": "Warm Gray", "hex": "#B8A89F", "rgb": (184, 168, 159)},
    {"name": "Olive Gray", "hex": "#9AA57C", "rgb": (154, 165, 124)},
    {"name": "Bamboo Leaf", "hex": "#A8B97A", "rgb": (168, 185, 122)},
    {"name": "Slate Blue", "hex": "#6A7BA2", "rgb": (106, 123, 162)},
    {"name": "Indigo Light", "hex": "#8BA3C7", "rgb": (139, 163, 199)},
    {"name": "Brick", "hex": "#B56547", "rgb": (181, 101, 71)},
    {"name": "Clay", "hex": "#C47F5A", "rgb": (196, 127, 90)},
    {"name": "Lavender Gray", "hex": "#B7A9CF", "rgb": (183, 169, 207)},
    {"name": "Lilac Mist", "hex": "#D7A9E3", "rgb": (215, 169, 227)}
]

```

## 功能特色
- 支持分别生成语文、数学、英语三科作业，也可一键生成“每日作业”合订版。
- 语文部分提供随机汉字书写格，自动标注拼音（依赖 `pypinyin`）。
- 数学部分提供加减乘除混合算式，支持自定义列宽与排版，适合打印练习。
- 英语部分基于 Oxford 3000 词表，按 A1~B2 词频级别筛选单词并生成书写练习格。
- 所有关键信息都会写入同目录下按日期命名的 PDF，例如 `2025-10-01-每日作业.pdf`。

## 项目结构
- `homework_app.py`：核心逻辑与 Tkinter 图形界面。
- `yuwen.txt`：语文字库，按行存放汉字及对应注释。
- `oxford-3000.csv`：英语词库，包含词性与级别信息。
- `start.bat`：Windows 快捷启动脚本，双击即可运行应用。
- `__pycache__`：Python 运行时生成的缓存，可忽略。

## 环境与依赖
- Python 3.10 及以上版本（代码使用了 3.10 的类型标注语法）。
- 系统需能访问 Windows 默认字体目录 `C:/Windows/Fonts`，以加载楷体、宋体及 Comic Sans。若字体缺失，可在系统中安装对应字体或自行修改代码中的字体配置。
- 第三方依赖：
  ```bash
  pip install reportlab pypinyin
  ```
  - `reportlab` 用于生成 PDF。
  - `pypinyin` 用于生成汉字拼音。

> **提示**：`tkinter` 随多数 Python Windows 发行版默认安装，无需额外配置。

## 快速开始
1. 安装 Python 3.10+ 并确保 `python` 与 `pip` 命令可用。
2. 在项目目录中安装依赖：
   ```bash
   pip install reportlab pypinyin
   ```
3. 运行应用：
   - 方式一：双击 `start.bat`；
   - 方式二：在命令行执行 `python homework_app.py`。
4. 在界面中选择英语词汇难度（A1/A2/B1/B2），点击“生成全科作业”。
5. 生成的 PDF 会保存在项目根目录下，文件名带有当天日期。

## 自定义资料
- **语文字表**：可按需编辑 `yuwen.txt`，每行一个汉字及注释，程序会自动随机抽取。修改后无需重启程序即可生效。
- **英语词库**：`oxford-3000.csv` 包含单词、词性、级别等列，格式为 UTF-8 编码。可添加或调整单词，保持列头不变即可。

## 常见问题
- **提示缺少依赖**：若界面弹出“缺少依赖”提示，请确认已安装 `reportlab` 与 `pypinyin`，并使用与 GUI 相同的 Python 解释器执行 `pip install`。
- **字体加载失败**：若系统不存在指定字体，可安装字体或在 `homework_app.py` 中调整 `PINYIN_FONT_FILES`、`COMIC_SANS_FONT_FILES` 等配置。
- **PDF 打开乱码**：请确保 PDF 阅读器支持中文字体，必要时在系统中安装相应宋体/楷体字体。

## 开发与测试建议
- 新增功能前，可运行 `python homework_app.py` 验证界面交互是否正常。
- 若要批量生成练习，建议先备份现有 PDF，防止被新的日期文件覆盖。

祝使用愉快！
