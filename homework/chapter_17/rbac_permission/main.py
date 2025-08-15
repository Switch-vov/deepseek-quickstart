import functools
from flask import Flask, jsonify, request, g

# 1. 模拟数据和配置
# ==============================================================================

# 定义权限：角色 -> {权限集合}
# 在真实应用中，这些数据会存储在数据库中。
PERMISSIONS: dict[str, set[str]] = {
    "admin": {"item:read", "item:create", "item:edit", "item:delete", "user:read"},
    "developer": {"item:read", "item:create", "item:edit"},
    "viewer": {"item:read"}
}

# 模拟用户数据库：用户名 -> {用户信息}
USERS: dict[str, dict] = {
    "alice": {"username": "alice", "role": "admin", "disabled": False},
    "bob": {"username": "bob", "role": "developer", "disabled": False},
    "charlie": {"username": "charlie", "role": "viewer", "disabled": False},
    "dave_disabled": {"username": "dave_disabled", "role": "developer", "disabled": True},
}

# 模拟 API Keys：API Key -> 用户名
# 在真实应用中，API Keys 应该是安全的哈希值，并存储在数据库中。
API_KEYS: dict[str, str] = {
    "SECRET_API_KEY_ALICE": "alice",
    "SECRET_API_KEY_BOB": "bob",
    "SECRET_API_KEY_CHARLIE": "charlie",
    "SECRET_API_KEY_DAVE": "dave_disabled",
}


# 2. RBAC 授权装饰器 (Authorization Decorator)
# ==============================================================================

def rbac_required(required_permission: str):
    """
    一个装饰器工厂，用于创建检查特定权限的装饰器。
    它负责完整的认证和授权流程。
    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # --- 认证 (Authentication) ---
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                return jsonify({"error": "Missing API Key"}), 401

            username = API_KEYS.get(api_key)
            if not username:
                return jsonify({"error": "Invalid API Key"}), 401

            user = USERS.get(username)
            if not user or user.get("disabled", False):
                return jsonify({"error": "Invalid or disabled user"}), 401

            # 将用户信息存储在 g 对象中，供路由函数后续使用
            g.user = user

            # --- 授权 (Authorization) ---
            user_role = user.get("role")
            if not user_role or required_permission not in PERMISSIONS.get(user_role, set()):
                return jsonify({
                    "error": "Permission denied",
                    "required_permission": required_permission
                }), 403

            # 如果认证和授权都通过，则执行被装饰的原始函数
            return f(*args, **kwargs)

        return wrapper

    return decorator


# 3. Flask 应用和路由
# ==============================================================================

app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True  # 使 JSON 输出更美观


@app.route("/items/", methods=["GET"])
@rbac_required("item:read")
def read_items():
    """
    读取物品列表。
    需要权限: 'item:read'
    允许角色: viewer, developer, admin
    """
    # 我们可以从 g 对象中获取用户信息
    current_user = g.user
    return jsonify({
        "message": f"User '{current_user['username']}' is reading items.",
        "items": ["Item 1", "Item 2"]
    })


@app.route("/items/", methods=["POST"])
@rbac_required("item:create")
def create_item():
    """
    创建新物品。
    需要权限: 'item:create'
    允许角色: developer, admin
    """
    current_user = g.user
    return jsonify({
        "message": f"Item created by user '{current_user['username']}' with role '{current_user['role']}'."
    }), 201


@app.route("/items/<int:item_id>", methods=["DELETE"])
@rbac_required("item:delete")
def delete_item(item_id):
    """
    删除物品。
    需要权限: 'item:delete'
    允许角色: admin
    """
    current_user = g.user
    return jsonify({
        "message": f"Item {item_id} has been deleted by admin '{current_user['username']}'."
    })


# 一个不需要特定权限，但需要有效登录的端点
@app.route("/users/me", methods=["GET"])
@rbac_required("user:read")  # 假设查看自己信息也需要一个基本权限
def read_current_user():
    """
    获取当前用户信息。
    需要权限: 'user:read' (只有 admin 有)
    """
    # 装饰器已经将用户信息放入 g.user
    return jsonify({"user_info": g.user})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
