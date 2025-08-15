# rbac权限控制项目

[TOC]

## 安装 uv 包管理器

打开终端，运⾏以下命令（uv 是⼀个极速的 Python 包管理器。）

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

注意：安装完成后，请务必重启终端，以确保uv 命令能够被系统识别。

## 创建并设置项目依赖

```shell
# 为项目创建一个名为 rbac_permission 的新目录
uv init rbac_permission
cd rbac_permission
# 创建并激活虚拟环境(用于隔离项目依赖)
uv venv
source .venv/bin/activate
# 安装项目所需的依赖包
uv add Flask
```

## 启动服务

```bash
flask --app main run
```

服务将运行在 `http://127.0.0.1:5000`。

整体项目文件在：[main.py](https://github.com/Switch-vov/deepseek-quickstart/blob/main/homework/chapter_17/rbac_permission/main.py)

## 使用 `curl` 进行测试

* **测试角色 `viewer` (charlie)**: 他只能读取 `items`。
```bash
# 成功 - 读取 items
curl -X GET http://127.0.0.1:5000/items/ -H "X-API-Key: SECRET_API_KEY_CHARLIE"
# 返回: { "items": [ "Item 1", "Item 2" ], "message": "User 'charlie' is reading items." }

# 失败 - 尝试创建 item
curl -X POST http://127.0.0.1:5000/items/ -H "X-API-Key: SECRET_API_KEY_CHARLIE"
# 返回: { "error": "Permission denied", "required_permission": "item:create" }
```

* **测试角色 `developer` (bob)**: 他可以读、写 `items`，但不能删除。
```bash
# 成功 - 创建 item
curl -X POST http://127.0.0.1:5000/items/ -H "X-API-Key: SECRET_API_KEY_BOB"
# 返回: { "message": "Item created by user 'bob' with role 'developer'." }

# 失败 - 尝试删除 item
curl -X DELETE http://127.0.0.1:5000/items/123 -H "X-API-Key: SECRET_API_KEY_BOB"
# 返回: { "error": "Permission denied", "required_permission": "item:delete" }
```

* **测试角色 `admin` (alice)**: 她拥有很多权限。
```bash
# 成功 - 删除 item
curl -X DELETE http://127.0.0.1:5000/items/123 -H "X-API-Key: SECRET_API_KEY_ALICE"
# 返回: { "message": "Item 123 has been deleted by admin 'alice'." }
```

* **测试无效的 API Key**:
```bash
curl -X GET http://127.0.0.1:5000/items/ -H "X-API-Key: INVALID_KEY"
# 返回: { "error": "Invalid API Key" }
```
