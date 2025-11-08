# SSO 统一认证中心实施进度报告

## 1. 文档目的

本报告旨在详细记录 XipiLabs 统一登录 (SSO) 方案的实施进度、已完成的工作、当前所处的阶段以及接下来的计划。此文档将作为项目状态的快照，便于在中断后快速恢复上下文。

## 2. 项目背景与总体方案回顾

**目标**: 为 XipiLabs 旗下所有产品（如 `taleweave.xipilabs.com`, `flowweaver.xipilabs.com`）实现统一的单点登录（SSO）功能。用户在官网（`www.xipilabs.com`）登录一次后，访问其他子域产品时应自动保持登录状态，无需重复认证。

**总体方案**: 采用“DIY 自建”方案，以 `www.xipilabs.com` (即 `hero2` 项目) 作为**统一认证中心**。

*   **认证中心 (`hero2` 项目)**: 负责所有登录 UI、处理认证回调、管理用户数据库、签发 JWT 并设置跨域 Cookie。
*   **网关 (`xipilabs-gateway`)**: 拦截所有对产品应用的请求，校验 JWT，并将用户信息注入请求头后转发给后端。
*   **产品应用 (`TaleWeave`, `FlowWeave`)**: 后端移除认证逻辑，信任网关注入的请求头；前端在未登录时重定向到认证中心。

详细方案请参考 `docs/SSO实施计划.md`。

## 3. 实施状态：已完成 (部分完成，Hero2 项目构建受阻)

所有 SSO 相关的核心开发、改造和配置工作均已完成，但 `hero2` 项目的生产环境部署遇到了持续的构建问题。

*   **阶段一：准备与配置 (已完成)**
    *   已生成并统一了用于签发和校验的 `JWT_SECRET`。
    *   已在 Google Cloud Console 中为新的认证中心配置了 OAuth 客户端。

*   **阶段二：构建统一认证中心 (已完成)**
    *   `hero2` 项目已具备完整的**Google 登录**和**短信登录**功能。
    *   `hero2` 项目已实现将用户 `display_name` (用户名) 和 `avatar_url` (头像) 保存至 `auth_identities` 表的逻辑。
    *   `hero2` 项目新增了 `/api/me` 接口，用于向前端提供当前登录用户的信息。
    *   `hero2` 项目新增了全局 `Header` 组件，可动态显示用户的登录状态（用户名、头像）或“登录”按钮。

*   **阶段三：升级网关 (已完成)**
    *   `xipilabs-gateway` 项目中已创建了一个新的 `auth_service` 容器，专门用于验证 `auth-token`。
    *   `xipilabs-gateway` 的 Nginx 配置已更新，使用 `auth_request` 模块来调用 `auth_service`，实现了对后端应用的请求拦截和保护。

*   **阶段四：改造产品应用 (已完成)**
    *   `TaleWeave` 后端已改造完毕，完全移除旧的认证逻辑，改为信任由网关注入的 `X-User-ID` 请求头。
    *   `TaleWeave` 前端已移除所有本地登录页面和组件，API 请求失败时会自动跳转到中央登录页，登出按钮也已指向中央登出接口。

*   **环境与网络配置 (已完成)**
    *   已为 `hero2` 和 `xipilabs-gateway` 项目的 `deploy.yml` 文件添加了处理生产环境变量 (GitHub Secrets) 的逻辑。
    *   已为 `TaleWeave`, `hero2`, `xipilabs-gateway` 三个项目的所有 `docker-compose.yml` 文件配置了统一的外部共享网络 `xipi-network`，解决了跨项目容器通信问题。

## 4. 遇到的问题与解决方案 (Hero2 项目构建阶段)

在尝试部署 `hero2` (门户) 项目时，遇到了多次构建失败，主要集中在 Docker 镜像构建阶段的 TypeScript 编译错误。这些错误暴露出初始代码在依赖管理、类型定义、Prisma API 使用、Next.js Cookie API 使用以及阿里云 SDK 调用等方面存在多处缺陷。

*   **`Module not found: Can't resolve '@alicloud/openapi-client'`**：
    *   **原因**：`@alicloud/openapi-client` 是 `dysmsapi20170525` 的子依赖，但未作为直接依赖声明。
    *   **修复**：通过 `pnpm add @alicloud/openapi-client` 显式添加为直接依赖。
