# Repository Guidelines

## Project Structure & Module Organization
The stack is orchestrated from `docker-compose.yml`, which wires TLS termination (Nginx), JWT verification, and certificate automation on `xipi-network`. Runtime code sits in `auth_service/` (Node.js Express app) while reverse-proxy rules live in `nginx_config/`. Certificates and ACME challenges persist under `data/certbot/` so renewals survive container rebuilds. Reference materials for the SSO rollout are in `docs/`; skim them before touching authentication flows.

## Build, Test, and Development Commands
Run `npm install` inside `auth_service/` once to pull dependencies. During local dev, `npm start` (or `node index.js`) spins up the verifier on port 3000. `docker compose up -d gateway-nginx auth_service` launches the edge stack; add `--build` after dependency or config changes. Use `docker compose logs -f auth_service` for verification traces. Renew TLS with `docker compose run --rm certbot renew` and ensure the `xipi-network` already exists (`docker network create xipi-network`).

## Coding Style & Naming Conventions
Follow the existing four-space indentation and prefer `const`/`let` over `var`. Keep Express middleware lean, log in structured sentences, and avoid swallowing JWT errors. Environment variables are SCREAMING_SNAKE_CASE (e.g., `JWT_SECRET`) and are injected either via `.env` or Compose; never hard-code secrets. New Nginx snippets should use lowercase, hyphenated filenames such as `sso-upstream.conf` and share the `xipi_` prefix for upstream names.

## Testing Guidelines
There is no formal test harness yet; rely on reproducible manual checks. Start only the auth service (`npm start`) and hit `curl -v http://localhost:3000/verify --cookie "auth-token=<jwt>"` to confirm the status code and headers. When running through Nginx, confirm the proxy adds `X-User-*` headers by inspecting upstream logs. Record edge cases (expired token, issuer mismatch, missing cookie) in the PR description until automated tests exist.

## Commit & Pull Request Guidelines
Use the Conventional Commits style found in git history: `<type>(<scope>): <imperative summary>` such as `feat(auth): tighten issuer check`. Each PR should describe the motivation, config changes, and manual verification steps (commands/output). Link related docs or tickets and include screenshots for Nginx/UI updates. Keep branches rebased onto main before review and avoid bundling certbot updates with application logic.

## Security & Configuration Tips
Always validate that `JWT_SECRET` in the container matches the issuer that signs tokens; a mismatch produces 401s at the edge. Treat `data/certbot/` as sensitive—do not commit subdirectories. When editing Nginx configs, reload via `docker compose exec gateway-nginx nginx -s reload` instead of restarting, and double-check that `proxy_set_header` directives continue forwarding `X-User-*` from the auth service.


- 当我发现问题、bug、报错，你先要分析原因（必要时查看代码和日志），然后向我解释原因，并提出修改思路（不要发给我大量的代码），经过我运行后再进行修改
- 未经我允许不能删除数据库里的数据，不要运行docker compose down --volumes，这会导致数据完全丢失
- 当我提出需求，你先给出修改思路（但不要发给我大量代码），我同意后你方可修改代码。未经过我的允许不得擅自修改代码
- When proposing code changes, only describe the implementation idea and expected outcome. Do not show the user large blocks of code unless they ask for it.
- All programs must be executed inside the appropriate Docker container, not on the host machine.
- 你可以执行命令启动Docker和运行其他docker命令，也可以运行其他shel命令,不需要经过我的允许
- 请使用中文跟我沟通
- 不允许你在编码时自定义异常类型，包装其他异常，需要根据原始异常的错误来显示错误日志
- 在修改.env或其他重要配置文件（尤其是文件不在 git 上，本地仅一份）之前要先进行备份
- 编码时需要注意，我们不需要能够处理各种情况的所谓“健壮”代码，那只会为程序埋下隐患，我们需要实现程序设计逻辑的精准代码，如果实际运行的逻辑不是我们设想的，那就应该报错，而且不是让代码适应所有可能的情况
- 进行 docker 配置或执行（包括让我执行） docker 命令的时候，需要考虑这些操作是否会导致数据丢失，如果会导致丢失，需要提前跟我说明
- Do not commit changes unless the user explicitly asks. When there are pending changes, inform the user and wait for their instruction to commit.
- 请使用中文跟我沟通