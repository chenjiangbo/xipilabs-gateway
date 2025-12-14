# 项目架构总览

本文档旨在概述 TaleWeave 生态系统中的各个项目，描述其核心功能及技术实现原理。

---

## 1. 总路由 (`xipilabs-gateway`) - `/Users/xipilabs/dev/xipilabs-gateway`

### 项目概述

此项目是整个 TaleWeave 服务的统一入口网关，基于 Nginx 构建。它负责接收所有外部流量，并根据域名和路径将请求智能转发到后端的不同服务。其设计的核心是**一个集中的、非侵入式的单点登录（SSO）系统**。

### 核心功能与 SSO 实现原理

- **反向代理与路由转发**: 作为所有后端服务的单一入口点，根据 `nginx_config/xipilabs.conf` 中的规则，将 `taleweave.xipilabs.com` 的请求转发至 TaleWeave 后端，将 `www.xipilabs.com` 的请求转发至门户网站等。

- **集中式 SSO 认证**: 网关通过 `auth_request` 机制实现对所有后端服务的统一认证，具体流程如下：
    1.  **拦截请求**: 当用户访问一个受保护的路径（例如 `/api/v1/tales`）时，Nginx 会暂停该请求。
    2.  **认证子请求**: Nginx 向内部的 `/verify` 端点发起一个认证子请求。此请求由一个专门的轻量级 Node.js 应用 `auth_service` 处理。
    3.  **JWT 验证**: `auth_service` 负责从请求的 Cookie 中提取 `auth-token` (JWT)，并对其进行解密和有效性验证（例如，检查签名和过期时间）。
    4.  **处理认证成功**: 如果 JWT 有效，`auth_service` 返回 `200 OK` 状态码，并在其响应头中附带用户信息，如 `X-User-ID`, `X-User-Email`。Nginx 捕获这些信息，并将它们作为新的请求头（`X-User-ID` 等）注入到原始的用户请求中，然后将请求放行到最终的后端业务服务（如 TaleWeave API）。后端服务因此可以完全信任这些请求头，无需再做身份验证。
    5.  **处理认证失败**: 如果 JWT 无效或不存在，`auth_service` 返回 `401 Unauthorized`。Nginx 捕获此状态码，并触发一个内部重定向，将用户浏览器重定向到统一登录页面 `https://www.xipilabs.com/login`，同时附带一个 `redirect_url` 参数，以便登录成功后能返回原始页面。

- **SSL 终端**: 集中处理 `*.xipilabs.com` 的通配符 SSL 证书，为所有下游服务提供 HTTPS 支持。

### 技术实现

- **Nginx**: 核心反向代理服务器。`nginx_config/xipilabs.conf` 中通过 `auth_request` 指令、`error_page` 重定向和 `auth_request_set` 指令实现了完整的 SSO 流程。
- **Node.js (`auth_service`)**: 一个专门用于验证 JWT 的微服务。它被 Nginx 作为认证子请求的目标调用，是 SSO 体系中的决策点。它的唯一职责是校验令牌并返回用户信息，实现了认证逻辑与业务逻辑的完全解耦。
- **Docker Compose**: `docker-compose.yml` 文件负责编排 Nginx 服务和 `auth_service`，并将它们连接到同一个 Docker 网络中，确保服务间的顺畅通信。

---

## 2. TaleWeave (核心产品) - `/Users/xipilabs/dev/TaleWeave`

### 项目概述

这是 TaleWeave 的核心业务系统，一个功能完善的 Monorepo 项目。它包含了用于生成AI绘本的后端服务、Web前端应用以及所有必要的依赖服务。其架构设计旨在通过异步任务处理来支持计算密集型的AI内容生成。

### 核心功能

- **AI 绘本生成**: 用户提供一个核心创意（prompt），系统通过多阶段的 AI 调用，生成包含故事文本、插图和旁白音频的完整绘本。
- **异步任务处理**: 绘本的生成是一个耗时的过程。系统接受请求后，立即返回一个任务ID，并通过 Celery 任务队列在后台异步执行生成步骤，客户端可以轮询任务状态。
- **媒体资源管理**: 生成的图片、音频和最终的 PDF 文件都存储在 Minio（一个 S3 兼容的对象存储服务）中。
- **用户与内容管理**: 提供 API 来管理用户、故事库、查看生成历史等。

### 技术实现

- **后端 (`apps/backend`)**:
    - **框架**: 使用 Python 的 **FastAPI** 构建，提供高性能的异步 API。
    - **异步队列**: **Celery** 作为任务队列，**Redis** 作为其消息代理（Broker），负责处理所有耗时的 AI 生成任务（如调用大语言模型、文生图、TTS等）。`docker-compose.yml` 中配置了多个 `worker` 实例来并行处理任务。
    - **数据库**: 使用 **PostgreSQL** 作为主数据库，**SQLAlchemy** 作为 ORM，**Alembic** 用于数据库结构的版本迁移。数据库模型（如 `tales`, `users`, `generation_logs`）清晰地定义了核心业务数据结构。
    - **AI 服务集成**: `requirements.txt` 表明项目集成了多个第三方 AI 服务：
        - **大语言模型 (LLM)**: `google-genai`, `openai`，用于将用户的简单想法扩展成详细的故事脚本。
        - **文本转语音 (TTS)**: `elevenlabs`, `google-cloud-texttospeech`，用于为故事生成旁白。
        - **图像生成**: 通过可配置的 API (`IMAGE_GEN_BASE_URL`) 调用，可能集成了如 Midjourney, Stable Diffusion (ComfyUI) 或 Gemini Image。
    - **对象存储**: 使用 **Minio** 库与 Minio 服务交互，上传和管理生成的媒体文件。

