# <font style="color:rgb(27, 28, 29);">XipiLabs 统一登录 (SSO) 架构方案</font>
## <font style="color:rgb(27, 28, 29);">1. 项目背景与现状</font>
### <font style="color:rgb(27, 28, 29);">1.1. 项目目标</font>
<font style="color:rgb(27, 28, 29);">为 XipiLabs 旗下所有产品实现统一的单点登录（Single Sign-On, SSO）功能。用户在官网（</font>`<font style="color:rgb(68, 71, 70);">www.xipilabs.com</font>`<font style="color:rgb(27, 28, 29);">）登录一次后，访问其他子域产品（如 </font>`<font style="color:rgb(68, 71, 70);">taleweave.xipilabs.com</font>`<font style="color:rgb(27, 28, 29);">）时应自动保持登录状态，无需重复认证。</font>

### <font style="color:rgb(27, 28, 29);">1.2. 当前架构</font>
+ **<font style="color:rgb(27, 28, 29);">服务器：</font>**<font style="color:rgb(27, 28, 29);"> 所有项目统一部署于一台位于日本东京的服务器上。</font>
+ **<font style="color:rgb(27, 28, 29);">网关 (Gateway)：</font>**<font style="color:rgb(27, 28, 29);"> 存在一个总路由项目 (</font>`<font style="color:rgb(68, 71, 70);">xipilabs-gateway</font>`<font style="color:rgb(27, 28, 29);">)，作为反向代理。它负责解析不同的子域名，并将请求转发到后端各自独立的产品容器端口。</font>
+ **<font style="color:rgb(27, 28, 29);">项目：</font>**<font style="color:rgb(27, 28, 29);"> 存在多个独立的应用项目，包括：</font>
    - <font style="color:rgb(27, 28, 29);">门户网站: </font>`<font style="color:rgb(68, 71, 70);">www.xipilabs.com</font>`<font style="color:rgb(27, 28, 29);"> (对应 </font>`<font style="color:rgb(51, 51, 51);background-color:rgb(229, 229, 229);">/Users/xipilabs/dev/Experiment/hero2/project</font>`<font style="color:rgb(27, 28, 29);">)</font>
    - <font style="color:rgb(27, 28, 29);">产品1: </font>`<font style="color:rgb(68, 71, 70);">taleweave.xipilabs.com</font>`<font style="color:rgb(27, 28, 29);"> (对应 </font>`<font style="color:rgb(51, 51, 51);background-color:rgb(229, 229, 229);">/Users/xipilabs/dev/TaleWeave</font>`<font style="color:rgb(27, 28, 29);">)</font>
    - <font style="color:rgb(27, 28, 29);">产品2: </font>`<font style="color:rgb(68, 71, 70);">flowweaver.xipilabs.com</font>`<font style="color:rgb(27, 28, 29);"> (对应 </font>`<font style="color:rgb(51, 51, 51);background-color:rgb(229, 229, 229);"> /Users/xipilabs/dev/Experiment/FlowWeaver</font>`<font style="color:rgb(27, 28, 29);">)</font>

<font style="color:rgb(51, 51, 51);background-color:rgb(229, 229, 229);">总路由 /Users/xipilabs/dev/xipilabs-gateway</font>

+ **<font style="color:rgb(27, 28, 29);">部署：</font>**<font style="color:rgb(27, 28, 29);"> 每个项目（门户、产品1、产品2、Gateway）都是独立的 GitHub 仓库，并通过 GitHub Actions 自动化 CI/CD 流程，独立打包成容器运行。</font>

### <font style="color:rgb(27, 28, 29);">1.3. 核心痛点</font>
<font style="color:rgb(27, 28, 29);">当前架构导致各产品之间身份认证完全隔离。如不进行改造，每个产品（TaleWeave, FlowWeave）都需要独立实现一套登录系统，用户体验割裂且开发维护成本高。</font>

### <font style="color:rgb(27, 28, 29);">1.4. 决策与方案选型</font>
<font style="color:rgb(27, 28, 29);">我们评估了两种主流方案：</font>