*   **`Type error: Could not find a declaration file for module 'jsonwebtoken'`**：
    *   **原因**：`jsonwebtoken` 库缺少 TypeScript 类型定义文件。
    *   **修复**：通过 `pnpm add --save-dev @types/jsonwebtoken` 安装类型定义。
*   **`Type error: Module '"@prisma/client"' has no exported member 'User'. Did you mean 'users'?`**：
    *   **原因**：`prisma generate` 命令未在构建前执行，导致 `@prisma/client` 类型文件未生成或生成不正确。同时，Prisma 在此项目中生成了非标准的、小写的模型类型名（如 `users` 而非 `User`）。
    *   **修复**：
        1.  修改 `package.json` 的 `build` 脚本，确保 `prisma generate` 在 `next build` 前运行。
        2.  将代码中对 Prisma 模型类型的引用从 `User` 修正回 `users`（以及 `AuthIdentity` 修正回 `auth_identities`），以匹配实际生成的类型。
*   **`PrismaConfigEnvError: Missing required environment variable: DATABASE_URL`**：
    *   **原因**：`prisma generate` 在 Docker 构建阶段执行时，缺少 `DATABASE_URL` 环境变量。
    *   **修复**：修改 `Dockerfile` 接收 `DATABASE_URL` 构建参数，并在 `deploy.yml` 中传入一个假的 `DATABASE_URL` 值，以满足 `prisma generate` 的语法要求。
*   **`Type error: Property 'set' does not exist on type 'Promise<ReadonlyRequestCookies>'`**：
    *   **原因**：在 Next.js Route Handler 中，错误地尝试通过 `cookies().set()` 来设置 Cookie。`cookies()` 返回的对象是只读的。
    *   **修复**：修改 `google/route.ts` 和 `phone/verify/route.ts`，采用正确的 Next.js 模式：先创建 `NextResponse` 对象，然后通过 `response.cookies.set()` 在响应上设置 Cookie。
*   **`Type error: Cannot find name 'int'.`**：
    *   **原因**：在 TypeScript 代码中错误地使用了 `int` 作为类型注解。
    *   **修复**：将 `int` 修正为 `number`。
*   **`Type error: 'response.body' is possibly 'undefined'.`**：
    *   **原因**：在调用阿里云 SDK 后，未对 `response.body` 进行空值检查就直接访问其属性。
    *   **修复**：添加 `if (!response.body)` 检查。
*   **`Type error: 'prisma' is possibly 'undefined'.`**：
    *   **原因**：`src/lib/prisma.ts` 中用于在开发环境缓存 `PrismaClient` 实例的复杂逻辑，导致 TypeScript 编译器在生产构建中无法正确推断 `prisma` 对象的类型。
    *   **修复**：**（待执行）** 计划彻底简化 `src/lib/prisma.ts` 文件，移除复杂的缓存逻辑，直接导出 `new PrismaClient()`，以消除类型推导歧义。

## 5. 阶段五：部署与端到端测试 (修订后的安全部署方案)

*   **当前状态**：`hero2` 项目的构建仍在进行中，尚未成功部署。
*   **修订后的部署策略**：鉴于 `hero2` 项目在构建阶段暴露出的诸多问题，我们决定暂停直接在生产环境进行测试，并采纳一个更严谨、更注重质量保障的流程。
*   **新流程步骤**：
    1.  **彻底的代码审查 (Hero2 项目)**：AI Coder 将对 `hero2` 项目中所有修改过的文件进行一次手动、逐行、极其细致的审查，确保所有潜在错误都被发现并修正。
    2.  **本地构建验证 (Hero2 项目)**：审查完成后，用户将在本地执行 `docker build` 命令，验证代码能够成功构建。
    3.  **功能测试指导 (Hero2 项目)**：如果本地构建成功，AI Coder 将提供详细步骤，指导用户在本地运行 `hero2` 项目，并手动测试 Google 登录和手机号登录/验证码等核心功能。
    4.  **其他项目 (TaleWeave, xipilabs-gateway) 的同等审查**：只有在 `hero2` 项目确认稳定后，才会对 `TaleWeave` 和 `xipilabs-gateway` 采取同样的严谨审查和本地测试流程。
    5.  **最终部署**：所有三个项目都通过严格审查和本地测试后，才会再次尝试生产环境的部署，并严格按照 `门户 -> TaleWeave -> 网关` 的顺序进行。
