import os
import aiohttp
import asyncio
import base64
import json
from astrbot.api.all import *

PLUGIN_DIR = os.path.join('data', 'plugins', 'astrbot_plugin_violationquery')
FIRST_API_URL = base64.b64decode("aHR0cDovL2FwaS5vY29hLmNuL2FwaS9xcWN3Zy9sb2dpbi5waHA=").decode()

@register("violation_query", "知鱼", "查询QQ违规记录的插件", "1.0")
class ViolationQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
    async def _query_first_api(self, api_url: str):
        """查询第一个接口获取URL和code"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data  # 返回完整的JSON数据
                    else:
                        return None
        except Exception as e:
            self.context.logger.error(f"第一个API查询失败: {str(e)}")
            return None
    
    async def _query_violation_data(self, code: str):
        """查询完整的违规记录数据链"""
        try:
            async with aiohttp.ClientSession() as session:
                # 第二步：使用code获取ticket和uin
                response2 = await session.get(f"http://api.ocoa.cn/api/qqcwg/login.php?type=1&code={code}")
                text2 = await response2.text()
                json_data2 = json.loads(text2)
                
                if json_data2.get("data") and json_data2["data"].get("ticket") and json_data2["data"].get("uin"):
                    ticket = json_data2["data"]["ticket"]
                    uin = json_data2["data"]["uin"]
                    
                    # 第三步：获取openid和minico_token
                    response3 = await session.get(f"http://api.ocoa.cn/api/qqcwg/safety.php?type=1&ticket={ticket}")
                    text3 = await response3.text()
                    json_data3 = json.loads(text3)
                    
                    if json_data3.get("openid") and json_data3.get("minico_token"):
                        openid = json_data3["openid"]
                        minico_token = json_data3["minico_token"]
                        
                        # 第四步：获取最终的违规记录
                        response4 = await session.get(f"http://api.ocoa.cn/api/qqcwg/safety.php?type=2&id={openid}&token={minico_token}&uin={uin}")
                        text4 = await response4.text()
                        
                        full_content = f"{text4}\n因考虑到霸屏缘故 违规内容只返回十条"
                        return full_content
                    else:
                        return "未获取到openid或minico_token"
                else:
                    return "未获取到ticket或uin"
        except Exception as e:
            self.context.logger.error(f"违规记录查询失败: {str(e)}")
            return f"查询过程中发生错误: {str(e)}"
    
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        """群聊消息处理器"""
        msg = event.message_str.strip()
        
        if msg == "查违规":
            # 第一步：获取第一个接口的数据
            yield event.chain_result([Plain(text="正在获取验证码链接...")])
            first_data = await self._query_first_api(FIRST_API_URL)
            
            if first_data is None:
                yield event.chain_result([Plain(text="获取验证码链接失败")])
                return
            
            # 发送URL链接给用户
            url = first_data.get("url", "")
            code = first_data.get("code", "")
            
            if url and code:
                yield event.chain_result([Plain(text=f"验证码链接: {url}")])
                yield event.chain_result([Plain(text=f"获取到的code: {code}")])
                
                # 等待15秒
                yield event.chain_result([Plain(text="等待15秒后查询最终结果...")])
                await asyncio.sleep(15)
                
                # 第二步及后续：查询完整的违规记录
                yield event.chain_result([Plain(text="正在查询最终结果...")])
                final_result = await self._query_violation_data(code)
                
                yield event.chain_result([Plain(text=final_result)])
            else:
                yield event.chain_result([Plain(text="获取到的数据不完整")])