1. **<font style="color:rgb(27, 28, 29);">方案一 (IDaaS)：</font>**<font style="color:rgb(27, 28, 29);"> 使用第三方服务如 Authing.cn。</font>
    - _<font style="color:rgb(27, 28, 29);">评估结论：</font>_<font style="color:rgb(27, 28, 29);"> 免费版功能受限（可能仅支持1个社交登录源），无法同时满足 Google 和微信登录的需求。付费版（如 ￥99/月）对于项目当前阶段（用户为朋友同事，尚未盈利）而言，固定成本过高。</font>
2. **<font style="color:rgb(27, 28, 29);">方案二 (DIY 自建)：</font>**<font style="color:rgb(27, 28, 29);"> 利用现有门户网站自建统一认证中心。</font>
    - _<font style="color:rgb(27, 28, 29);">评估结论：</font>_**<font style="color:rgb(27, 28, 29);">此为最终选定方案。</font>**
    - _<font style="color:rgb(27, 28, 29);">理由：</font>_
        * **<font style="color:rgb(27, 28, 29);">零月租成本：</font>**<font style="color:rgb(27, 28, 29);"> 充分利用现有服务器资源，无固定套餐费。</font>
        * **<font style="color:rgb(27, 28, 29);">已有代码积累：</font>**<font style="color:rgb(27, 28, 29);"> 团队已在一个产品中实现了 Google 登录和短信登录，微信登录代码也已编写（待认证）。</font>
        * **<font style="color:rgb(27, 28, 29);">可控性高：</font>**<font style="color:rgb(27, 28, 29);"> 可自由扩展支持任意多种登录方式，数据100%自控。</font>

<font style="color:rgb(27, 28, 29);">本方案将详细阐述如何执行</font>**<font style="color:rgb(27, 28, 29);">方案二</font>**<font style="color:rgb(27, 28, 29);">。</font>

## <font style="color:rgb(27, 28, 29);">2. 核心架构与角色定义</font>
<font style="color:rgb(27, 28, 29);">本方案的核心是将认证逻辑上浮，实现认证与业务的彻底分离。</font>

1. **<font style="color:rgb(27, 28, 29);">门户网站 (Auth Center):</font>**`<font style="color:rgb(68, 71, 70);">www.xipilabs.com</font>`
    - **<font style="color:rgb(27, 28, 29);">项目路径:</font>**`<font style="color:rgb(68, 71, 70);">/Users/xipilabs/dev/Experiment/hero2/project</font>`
    - **<font style="color:rgb(27, 28, 29);">职责:</font>**
        * <font style="color:rgb(27, 28, 29);">提供</font>**<font style="color:rgb(27, 28, 29);">所有</font>**<font style="color:rgb(27, 28, 29);">的登录UI（Google/微信/短信登录按钮）。</font>
        * <font style="color:rgb(27, 28, 29);">处理</font>**<font style="color:rgb(27, 28, 29);">所有</font>**<font style="color:rgb(27, 28, 29);">的登录回调（</font>`<font style="color:rgb(68, 71, 70);">/auth/callback/google</font>`<font style="color:rgb(27, 28, 29);"> 等）。</font>
        * <font style="color:rgb(27, 28, 29);">管理用户数据库（注册、查询用户）。</font>
        * **<font style="color:rgb(27, 28, 29);">核心：</font>**<font style="color:rgb(27, 28, 29);"> 登录成功后，</font>**<font style="color:rgb(27, 28, 29);">生成 (Sign) JWT</font>**<font style="color:rgb(27, 28, 29);">。</font>
        * **<font style="color:rgb(27, 28, 29);">核心：</font>**<font style="color:rgb(27, 28, 29);"> 将 JWT 存入一个</font>**<font style="color:rgb(27, 28, 29);">跨子域 (Cross-Subdomain) Cookie</font>**<font style="color:rgb(27, 28, 29);">。</font>
        * <font style="color:rgb(27, 28, 29);">处理集中的 </font>`<font style="color:rgb(68, 71, 70);">/logout</font>`<font style="color:rgb(27, 28, 29);"> 请求。</font>
