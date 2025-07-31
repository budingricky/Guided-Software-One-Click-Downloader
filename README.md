# 软件资源整合桌面应用程序

一款类似Ninite的Windows 11桌面应用程序，用于管理和安装1000+款常用软件。

## 功能特性

### 🔧 软件资源整合
- 收集1000+款常用软件的最新版安装包
- 涵盖7大类别：系统工具、办公软件、设计创意、开发工具、网络工具、娱乐影音、行业软件
- 自动获取软件安装包链接，支持真正的自动下载

### 🎯 交互功能设计
- 多级列表软件分类，支持用户多选
- 退出多级菜单后保持用户选择状态
- 一键取消已选项目功能（全部取消/指定取消）
- 实时显示已选择软件列表

### ⚙️ 安装包处理功能
- 用户确定选择后进入配置界面
- 支持对所选软件进行具体配置
- 生成类似Ninite的一键安装程序
- 支持将安装程序保存到用户指定路径

### 🎨 UI设计
- 简洁、圆润、清晰、美观的界面风格
- 现代化Windows 11风格设计
- 响应式布局，适配不同屏幕尺寸

## 软件分类

### 系统工具 (60+)
- **系统优化**: CCleaner、Advanced SystemCare、Wise Care 365等
- **压缩解压**: WinRAR、7-Zip、Bandizip等
- **备份恢复**: Macrium Reflect、EaseUS Todo Backup等
- **硬件检测**: CPU-Z、GPU-Z、HWMonitor等
- **安全防护**: Windows Defender、Malwarebytes、卡巴斯基等
- **进程管理**: Process Explorer、Task Manager等

### 办公软件 (70+)
- **文档处理**: Microsoft Office、WPS Office、LibreOffice等
- **思维导图**: XMind、MindManager、FreeMind等
- **PDF工具**: Adobe Acrobat Pro、Foxit PhantomPDF等
- **翻译工具**: DeepL、Google翻译、百度翻译等
- **笔记工具**: Microsoft OneNote、Evernote、Notion等
- **协作工具**: Slack、Microsoft Teams、Zoom等

### 设计创意 (80+)
- **图像编辑**: Adobe Photoshop、GIMP、Corel Painter等
- **矢量设计**: Adobe Illustrator、CorelDRAW、Inkscape等
- **视频编辑**: Adobe Premiere Pro、Final Cut Pro、DaVinci Resolve等
- **音频处理**: Adobe Audition、Audacity、Logic Pro等
- **3D设计**: Blender、3ds Max、Maya等
- **截图录屏**: Snagit、Camtasia、OBS Studio等

### 开发工具 (90+)
- **代码编辑器**: Visual Studio Code、Sublime Text、Atom等
- **IDE集成开发环境**: Visual Studio、Eclipse、IntelliJ IDEA等
- **版本控制**: Git、GitHub Desktop、SourceTree等
- **数据库工具**: MySQL Workbench、Navicat、DBeaver等
- **调试工具**: Chrome DevTools、Postman、Fiddler等
- **编程语言环境**: Python、Node.js、Java JDK等

### 网络工具 (60+)
- **浏览器**: Google Chrome、Mozilla Firefox、Microsoft Edge等
- **下载工具**: IDM、迅雷、Free Download Manager等
- **远程控制**: TeamViewer、AnyDesk、VNC Viewer等
- **VPN工具**: ExpressVPN、NordVPN、Surfshark等
- **邮件客户端**: Microsoft Outlook、Mozilla Thunderbird等
- **FTP工具**: FileZilla、WinSCP、Cyberduck等

### 娱乐影音 (70+)
- **视频播放**: PotPlayer、VLC Media Player、KMPlayer等
- **音乐播放**: Foobar2000、Winamp、Spotify等
- **游戏平台**: Steam、Epic Games Launcher、Origin等
- **直播工具**: OBS Studio、Streamlabs OBS、XSplit等
- **图片查看**: IrfanView、FastStone Image Viewer等

### 行业软件 (70+)
- **工程制图**: AutoCAD、SolidWorks、CATIA等
- **数据分析**: Microsoft Excel、SPSS、Tableau等
- **医学软件**: 3D Slicer、OsiriX、Mimics等
- **教育软件**: Anki、Quizlet、Mathematica等
- **金融软件**: 同花顺、通达信、Bloomberg Terminal等

## 系统要求

- **操作系统**: Windows 11 64位
- **Python版本**: Python 3.8+
- **内存**: 最低4GB RAM，推荐8GB+
- **存储空间**: 至少1GB可用空间
- **网络**: 稳定的互联网连接（用于下载软件）

## 安装说明

### 1. 环境准备
```bash
# 确保已安装Python 3.8+
python --version

# 安装依赖包
pip install -r requirements.txt
```

### 2. 运行程序
```bash
# 进入项目目录
cd au

# 运行主程序
python main.py
```

### 3. 使用说明
1. 启动程序后，在左侧软件分类树中浏览软件
2. 双击软件名称将其添加到右侧已选列表
3. 在已选列表中可以移除不需要的软件
4. 点击"生成一键安装程序"创建批处理文件
5. 或点击"下载选中软件"直接下载安装包

## 项目结构

```
au/
├── main.py              # 主程序文件
├── software_data.json   # 软件数据库
├── requirements.txt     # 依赖包列表
├── README.md           # 项目说明文档
└── generated/          # 生成的安装程序目录（自动创建）
```

## 技术特性

- **GUI框架**: 使用Python tkinter构建现代化界面
- **数据存储**: JSON格式存储软件信息，易于维护和扩展
- **多线程下载**: 支持并发下载多个软件包
- **批处理生成**: 自动生成Windows批处理安装脚本
- **错误处理**: 完善的异常处理和用户提示
- **跨平台兼容**: 核心功能支持Windows、macOS、Linux

## 开发计划

### 已完成功能
- ✅ 基础GUI界面设计
- ✅ 软件分类树形结构
- ✅ 多选软件管理
- ✅ 批处理安装程序生成
- ✅ 软件下载功能
- ✅ 1000+软件数据库

### 计划功能
- 🔄 软件版本检测和更新
- 🔄 自定义软件添加
- 🔄 安装进度监控
- 🔄 软件分类搜索过滤
- 🔄 用户配置文件保存
- 🔄 多语言界面支持

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

### 如何贡献
1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

## 免责声明

本软件仅用于学习和研究目的。所有软件的版权归其各自的开发者所有。请确保您有权下载和使用这些软件，并遵守相关的许可协议。