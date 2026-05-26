# Self-learning-AI / HDWS

层级子空间路由（Hierarchical Dynamic Weight Subspaces）原型。

## 文件说明

| 文件 | 作用 |
|------|------|
| `subspace.py` | 子空间容器，带 anchor 与知识权重 |
| `space_router.py` | 空间路由层，按语义向量递归选子空间 |
| `verify.py` | 本地验证脚本 |
| `requirements.txt` | Python 依赖 |

## 本地验证

```bash
pip install -r requirements.txt
python verify.py
```

预期：tech 查询 → `apple_company`，science 查询 → `apple_fruit`，forward 输出 shape 不变且与输入不同。

## 推送到 GitHub

仓库：<https://github.com/AndCreateStars/Self-learning-AI>

```powershell
# 方式 1：一键脚本（推荐）
.\scripts\sync-and-push.ps1 -Message "你的提交说明"

# 方式 2：手动
git pull origin main --rebase
git add .
git commit -m "你的提交说明"
git push origin main
```

若 `Connection was reset`，见下方「网络问题」。

## 网络问题

Git 推送失败时按顺序尝试：

1. 重试 2～3 次（网络偶发不稳定）
2. 配置系统代理后重试
3. 改用 SSH：`git remote set-url origin git@github.com:AndCreateStars/Self-learning-AI.git`
4. 兜底：在 GitHub 网页 **Add file → Upload files** 上传改动

**切勿**把 Token 写进 `git remote` URL，用 Git Credential Manager 或环境变量 `GITHUB_TOKEN`。

## 后期开发约定

- 改代码后先本地跑 `python verify.py`
- 确认通过再提交推送
- 对 Cursor 说「帮我上传到 GitHub」即可，会按 `.cursor/rules/github-upload.mdc` 执行