2. **<font style="color:rgb(27, 28, 29);">产品应用 (Products):</font>**`<font style="color:rgb(68, 71, 70);">taleweave.xipilabs.com</font>`<font style="color:rgb(27, 28, 29);">, </font>`<font style="color:rgb(68, 71, 70);">flowweaver.xipilabs.com</font>`
    - **<font style="color:rgb(27, 28, 29);">项目路径:</font>**`<font style="color:rgb(68, 71, 70);">.../TaleWeave</font>`<font style="color:rgb(27, 28, 29);">, </font>`<font style="color:rgb(68, 71, 70);">.../FlowWeaver</font>`
    - **<font style="color:rgb(27, 28, 29);">职责:</font>**
        * **<font style="color:rgb(27, 28, 29);">前端:</font>**<font style="color:rgb(27, 28, 29);"> 不再处理任何登录逻辑。唯一任务是：检查自身状态，如果发现未登录，</font>**<font style="color:rgb(27, 28, 29);">重定向到门户网站</font>**<font style="color:rgb(27, 28, 29);">。</font>
        * **<font style="color:rgb(27, 28, 29);">后端:</font>****<font style="color:rgb(27, 28, 29);">完全移除</font>**<font style="color:rgb(27, 28, 29);">所有 session 和 JWT 校验逻辑。它</font>**<font style="color:rgb(27, 28, 29);">无条件信任</font>**<font style="color:rgb(27, 28, 29);"> Gateway 转发过来的请求头（如 </font>`<font style="color:rgb(68, 71, 70);">X-User-ID</font>`<font style="color:rgb(27, 28, 29);">）。</font>
3. **<font style="color:rgb(27, 28, 29);">总路由 (Gateway):</font>**`<font style="color:rgb(68, 71, 70);">xipilabs-gateway</font>`
    - **<font style="color:rgb(27, 28, 29);">项目路径:</font>**`<font style="color:rgb(68, 71, 70);">/Users/xipilabs/dev/xipilabs-gateway</font>`
    - **<font style="color:rgb(27, 28, 29);">职责:</font>**
        * <font style="color:rgb(27, 28, 29);">继续扮演反向代理和路由转发的角色。</font>
        * **<font style="color:rgb(27, 28, 29);">核心：</font>**<font style="color:rgb(27, 28, 29);"> 拦截</font>**<font style="color:rgb(27, 28, 29);">所有</font>**<font style="color:rgb(27, 28, 29);">发往“产品应用”的请求。</font>
        * <font style="color:rgb(27, 28, 29);">读取请求中的 Cookie，</font>**<font style="color:rgb(27, 28, 29);">校验 (Verify) JWT</font>**<font style="color:rgb(27, 28, 29);">。</font>
        * **<font style="color:rgb(27, 28, 29);">如果校验通过:</font>**<font style="color:rgb(27, 28, 29);"> 从 JWT 中解析出用户信息（如 </font>`<font style="color:rgb(68, 71, 70);">userId</font>`<font style="color:rgb(27, 28, 29);">），将其</font>**<font style="color:rgb(27, 28, 29);">注入</font>**<font style="color:rgb(27, 28, 29);">到新的 HTTP 请求头（如 </font>`<font style="color:rgb(68, 71, 70);">X-User-ID: 123</font>`<font style="color:rgb(27, 28, 29);">），然后才转发给后端的产品容器。</font>
        * **<font style="color:rgb(27, 28, 29);">如果校验失败 (或没有Cookie):</font>**<font style="color:rgb(27, 28, 29);"> 直接 302 重定向到</font>**<font style="color:rgb(27, 28, 29);">门户网站</font>**<font style="color:rgb(27, 28, 29);">的登录页。</font>

