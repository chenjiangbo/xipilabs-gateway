# SSO 统一认证中心实施计划

## 1. 目标与原则

- **目标**: 实现以 `www.xipilabs.com` 为中心的单点登录（SSO），用户登录一次后，可无缝访问 `taleweave.xipilabs.com` 和 `flowweaver.xipilabs.com` 等所有产品。
- **原则**:
    - **分阶段实施**: 逐步上线，降低风险，便于调试和回滚。
    - **兼容生产**: 在实施过程中，确保现有服务的稳定性。
    - **安全第一**: 遵循安全最佳实践，特别是 JWT 和 Cookie 的处理。

## 2. 核心风险

1.  **生产环境中断**: 涉及网关和多个核心应用的变更，任何环节出错都可能导致全站服务不可用。
2.  **认证逻辑不匹配**: JWT 的签发与验证逻辑、密钥不匹配，会导致无限重定向或认证失败。
3.  **配置管理复杂**: 新增的 `JWT_SECRET` 和各项服务地址需要在多个项目的环境变量中正确配置。

## 3. 实施阶段

---

### **阶段一：准备与配置 (无服务中断)**

此阶段仅做后台准备，不影响线上服务。

1.  **备份关键配置**:
    - **操作**: 备份 `TaleWeave` 和 `hero2/project` 项目中所有 `.env` 文件，特别是包含 Google OAuth 凭证、数据库连接等信息的文件。
    - **目的**: 防止配置丢失，便于快速回滚。

2.  **生成并统一 JWT 密钥**:
    - **操作**: 生成一个高强度的、唯一的 `JWT_SECRET` 字符串。
    - **目的**: 作为后续“认证中心”和“网关”之间共享的加密密钥。

3.  **配置 Google OAuth 客户端**:
    - **操作**:
        1. 访问 Google Cloud Console。
        2. 找到 `TaleWeave` 项目正在使用的 OAuth 2.0 客户端 ID。
        3. 在“已获授权的 JavaScript 来源”中，添加 `https://www.xipilabs.com`。
        4. 在“已获授权的重定向 URI”中，添加 `https://www.xipilabs.com/api/auth/callback/google`。
    - **目的**: 允许新的“认证中心”使用现有的 Google 登录应用。

---

### **阶段二：构建统一认证中心 (Portal: `hero2/project`)**

此阶段开发新的认证中心，完成后可独立部署，暂不接入网关。

1.  **迁移并改造登录逻辑**:
    - **操作**:
        1. 从 `TaleWeave` 后端 (`apps/backend`) 识别并复制 Google 登录和短信登录的核心逻辑代码。
        2. 在 `hero2/project` (Next.js) 的 `src/app/api/auth/` 目录下，创建新的 API 路由来承载这些逻辑。
        3. 将 `TaleWeave` 的 Python/FastAPI 代码逻辑，改写为 TypeScript/Next.js API Route 的形式。
    - **目的**: 将认证功能集中到门户网站。

2.  **实现 JWT 签发与跨域 Cookie**:
    - **操作**:
        1. 在 `/api/auth/callback/google` 和短信验证成功后，使用**阶段一**生成的 `JWT_SECRET` 签发 JWT。
        2. 在响应中设置名为 `auth-token` 的 Cookie，并包含以下关键属性：
           - `domain: .xipilabs.com` (实现跨子域)
           - `httpOnly: true` (防止客户端脚本读取)
           - `secure: true` (仅在 HTTPS 下传输)
           - `sameSite: 'Lax'` (安全与体验的平衡)
    - **目的**: 实现 SSO 的核心凭证分发。

3.  **创建登录与登出页面**:
    - **操作**:
        1. 在 `hero2/project` 中创建 `/login` 页面，包含所有登录选项按钮。
        2. 创建 `/api/logout` 接口，其唯一作用是清除 `.xipilabs.com` 域下的 `auth-token` Cookie。
    - **目的**: 提供统一的登录入口和登出机制。

4.  **部署与独立测试**:
    - **操作**: 部署 `hero2/project` 的新版本。
    - **测试**: 直接访问 `https://www.xipilabs.com/login`，尝试登录，并使用浏览器开发者工具检查 `auth-token` Cookie 是否在 `.xipilabs.com` 域下正确设置。

---

### **阶段三：升级网关实现认证拦截 (Gateway: `xipilabs-gateway`)**

这是最关键的一步，将认证逻辑正式应用到流量入口。

1.  **技术选型：引入 `auth_request` 服务**:
    - **决策**: 由于 Nginx 本身不具备 JWT 校验能力，我们将引入一个轻量级的“认证服务”，并通过 Nginx 的 `auth_request` 模块调用它。这是最灵活和安全的方案。

