import os
import aiohttp
import time
import base64
import json
from astrbot.api.all import *

PLUGIN_DIR = os.path.join('data', 'plugins', 'astrbot_plugin_violationquery')
VIOLATION_API_URL = base64.b64decode("aHR0cDovL2FwaS5vY29hLmNuL2FwaS9xcWN3Zy9sb2dpbi5waHA/cXE9").decode()

COOLDOWN_TIME = 20  # 冷却时间20秒
#请勿修改冷却时间 大量频繁查询会导致查询失败 最低可保持在15秒内

@register("violation_query", "知鱼", "查询QQ违规记录的插件", "1.0")
class ViolationQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.last_query_time = 0 
    
    async def _query_api(self, api_url: str, qq: str = ""):     
        try:
            current_time = time.time()
            if current_time - self.last_query_time < COOLDOWN_TIME:
                remaining = COOLDOWN_TIME - (current_time - self.last_query_time)
                return f"查询过于频繁 请等待 {remaining:.1f} 秒后再试"
            
            self.last_query_time = current_time
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url + qq) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "url" in data:
                            # 将url中的com替换为大写Com
                            modified_url = data["url"].replace("com", "Com")
                            return modified_url
                        return "未获取到违规记录链接"
                    else:
                        return f"查询失败 状态码：{response.status}"
        except Exception as e:
            self.context.logger.error(f"违规查询API失败: {str(e)}")
            return "查询违规记录时发生错误"
    
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        """群聊消息处理器"""
        msg = event.message_str.strip()
        
        # 查询菜单指令
        if msg == "查询菜单":
            menu = f"""可用查询指令：
查违规 [QQ号] - 查询QQ违规记录
注意：每次查询后有{COOLDOWN_TIME}秒冷却时间"""
            yield event.chain_result([Plain(text=menu)])
            return
        
        # 查违规指令
        elif msg.startswith("查违规"):
            parts = msg.split()
            if len(parts) >= 2 and parts[1].isdigit():
                qq_number = parts[1]
                violation_url = await self._query_api(VIOLATION_API_URL, qq_number)
                yield event.chain_result([Plain(text=violation_url)])
            else:
                yield event.chain_result([Plain(text="请输入要查询的QQ号\n例如：查违规 123456")])
