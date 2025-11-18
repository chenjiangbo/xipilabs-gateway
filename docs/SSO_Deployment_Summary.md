### **SSO 统一认证系统部署问题总结报告**

**日期**: 2025年11月8日

**项目目标**: 为 `www.xipilabs.com` (hero2), `taleweave.xipilabs.com` (TaleWeave) 和 `xipilabs-gateway` 部署完整的 SSO 统一认证系统。

---

#### **1. 项目 `hero2` (门户) 变更记录**

*   **问题**: 初始构建失败，`Cannot find name 'prisma'`。
    *   **原因**: `prisma` 客户端未导入。
    *   **修复**: 在 `src/app/api/auth/phone/verify/route.ts` 中添加 `import { prisma } from '@/lib/prisma';`。
*   **问题**: `Type error: 'phone_number' does not exist in type 'usersWhereInput'`。
    *   **原因**: Prisma `users` 模型中字段名为 `phone`，而非 `phone_number`。
    *   **修复**: 将 `src/app/api/auth/phone/verify/route.ts` 中所有 `phone_number` 替换为 `phone`。
*   **问题**: `Type error: Property 'set' does not exist on type 'Promise<ReadonlyRequestCookies>'`。
    *   **原因**: 在 Next.js Route Handler 中，`cookies()` 返回只读对象，不能直接 `set`。
    *   **修复**: 修改 `src/app/api/logout/route.ts`，通过 `NextResponse.redirect(url).cookies.set(...)` 设置 Cookie。
*   **问题**: `Type error: Property 'get' does not exist on type 'Promise<ReadonlyRequestCookies>'`。
    *   **原因**: `cookies()` 在 `src/app/api/me/route.ts` 中被错误地当作 Promise 处理。
    *   **修复**: 修改 `src/app/api/me/route.ts`，直接使用 `req.cookies.get()` 获取 Cookie。
*   **问题**: `hero2` 部署时环境变量丢失 (`Missing environment variable: GOOGLE_CLIENT_ID`)。
    *   **原因**: `deploy.yml` 中使用 `echo "${{ secrets.DOT_ENV }}" > .env` 写入 `.env` 文件时，特殊字符导致解析失败。
    *   **修复**: 修改 `deploy.yml`，将所有环境变量作为独立的 GitHub Secrets 传入，并在部署脚本中逐一写入 `.env` 文件。
*   **问题**: `Dockerfile` 中 Prisma 客户端 `MODULE_NOT_FOUND`。
    *   **原因**: `runner` 阶段从 `deps` 阶段复制 `node_modules`，但 `prisma generate` 在 `builder` 阶段执行。
    *   **修复**: 修改 `Dockerfile`，让 `runner` 阶段从 `builder` 阶段复制 `node_modules`。
*   **问题**: `hero2` 数据库连接失败 (`Can't reach database server at postgres:5433`)。
    *   **原因**: `DATABASE_URL` 中使用了 PostgreSQL 的外部端口 `5433`，而容器间通信应使用内部端口 `5432`。
    *   **修复**: 修改 `hero2` 的 `DATABASE_URL` secret，将端口改为 `5432`。

---

#### **2. 项目 `TaleWeave` (应用) 变更记录**

*   **问题**: `TaleWeave` 构建缓慢。
    *   **原因**: GitHub Actions 未启用 Docker 层缓存。
    *   **修复**: 修改 `.github/workflows/deploy.yml`，为 `docker/build-push-action` 添加 `cache-from` 和 `cache-to`。
*   **问题**: `contentlayer` 构建时 `TypeError: The "code" argument must be of type number`。
    *   **原因**: `contentlayer@0.3.4` 与 Node.js 22 兼容性问题。
    *   **修复**: 用户选择忽略此非致命错误，未进行代码修改。
*   **问题**: `TaleWeave` 部署时环境变量丢失。
    *   **原因**: `ci.yml` 中使用 `echo "${{ secrets.DOT_ENV }}" > .env` 写入 `.env` 文件时，特殊字符导致解析失败。
    *   **修复**: 修改 `ci.yml`，使用 `cat <<'EOF' > .env` 的 `heredoc` 方式安全写入 `DOT_ENV` 内容。
*   **问题**: 前端构建失败 (`Could not resolve "./pages/Login" from "src/App.tsx"`)。
    *   **原因**: SSO 改造后，旧的本地登录页面被删除，但 `App.tsx` 中仍有引用。
    *   **修复**: 移除 `App.tsx` 中对 `Login`、`PhoneLogin`、`MobileLogin`、`MobilePhoneLogin` 的导入和路由定义。
*   **问题**: 前端构建失败 (`Could not resolve "./pages/AuthCallback" from "src/App.tsx"`)。
    *   **原因**: SSO 改造后，`AuthCallback` 页面被删除，但 `App.tsx` 中仍有引用。
    *   **修复**: 移除 `App.tsx` 中对 `AuthCallback` 的导入和路由定义。
*   **问题**: 前端构建失败 (`"ensureSession" is not exported by "src/lib/auth.ts"`)。
    *   **原因**: `lib/auth.ts` 中 `ensureSession` 函数已被删除，但 `Splash.tsx` 中仍有引用。
    *   **修复**: 移除 `Splash.tsx` 中对 `ensureSession` 的导入和调用。
*   **问题**: 前端构建失败 (`"persistTokens" is not exported by "src/lib/auth.ts"`)。
    *   **原因**: `lib/auth.ts` 中 `persistTokens` 函数已被删除，但 `AuthDone.tsx` 中仍有引用。
    *   **修复**: 移除 `App.tsx` 中对 `AuthDone` 和 `MobileAuthDone` 的导入和路由定义。