## <font style="color:rgb(27, 28, 29);">3. 详细实施步骤</font>
### <font style="color:rgb(27, 28, 29);">步骤一：迁移并集中化登录逻辑 (门户网站)</font>
1. **<font style="color:rgb(27, 28, 29);">迁移代码:</font>**<font style="color:rgb(27, 28, 29);"> 将您在“产品1”中已写好的 Google、短信、微信登录的</font>**<font style="color:rgb(27, 28, 29);">后端逻辑</font>**<font style="color:rgb(27, 28, 29);">（包括 </font>`<font style="color:rgb(68, 71, 70);">Controller/Handler</font>`<font style="color:rgb(27, 28, 29);">, </font>`<font style="color:rgb(68, 71, 70);">Service</font>`<font style="color:rgb(27, 28, 29);"> 层代码）全部</font>**<font style="color:rgb(27, 28, 29);">剪切</font>**<font style="color:rgb(27, 28, 29);">并</font>**<font style="color:rgb(27, 28, 29);">粘贴</font>**<font style="color:rgb(27, 28, 29);">到“门户网站”项目中。</font>
2. **<font style="color:rgb(27, 28, 29);">建立新路由 (门户网站后端):</font>**
    - `<font style="color:rgb(68, 71, 70);">GET /login</font>`<font style="color:rgb(27, 28, 29);">: 返回登录页面 (给用户看)。</font>
    - `<font style="color:rgb(68, 71, 70);">GET /auth/google</font>`<font style="color:rgb(27, 28, 29);">: 重定向到 Google 授权页。</font>
    - `<font style="color:rgb(68, 71, 70);">GET /auth/callback/google</font>`<font style="color:rgb(27, 28, 29);">: 处理 Google 回调。</font>
    - `<font style="color:rgb(68, 71, 70);">POST /auth/sms/send</font>`<font style="color:rgb(27, 28, 29);">: 发送短信验证码。</font>
    - `<font style="color:rgb(68, 71, 70);">POST /auth/sms/verify</font>`<font style="color:rgb(27, 28, 29);">: 校验验证码并登录。</font>
    - `<font style="color:rgb(68, 71, 70);">GET /auth/wechat</font>`<font style="color:rgb(27, 28, 29);">: （您未来使用）获取微信二维码。</font>
    - `<font style="color:rgb(68, 71, 70);">GET /auth/callback/wechat</font>`<font style="color:rgb(27, 28, 29);">: （您未来使用）处理微信回调。</font>
    - `<font style="color:rgb(68, 71, 70);">GET /logout</font>`<font style="color:rgb(27, 28, 29);">: 处理登出。</font>

### <font style="color:rgb(27, 28, 29);">步骤二：实现 JWT 签发与跨域 Cookie (门户网站)</font>
<font style="color:rgb(27, 28, 29);">这是 SSO 的</font>**<font style="color:rgb(27, 28, 29);">第一个关键点</font>**<font style="color:rgb(27, 28, 29);">。当用户在门户网站通过任何方式（Google/短信）成功登录后：</font>

1. **<font style="color:rgb(27, 28, 29);">查询/创建用户:</font>**<font style="color:rgb(27, 28, 29);"> 在您的数据库中找到或创建该用户，获取其唯一 </font>`<font style="color:rgb(68, 71, 70);">userId</font>`<font style="color:rgb(27, 28, 29);">。</font>
2. **<font style="color:rgb(27, 28, 29);">生成 JWT:</font>**
    - <font style="color:rgb(27, 28, 29);">您需要一个</font>**<font style="color:rgb(27, 28, 29);">全局唯一的 </font>**`**<font style="color:rgb(68, 71, 70);">JWT_SECRET</font>**`<font style="color:rgb(27, 28, 29);">（一个长且复杂的字符串），并将其配置在“门户网站”和“Gateway”的环境变量中。</font>
    - _<font style="color:rgb(27, 28, 29);">关键代码 (示例, Node.js + </font>_`_<font style="color:rgb(68, 71, 70);">jsonwebtoken</font>_`_<font style="color:rgb(27, 28, 29);">):</font>_

```plain
// 假设在 /auth/callback/google 成功获取用户信息 user
const payload = {
  userId: user.id,
  email: user.email,
  // 'iss' (issuer) 和 'aud' (audience) 是好习惯
  iss: '[https://www.xipilabs.com](https://www.xipilabs.com)', 
  aud: 'xipilabs-products' 
};
const jwtToken = jwt.sign(payload, process.env.JWT_SECRET, { 
  expiresIn: '7d' // 7天过期
});
```

