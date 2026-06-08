# XPath 优化工具

一个基于 AI 的 XPath 表达式生成和优化工具，可以帮助您快速生成稳定、可靠的 XPath 表达式。

## 功能特点

- 🌐 **网页抓取**：自动抓取目标网页内容
- 🎯 **多种识别方式**：支持通过文本内容、现有 XPath 或 CSS 选择器来定位元素
- 🤖 **AI 分析**：使用大模型分析网页结构，生成最稳定的 XPath
- 📋 **一键复制**：方便快捷地复制生成的 XPath

## 安装依赖

```bash
pip install -r requirements_xpath.txt
```

或者手动安装：

```bash
pip install flask flask-cors requests beautifulsoup4 lxml
```

## 配置 Token（power-api）

### 方法 1：配置文件（推荐）

编辑 `xpath_config.json` 文件，填入你的 Token（可直接写 `AP_xxx`，或写成 `Bearer AP_xxx` 均可）：

```json
{
  "power_api_token": "your-token-here"
}
```

### 方法 2：环境变量

```bash
export POWER_API_TOKEN="your-token-here"       # 直接填 token
# 或
export POWER_API_TOKEN="Bearer your-token-here" # 也支持带 Bearer
```

### 方法 3：前端界面

也可以在前端界面的 "API Key" 输入框中直接输入 Token。

## 使用方法

### 1. 启动后端服务

```bash
python xpath_optimizer_server.py
```

服务将在 `http://localhost:5000` 启动。

### 2. 打开前端界面

在浏览器中访问 `http://localhost:5000`，或者直接打开 `xpath_optimizer.html` 文件。

### 3. 使用步骤

1. **输入网址**：在 "目标网址" 输入框中填入要分析的网页地址
2. **选择识别方式**：
   - **文本内容**：输入目标元素的文本内容
   - **当前 XPath**：输入需要优化的 XPath 表达式
   - **CSS 选择器**：输入 CSS 选择器，工具会转换为 XPath
3. **输入目标标签**：根据选择的识别方式，输入相应的内容
4. **（可选）输入 Token**：如果未在配置文件或环境变量中设置，可以在此输入
5. **点击"开始分析"**：等待 AI 分析并生成结果
6. **复制 XPath**：点击"复制 XPath"按钮复制结果

## API 接口

### POST /api/optimize-xpath

优化 XPath 的 API 端点。

**请求体：**

```json
{
  "url": "https://example.com/page",
  "target": "目标文本或 XPath 或 CSS 选择器",
  "type": "text|xpath|selector",
  "api_key": "可选的自定义 Token（留空则读取配置/环境变量）"
}
```

**响应：**

```json
{
  "xpath": "//div[@class='content']//p[contains(text(), '目标文本')]",
  "explanation": "使用 class 属性和文本匹配，避免了位置索引，提高了稳定性..."
}
```

### GET /api/health

健康检查端点，返回服务状态。

## 注意事项

1. **网络连接**：需要能够访问目标网页和 power-api 接口
2. **API 费用**：调用第三方大模型接口可能会产生费用，请注意使用量
3. **网页结构**：如果网页结构复杂或动态加载，可能需要多次尝试
4. **XPath 验证**：生成的 XPath 建议在实际环境中验证其准确性

## 故障排除

### 无法访问网页

- 检查网址是否正确
- 确认网络连接正常
- 某些网站可能有反爬虫机制

### API 调用失败

- 检查 API Key 是否正确配置
- 确认账户余额充足
- 检查网络连接

### 生成的 XPath 不准确

- 尝试使用更具体的目标文本
- 使用"当前 XPath"方式，提供现有的 XPath 进行优化
- 检查网页结构是否发生变化

## 技术栈

- **前端**：HTML + CSS + JavaScript（原生）
- **后端**：Flask（Python）
- **AI 模型**：power-api（可配置）

## 许可证

MIT License