*   **问题**: 后端启动失败 (`ModuleNotFoundError: No module named 'jose'`)。
    *   **原因**: `python-jose` 库未添加到 `apps/backend/requirements.txt`。
    *   **修复**: 在 `apps/backend/requirements.txt` 中添加 `python-jose[cryptography]>=3.3.0`。
*   **调试清理**:
    *   **修改**: 移除 `apps/backend/app/auth/dependencies.py` 中的调试日志。
    *   **修改**: 重新启用 `apps/web-pc/src/lib/api.ts` 中的 401 自动跳转。

---

#### **3. 项目 `xipilabs-gateway` (网关) 变更记录**

*   **问题**: Nginx 配置中 `certbot` 路径拼写错误。
    *   **原因**: `nginx_config/xipilabs.conf` 中 `w-ww` 应为 `www`。
    *   **修复**: 修正 `nginx_config/xipilabs.conf` 中的拼写错误。
*   **问题**: `auth_service` JWT 验证失败。
    *   **原因**: `hero2` 签发 token 时 `issuer` 为 `xipilabs-auth`，但 `auth_service` 验证时期望 `issuer` 为 `www.xipilabs.com`。
    *   **修复**: 修改 `auth_service/index.js`，将期望的 `issuer` 改为 `xipilabs-auth`。
*   **问题**: `TaleWeave` 首页被网关强制登录。
    *   **原因**: `nginx_config/xipilabs.conf` 中 `location /` 对 `taleweave.xipilabs.com` 强制 `auth_request`。
    *   **修复**: 修改 `nginx_config/xipilabs.conf`，使 `taleweave.xipilabs.com` 的 `location /` 公开访问，并为 `/app/` 路径添加保护。
*   **问题**: `TaleWeave` 后端收不到 `X-User-ID` 请求头。
    *   **原因**: Nginx 默认可能丢弃非标准请求头。
    *   **修复**: 在 `nginx_config/xipilabs.conf` 中添加 `underscores_in_headers on;`。
*   **调试清理**:
    *   **修改**: 移除 `nginx_config/xipilabs.conf` 中添加的 `X-Debug-Auth-User-Id` 调试头。

---

#### **4. 当前问题 (Current Problem)**

*   **现象**: 用户登录 `www.xipilabs.com` 后，点击 `TaleWeave` 卡片进入 `taleweave.xipilabs.com`，页面会立即跳转回 `www.xipilabs.com/login`，但该登录页显示用户已登录。
*   **核心**: `TaleWeave` 无法识别用户已登录状态。

---

#### **5. 我的最新分析 (My Latest Analysis)**

根据你最新的描述，问题依然是 `TaleWeave` 无法识别 `hero2` 设置的登录状态。

我之前对 `hero2` 设置 Cookie 的代码进行了检查，确认 `domain: '.xipilabs.com'` 是正确的，理论上应该允许 Cookie 在 `www.xipilabs.com` 和 `taleweave.xipilabs.com` 之间共享。

我最新的尝试是修改 `hero2` 设置 Cookie 时的 `SameSite` 属性为 `None`，并要求必须同时设置 `Secure` 属性。这是为了解决浏览器在跨子域 `fetch` 请求时可能拒绝发送 Cookie 的问题。

**如果 `SameSite=None` 仍然没有解决问题，那么可能的原因是：**

1.  **`Secure` 属性**：`SameSite=None` 必须配合 `Secure` 属性使用。如果 `hero2` 设置 Cookie 时 `secure: process.env.NODE_ENV === 'production'` 在生产环境没有生效，或者 `taleweave.xipilabs.com` 的请求不是 HTTPS，Cookie 就不会被发送。但我们确认了都是 HTTPS。
2.  **浏览器缓存**：尽管使用了无痕模式，但有时浏览器行为仍可能受缓存影响。
3.  **Nginx 缓存/配置未完全生效**：`gateway-nginx` 的配置更新后，可能需要更长时间才能完全生效，或者有其他缓存机制。
4.  **`auth_service` 仍然有问题**：尽管 `curl` 测试显示 `auth_service` 验证成功，但可能在某些特定情况下，它仍然返回了 `401`。
5.  **`auth-token` Cookie 根本没有被发送**：这是最直接的原因。浏览器出于某种我们尚未完全理解的安全策略，根本没有把 `auth-token` Cookie 发送给 `taleweave.xipilabs.com` 的请求。

---

#### **6. 下一步排查思路 (Next Debugging Steps)**

鉴于我们已经排除了后端和网关的大部分问题，现在需要更直接地确认浏览器行为。

**最关键的信息是：当浏览器访问 `taleweave.xipilabs.com` 并发起 `/api/users/me` 请求时，它到底有没有带上 `auth-token` 这个 Cookie。**

**排查方法：**

1.  **再次捕获 HAR 文件**：
    *   请你再次使用无痕模式。
    *   先访问 `www.xipilabs.com` 并登录。
    *   **然后，在浏览器开发者工具的“网络 (Network)”标签页打开的情况下**，访问 `https://taleweave.xipilabs.com`。
    *   等待页面加载完成，直到跳转发生。
    *   在“网络 (Network)”标签页中，右键点击任意请求，选择 **“Save all as HAR with content”** (保存所有为 HAR，包含内容)。
    *   把这个 HAR 文件发给我。

这个 HAR 文件将包含浏览器在访问 `taleweave.xipilabs.com` 时发出的所有请求，包括对 `/api/users/me` 的请求，以及这些请求头中是否包含了 `auth-token` Cookie。这将是决定性的证据。