3. **<font style="color:rgb(27, 28, 29);">设置跨域 Cookie:</font>**
    - <font style="color:rgb(27, 28, 29);">这是</font>**<font style="color:rgb(27, 28, 29);">最核心的步骤</font>**<font style="color:rgb(27, 28, 29);">。您必须在 HTTP 响应中设置 Cookie，并指定 </font>`<font style="color:rgb(68, 71, 70);">Domain</font>`<font style="color:rgb(27, 28, 29);"> 为您的</font>**<font style="color:rgb(27, 28, 29);">顶级域名</font>**<font style="color:rgb(27, 28, 29);">。</font>
    - _<font style="color:rgb(27, 28, 29);">关键代码 (示例, Node.js + Express):</font>_

```plain
// 紧接着上一步，获取到 jwtToken
const cookieOptions = {
  // 关键：.xipilabs.com (前面的点) 
  // 使其对 www.、taleweave.、flowweave. 都有效
  domain: '.xipilabs.com', 
  path: '/',
  httpOnly: true, // 必须：防止前端JS读取，防XSS
  secure: true,   // 必须：只在HTTPS下发送
  sameSite: 'Lax' // 推荐：防止CSRF，'Lax'允许从顶级域名跳转时携带
};

// 假设您的 cookie 名叫 'auth-token'
res.cookie('auth-token', jwtToken, cookieOptions);

// 最后，重定向回用户最初想去的地方 (见步骤三)
res.redirect(req.query.redirect_url || '/');
```

### <font style="color:rgb(27, 28, 29);">步骤三：实现认证重定向 (SSO Dance)</font>
<font style="color:rgb(27, 28, 29);">这个流程串联起所有服务：</font>

1. **<font style="color:rgb(27, 28, 29);">(产品前端)</font>**<font style="color:rgb(27, 28, 29);"> 用户访问 </font>`<font style="color:rgb(68, 71, 70);">https://taleweave.xipilabs.com/dashboard</font>`<font style="color:rgb(27, 28, 29);">（一个需要登录的页面）。</font>
2. **<font style="color:rgb(27, 28, 29);">(产品前端)</font>**<font style="color:rgb(27, 28, 29);"> TaleWeave 的前端（例如在 React 的根组件或路由守卫中）检查本地是否已有用户信息。发现没有。</font>
3. **<font style="color:rgb(27, 28, 29);">(产品前端)</font>****<font style="color:rgb(27, 28, 29);">执行重定向</font>**<font style="color:rgb(27, 28, 29);">。</font>
    - _<font style="color:rgb(27, 28, 29);">关键代码 (示例, JavaScript):</font>_

```plain
// 假设前端通过 /api/me 检查登录状态，失败后
const currentUrl = window.location.href;
const loginUrl = `https://www.xipilabs.com/login?redirect_url=${encodeURIComponent(currentUrl)}`;
window.location.href = loginUrl; // 跳转到门户网站
```

4. **<font style="color:rgb(27, 28, 29);">(门户网站)</font>**<font style="color:rgb(27, 28, 29);"> 用户在 </font>`<font style="color:rgb(68, 71, 70);">www.xipilabs.com</font>`<font style="color:rgb(27, 28, 29);"> 上完成登录。</font>
5. **<font style="color:rgb(27, 28, 29);">(门户网站后端)</font>**<font style="color:rgb(27, 28, 29);"> 按照</font>**<font style="color:rgb(27, 28, 29);">步骤二</font>**<font style="color:rgb(27, 28, 29);">，设置跨域 Cookie。</font>
6. **<font style="color:rgb(27, 28, 29);">(门户网站后端)</font>**<font style="color:rgb(27, 28, 29);"> 从查询参数中获取 </font>`<font style="color:rgb(68, 71, 70);">redirect_url</font>`<font style="color:rgb(27, 28, 29);">（即 </font>`<font style="color:rgb(68, 71, 70);">https://taleweave.xipilabs.com/dashboard</font>`<font style="color:rgb(27, 28, 29);">），并 </font>`<font style="color:rgb(68, 71, 70);">res.redirect()</font>`<font style="color:rgb(27, 28, 29);"> 回去。</font>
7. **<font style="color:rgb(27, 28, 29);">(浏览器)</font>**<font style="color:rgb(27, 28, 29);"> 浏览器收到重定向，</font>**<font style="color:rgb(27, 28, 29);">带着 </font>**`**<font style="color:rgb(68, 71, 70);">.xipilabs.com</font>**`**<font style="color:rgb(27, 28, 29);"> 的 Cookie</font>**<font style="color:rgb(27, 28, 29);"> 再次请求 </font>`<font style="color:rgb(68, 71, 70);">https://taleweave.xipilabs.com/dashboard</font>`<font style="color:rgb(27, 28, 29);">。</font>