- **前端 (`apps/web-pc`)**:
    - **框架**: 使用 **React** 和 **Vite** 构建的现代化单页应用（SPA）。
    - **功能**: 提供用户界面，让用户可以输入故事创意、调整参数、查看自己的作品库以及监控生成进度。
    - **API 通信**: 通过 HTTP 请求与后端 FastAPI 服务交互，以创建和获取故事数据。

- **基础设施 (`docker-compose.yml`)**:
    - 使用 Docker Compose 统一管理和编排所有服务，包括 `backend`, `web`, `worker`, `postgres`, `redis`, 和 `minio`，实现了开发和生产环境的一致性。

---

## 3. 门户网站 (`Experiment/hero2/project`) - `/Users/xipilabs/dev/Experiment/hero2/project`

### 项目概述

此项目是 Xipi Labs 的官方门户网站，同时它也扮演着整个生态系统中**认证中心 (Auth Center)** 的关键角色。所有需要登录的操作最终都会汇集于此。

### 核心功能与 SSO 实现原理

- **统一登录页面**: 托管着全局唯一的登录页面 (`/login`)。所有未登录的用户都会被 `xipilabs-gateway` 重定向到这里。
- **OAuth 提供商集成**: 作为认证中心，它直接与外部 OAuth 提供商（如 Google, Apple）进行交互。它负责将用户引导至提供商的授权页面，并处理从提供商回调的授权码。
- **处理登录回调**: `api/auth/callback/*` 路径下的 API 负责处理 OAuth 回调。它们用授权码换取访问令牌，然后获取用户信息，并在数据库中创建或更新用户记录。
- **签发 JWT**: 用户信息验证成功后，该服务会使用一个全局密钥 (`JWT_SECRET`) 生成一个包含用户身份信息的 JWT（JSON Web Token），并将其写入到作用于 `*.xipilabs.com` 顶级域的 `auth-token` Cookie 中。这使得用户在访问生态系统内任何子域时，浏览器都会自动携带此 Cookie。
- **防止 CSRF 攻击**: 在发起 OAuth 请求时，会生成一个唯一的 `state` 参数，并与 `redirect_url` 一同存入 **Redis** (`oauth.ts` 模块负责此逻辑)。在处理回调时，会校验返回的 `state` 是否与存储的一致，这能有效防止跨站请求伪造攻击。校验成功后，从 Redis 中安全地取出 `redirect_url`，并将用户浏览器重定向回其最初尝试访问的页面。
- **内容展示**: 使用 `contentlayer` 管理 Markdown 文件，用于发布博客、新闻、关于页面等。

### 技术实现

- **框架**: 使用 **Next.js** 构建，支持服务端渲染（SSR）和静态站点生成（SSG），对 SEO 友好。
- **数据库与 ORM**: 使用 **Prisma** 作为 ORM 与 **PostgreSQL** 数据库交互。
- **共享数据库**: 一个关键的架构决策是，此门户网站与 `TaleWeave` 核心产品 **共享同一个数据库**。这意味着用户账户是统一的，在一个平台注册后，可以在所有产品中使用。
- **国际化**: `next-intl` 库和 `messages` 目录表明网站支持多语言（中文和英文）。
- **状态管理 (OAuth)**: 使用 **Redis** (`ioredis` 库) 来临时存储 OAuth 流程中的 `state` 参数，确保登录流程的安全性。

---

## 4. TaleWeave iOS App - `/Users/xipilabs/dev/taleweave_app`

### 项目概述

一个基于 SwiftUI 构建的原生 iOS 应用程序，为移动端用户提供了创作和阅读 AI 绘本的核心体验。

### 核心功能

- **故事创作 (`CreateStoryView.swift`)**: 提供简洁的界面让用户输入故事灵感、选择插画风格和旁白声音，然后发起创作请求。
- **语音输入 (`SpeechToTextManager.swift`)**: 集成了 iOS 的语音识别功能，允许用户通过语音输入故事创意。
- **作品库 (`MyLibraryView.swift`)**: 展示用户已创作的所有绘本，并可以查看生成状态。
- **绘本阅读器 (`StoryReaderView.swift`)**: 提供沉浸式的绘本阅读体验，可以逐页查看图片、文字和播放音频。
- **应用内购买 (`AIStoryAppPaywallView.swift`, `PurchaseManager.swift`)**: 集成了 Apple 的 StoreKit，允许用户购买积分或订阅服务以解锁更多功能。
- **用户认证 (`AuthManager.swift`)**: 管理用户登录状态，通过 `KeychainStore` 安全地存储认证凭证。

### 技术实现

- **UI 框架**: 完全使用 **SwiftUI** 构建，提供了现代且响应迅速的用户界面。
- **状态管理**: 通过自定义的 `AppState` (EnvironmentObject) 在整个应用中共享和管理全局状态，如用户信息、任务列表、导航路径等。
- **网络层 (`Networking/APIClient.swift`)**:
    - 封装了一个单例的 `APIClient` 来处理所有与后端的网络通信。
    - 定义了清晰的请求/响应数据模型（如 `CreateTalePayload`, `TaleDetailResponse`），这些模型与 `TaleWeave` 后端的 API 端点严格对应。
    - 支持通过 `Bearer Token` 进行认证的请求。所有需要授权的 API 调用都会自动在请求头中附带认证令牌。
- **API 交互**: App 直接与部署在 `xipilabs-gateway` 之后的后端 API (`/api/v1/tales`, `/api/v1/users/me` 等) 通信，以实现其所有核心功能。