import os
import aiohttp
import asyncio
import json
from astrbot.api.all import *

PLUGIN_DIR = os.path.join('data', 'plugins', 'astrbot_plugin_violationquery')
FIRST_API_URL = "http://api.ocoa.cn/api/qqcwg/login.php"
LOGIN_API_URL = "http://api.ocoa.cn/api/qqcwg/login.php?type=1"
SAFETY_API_URL = "http://api.ocoa.cn/api/qqcwg/safety.php?type=1"
FINAL_API_URL = "http://api.ocoa.cn/api/qqcwg/safety.php?type=2"

@register("violation_query", "知鱼", "查询QQ违规记录的插件", "1.0")
class ViolationQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
    async def _query_first_api(self, api_url: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data  
                    else:
                        return None
        except Exception as e:
            self.context.logger.error(f"第一个API查询失败: {str(e)}")
            return None
    
    async def _query_violation_data(self, code: str):
        try:
            async with aiohttp.ClientSession() as session:
                response2 = await session.get(f"{LOGIN_API_URL}&code={code}")
                text2 = await response2.text()
                json_data2 = json.loads(text2)
                
                if json_data2.get("data") and json_data2["data"].get("ticket") and json_data2["data"].get("uin"):
                    ticket = json_data2["data"]["ticket"]
                    uin = json_data2["data"]["uin"]
                    
                    response3 = await session.get(f"{SAFETY_API_URL}&ticket={ticket}")
                    text3 = await response3.text()
                    json_data3 = json.loads(text3)
                    
                    if json_data3.get("openid") and json_data3.get("minico_token"):
                        openid = json_data3["openid"]
                        minico_token = json_data3["minico_token"]
                         
                        response4 = await session.get(f"{FINAL_API_URL}&id={openid}&token={minico_token}&uin={uin}")
                        text4 = await response4.text()
                        
                        full_content = f"{text4}\n因考虑到霸屏缘故 违规内容只返回十条"
                        return full_content
                    else:
                        return "未确认查询失败"
                else:
                    return "未确认查询失败"
        except Exception as e:
            self.context.logger.error(f"违规记录查询失败: {str(e)}")
            return f"查询过程中发生错误: {str(e)}"
    
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        msg = event.message_str.strip()
        
        if msg in ["查违规", "违规查询"]:         
            first_data = await self._query_first_api(FIRST_API_URL)
            
            if first_data is None:
                yield event.chain_result([Plain(text="获取验证码链接失败")])
                return
           
            url = first_data.get("url", "")
            code = first_data.get("code", "")
            
            if url and code:
                yield event.chain_result([Plain(text=f"请在15秒内点击下方链接完成确认: \n{url}")])
                
                await asyncio.sleep(15)
                
                final_result = await self._query_violation_data(code)
                
                yield event.chain_result([Plain(text=final_result)])
            else:
                yield event.chain_result([Plain(text="获取到的数据不完整")])