### <font style="color:rgb(27, 28, 29);">步骤四：实现 Gateway 认证拦截 (Gateway)</font>
<font style="color:rgb(27, 28, 29);">请求现在到达了 Gateway，这是 SSO 的</font>**<font style="color:rgb(27, 28, 29);">第二个关键点</font>**<font style="color:rgb(27, 28, 29);">：</font>

1. **<font style="color:rgb(27, 28, 29);">(Gateway)</font>**<font style="color:rgb(27, 28, 29);"> Gateway 拦截所有发往 </font>`<font style="color:rgb(68, 71, 70);">taleweave.</font>`<font style="color:rgb(27, 28, 29);"> 和 </font>`<font style="color:rgb(68, 71, 70);">flowweave.</font>`<font style="color:rgb(27, 28, 29);"> 的请求。</font>
2. **<font style="color:rgb(27, 28, 29);">(Gateway)</font>**<font style="color:rgb(27, 28, 29);"> 读取 </font>`<font style="color:rgb(68, 71, 70);">JWT_SECRET</font>`<font style="color:rgb(27, 28, 29);"> 环境变量（</font>**<font style="color:rgb(27, 28, 29);">必须</font>**<font style="color:rgb(27, 28, 29);">与步骤二中的密钥一致）。</font>
3. **<font style="color:rgb(27, 28, 29);">(Gateway)</font>**<font style="color:rgb(27, 28, 29);"> 尝试从请求中解析 </font>`<font style="color:rgb(68, 71, 70);">auth-token</font>`<font style="color:rgb(27, 28, 29);"> Cookie。</font>
    - _<font style="color:rgb(27, 28, 29);">关键逻辑 (示例, 伪代码, 具体实现取决于您的Gateway技术栈):</font>_

```plain
// 伪代码: Gateway 的中间件逻辑
function handleRequest(request):
    // 1. 提取 cookie
    token = request.cookies['auth-token']

    // 2. 检查公开路径 (例如 /login, /assets 等，这些不需要登录)
    if isPublicPath(request.path):
        forward(request) // 直接转发
        return

    // 3. 检查Token
    if not token:
        // 没有token，重定向到门户登录页
        redirectToLogin(request)
        return

    // 4. 校验Token
    try:
        payload = jwt.verify(token, process.env.JWT_SECRET, { 
            issuer: '[https://www.xipilabs.com](https://www.xipilabs.com)',
            audience: 'xipilabs-products' 
        })
    except (TokenExpiredError, InvalidSignatureError):
        // Token无效或过期，重定向到门户登录页 (并清除坏cookie)
        clearCookie(request)
        redirectToLogin(request)
        return

    // 5. 校验成功！注入用户信息
    // 这是后端产品信任的来源
    request.headers['X-User-ID'] = payload.userId
    request.headers['X-User-Email'] = payload.email

    // 6. 转发给后端产品容器
    forward(request)


function redirectToLogin(request):
    // 构造回调URL
    originalUrl = "https://" + request.host + request.path
    loginUrl = "[https://www.xipilabs.com/login?redirect_url=](https://www.xipilabs.com/login?redirect_url=)" + encode(originalUrl)
    return redirect(302, loginUrl)
```

