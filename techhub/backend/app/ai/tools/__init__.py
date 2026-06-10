"""
AI 工具注册与管理
"""
from functools import wraps
from flask_jwt_extended import get_jwt_identity
from app.models import User

# 工具注册表
_registered_tools = {}


def register_tool(name, description, parameters=None):
    """注册工具的修饰器"""
    def decorator(func):
        _registered_tools[name] = {
            'name': name,
            'description': description,
            'parameters': parameters or {},
            'func': func
        }
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_all_tools():
    """获取所有注册的工具定义（用于LLM function calling）"""
    tools = []
    for tool in _registered_tools.values():
        # 构建参数定义
        properties = {}
        required = []
        for param_name, param_info in tool['parameters'].items():
            prop = {
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", "")
            }
            if "enum" in param_info:
                prop["enum"] = param_info["enum"]
            properties[param_name] = prop
            if param_info.get("required", False):
                required.append(param_name)
        
        tools.append({
            'type': 'function',
            'function': {
                'name': tool['name'],
                'description': tool['description'],
                'parameters': {
                    'type': 'object',
                    'properties': properties,
                    'required': required
                }
            }
        })
    return tools


def execute_tool(name, arguments, user_id=None):
    """执行指定工具"""
    if name not in _registered_tools:
        return {'success': False, 'error': f'工具 {name} 不存在'}
    
    tool = _registered_tools[name]
    try:
        result = tool['func'](user_id=user_id, **arguments)
        return {'success': True, 'data': result}
    except Exception as e:
        import traceback
        return {'success': False, 'error': str(e), 'traceback': traceback.format_exc()}


def get_current_user(user_id):
    """获取当前用户"""
    if not user_id:
        return None
    return User.query.get(user_id)


# 导入所有工具模块（自动注册）
def init_tools():
    """初始化所有工具"""
    from app.ai.tools import query_tools, analysis_tools, action_tools
    # 工具模块导入时会自动通过 @register_tool 注册
    pass