2.  **创建认证服务**:
    - **操作**:
        1. 在 `xipilabs-gateway` 项目下创建新目录 `auth_service`。
        2. 在该目录中，创建一个简单的 Node.js (Express) 或 Python (Flask/FastAPI) 应用。
        3. 此应用提供一个端点（如 `/verify`），负责：
           - 读取请求中的 `auth-token` Cookie。
           - 使用共享的 `JWT_SECRET` 校验 JWT。
           - **成功**: 返回 `200 OK`，并在响应头中附带用户信息（如 `X-User-ID`, `X-User-Email`）。
           - **失败**: 返回 `401 Unauthorized`。
    - **目的**: 将 JWT 校验逻辑解耦，便于管理和扩展。

3.  **更新网关 Docker Compose**:
    - **操作**: 修改 `xipilabs-gateway/docker-compose.yml`，添加 `auth_service`，使其与 Nginx 服务一起启动。

4.  **修改 Nginx 配置**:
    - **操作**: 修改 `nginx_config/xipilabs.conf`：
        ```nginx
        # 在 http 或 server 块顶部
        # 定义认证服务
        upstream auth_service {
            server auth_service:3000; # 指向容器
        }

        # 在需要保护的 location 块内 (如 taleweave.xipilabs.com)
        location / {
            # 1. 发送认证子请求
            auth_request /_verify;

            # 2. 如果认证失败 (401)，执行命名 location @do_redirect
            error_page 401 = @do_redirect;

            # 3. 将认证服务的响应头（用户信息）捕获到变量中
            auth_request_set $auth_user_id $upstream_http_x_user_id;
            auth_request_set $auth_user_email $upstream_http_x_user_email;

            # 4. 将用户信息注入到转发给后端产品的请求头中
            proxy_set_header 'X-User-ID' $auth_user_id;
            proxy_set_header 'X-User-Email' $auth_user_email;

            # ... 原有的 proxy_pass 等指令
            proxy_pass http://taleweave_backend;
        }

        # 内部 location，用于处理认证请求
        location = /_verify {
            internal;
            proxy_pass http://auth_service/verify;
            proxy_pass_request_body off;
            proxy_set_header Content-Length "";
            proxy_set_header X-Original-URI $request_uri;
        }

        # 命名 location，用于处理重定向
        location @do_redirect {
            return 302 https://www.xipilabs.com/login?redirect_url=$scheme://$host$request_uri;
        }
        ```
    - **目的**: 将流量与认证逻辑串联起来。

---

### **阶段四：改造产品应用 (Product: `TaleWeave`)**

此阶段使产品应用适应新的认证模式。

1.  **后端改造 (`apps/backend`)**:
    - **操作**:
        1. **彻底移除**所有与用户认证相关的代码：Google/短信登录接口、JWT 校验中间件、session 管理。
        2. 修改所有需要用户身份的接口，改为从请求头 `X-User-ID` 中直接获取用户ID。
        3. 清理 `requirements.txt`，移除不再需要的认证库。
    - **目的**: 后端只关注业务，与认证完全解耦。

2.  **前端改造 (`apps/web-pc`)**:
    - **操作**:
        1. 移除所有登录页面和组件。
        2. 在全局路由守卫或 API 请求封装中，增加逻辑：如果 API 返回 401，或本地无用户信息，则执行重定向到 `https://www.xipilabs.com/login?redirect_url=...`。
        3. 将“登出”按钮的行为改为直接跳转到 `https://www.xipilabs.com/logout`。
    - **目的**: 将登录/登出流程交给认证中心处理。

3.  **清理配置**:
    - **操作**: 从 `TaleWeave` 项目的 `.env` 文件中移除 `JWT_SECRET`、Google OAuth 凭证等。

---

### **阶段五：部署与端到端测试**

1.  **部署顺序**:
    1.  部署**阶段二**完成的 `hero2/project` 新版本。
    2.  部署**阶段四**完成的 `TaleWeave` 新版本。
    3.  **最后部署** **阶段三**完成的 `xipilabs-gateway` 新版本（这是激活所有改动的开关）。

2.  **关键测试用例**:
    - **首次访问**: 访问 `taleweave.xipilabs.com` -> 期望：重定向到 `www.xipilabs.com/login`。
    - **登录流程**: 在官网登录 -> 期望：成功登录并重定向回 `taleweave.xipilabs.com`，显示已登录状态。
    - **SSO 体现**: 此时直接访问 `flowweaver.xipilabs.com` -> 期望：无需再次登录，直接进入。
    - **登出流程**: 在任一产品点击登出 -> 期望：重定向到官网，所有产品的登录状态均失效。
    - **异常测试**: 手动删除或篡改 Cookie -> 期望：访问受保护页面时，强制重新登录。

## 4. 回滚计划

- **网关层回滚**: 重新部署上一版的 `xipilabs-gateway` 容器。这是最快的中断恢复方式。
- **应用层回滚**: 依次重新部署 `TaleWeave` 和 `hero2/project` 的旧版本。
- **配置回滚**: 还原各项目的 `.env` 备份文件。