### <font style="color:rgb(27, 28, 29);">步骤五：简化产品后端 (TaleWeave, FlowWeave)</font>
1. **<font style="color:rgb(27, 28, 29);">移除所有</font>**`<font style="color:rgb(68, 71, 70);">jwt.verify</font>`<font style="color:rgb(27, 28, 29);">、session 校验、Google/短信登录的</font>**<font style="color:rgb(27, 28, 29);">所有后端代码</font>**<font style="color:rgb(27, 28, 29);">。</font>
2. **<font style="color:rgb(27, 28, 29);">信任请求头</font>**<font style="color:rgb(27, 28, 29);">。您的产品后端现在变得极其简单和干净。</font>
    - _<font style="color:rgb(27, 28, 29);">关键代码 (示例, TaleWeave 的 /api/me 接口):</font>_

```plain
// ----------------------------------------------------
// 之前：你需要复杂的 session/token 校验
// 现在：你只需要...
// ----------------------------------------------------

// Node.js + Express 示例
app.get('/api/me', (req, res) => {
  // 直接从 Gateway 注入的 header 中获取 userId
  const userId = req.headers['x-user-id']; 

  if (!userId) {
    // 这不应该发生，如果发生了说明Gateway配置有误
    // 但作为安全兜底，返回401
    return res.status(401).send('Unauthorized');
  }

  // 你100%信任这个userId，直接去数据库查
  const user = db.users.findById(userId);
  res.json(user);
});
```

### <font style="color:rgb(27, 28, 29);">步骤六：实现集中登出 (门户网站)</font>
1. **<font style="color:rgb(27, 28, 29);">(产品前端)</font>**<font style="color:rgb(27, 28, 29);"> 任何产品（如 TaleWeave）的“登出”按钮，都必须是一个</font>**<font style="color:rgb(27, 28, 29);">指向门户网站登出接口</font>**<font style="color:rgb(27, 28, 29);">的链接。</font>
    - _<font style="color:rgb(27, 28, 29);">关键代码 (示例, React):</font>_

```plain
// TaleWeave 里的登出按钮
<a href="[https://www.xipilabs.com/logout?redirect_url=https://www.xipilabs.com](https://www.xipilabs.com/logout?redirect_url=https://www.xipilabs.com)">
  登出
</a>
```

2. **<font style="color:rgb(27, 28, 29);">(门户网站后端)</font>**<font style="color:rgb(27, 28, 29);"> 创建 </font>`<font style="color:rgb(68, 71, 70);">/logout</font>`<font style="color:rgb(27, 28, 29);"> 接口，其</font>**<font style="color:rgb(27, 28, 29);">唯一</font>**<font style="color:rgb(27, 28, 29);">职责是</font>**<font style="color:rgb(27, 28, 29);">清除跨域 Cookie</font>**<font style="color:rgb(27, 28, 29);">。</font>
    - _<font style="color:rgb(27, 28, 29);">关键代码 (示例, Node.js + Express):</font>_

```plain
app.get('/logout', (req, res) => {
  // 必须使用与设置时完全相同的 
  // domain, path, secure, httpOnly 选项来清除
  const cookieOptions = {
    domain: '.xipilabs.com',
    path: '/',
    httpOnly: true,
    secure: true,
    sameSite: 'Lax'
  };

  // 设置一个空值和过期时间
  res.cookie('auth-token', '', { 
    ...cookieOptions, 
    expires: new Date(0) // 设置为过去的日期
  });

  // 重定向到指定地址，通常是门户首页
  res.redirect(req.query.redirect_url || '/');
});
```

**<font style="color:rgb(27, 28, 29);">方案总结：</font>**<font style="color:rgb(27, 28, 29);"> 这个方案将认证（AuthN）逻辑</font>**<font style="color:rgb(27, 28, 29);">上浮</font>**<font style="color:rgb(27, 28, 29);">到了“门户网站”和“Gateway”层，让您的核心产品（TaleWeave, FlowWeave）</font>**<font style="color:rgb(27, 28, 29);">只关注业务逻辑</font>**<font style="color:rgb(27, 28, 29);">，这是一个非常健康和可扩展的架构。</font>

