from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

@mcp.tool()
async def get_alerts(state: str) -> str:
    """
    获取美国某个州当前生效的天气预紧信息。
    
    Args:
        state (str): 两个字母的美国州代码 (如 "CA", "NY")
    """
    url = f'{NWS_API_BASE}/alerts/active/area/{state}'
    data = await make_nws_requests(url)
    
    if not data or "features" not in data:
        return "无法获取预警信息或未找到相关数据。"
    
    if not data["features"]:
        return "该州当前没有生效的天气预警。"
    
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """
    获取指定经纬度的天气预报。
    
    Args:
        latitude (float): 纬度
        longitude (float): 经度
    Returns:
        str: 天气预报信息
    """
    url = f'{NWS_API_BASE}/points/{latitude},{longitude}'
    data = await make_nws_requests(url)
    
    if not data or "properties" not in data:
        return "无法获取该地点的预报数据。"
    
    forecast_url = data["properties"]["forecast"]
    forecast_data = await make_nws_requests(forecast_url)
    
    if not forecast_data or "properties" not in forecast_data:
        return "无法获取详细的预报信息。"
    
    periods = forecast_data["properties"]["periods"]
    
    # 遍历接下来的5个预报周期（例如：今天下午、今晚、明天...）
    forecasts = []
    for period in periods[:5]:
        forecasts.append(format_forecast(period))
    return "\n---\n".join(forecasts)


async def make_nws_requests(url: str) -> dict[str, Any] | None:
    """
    一个通用的异步函数，用于向NWS API 发起请求并处理常见的错误。
    
    Args:
        url (str): 完整URL
    Returns:
        dict[str, Any] | None: 成功时返回解析后的 JSON 字典，失败时返回 None
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """
    将单个天气预警的 JSON 数据格式化为人类可读的字符串。
    
    Args:
        feature (dict): 单个天气预警的 JSON 字典
    Returns:
        str: 格式化后的字符串
    """
    props = feature["properties"]
    # 使用 .get() 方法安全地访问字典键，如果键不存在则返回默认值，避免程序出错
    return f"""
事件: {props.get('event', '未知')}
区域: {props.get('areaDesc', '未知')}
严重性: {props.get('severity', '未知')}
描述: {props.get('description', '无描述信息')}
指令: {props.get('instruction', '无具体指令')}
"""

def format_forecast(period: dict) -> str:
    """
    将单个预报周期的 JSON 数据格式化为人类可读的字符串。
    
    Args:
        period (dict): 单个预报周期的 JSON 字典
    Returns:
        str: 格式化后的字符串
    """
    return f"""
{period['name']}:
温度: {period['temperature']}°{period['temperatureUnit']}
风力: {period['windSpeed']} {period['windDirection']}
预报: {period['detailedForecast']}
"""

if __name__ == "__main__":
    mcp.run(transport="stdio")