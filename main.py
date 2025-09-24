import os
import aiohttp
import asyncio
import base64
import json
from urllib.parse import quote
from astrbot.api.all import *

PLUGIN_DIR = os.path.join('data', 'plugins', 'astrbot_plugin_violationquery')
FIRST_API_URL = base64.b64decode("aHR0cDovL2FwaS5vY29hLmNuL2FwaS9xcWN3Zy9sb2dpbi5waHA=").decode()
SECOND_API_URL = base64.b64decode("aHR0cDovL2FwaS5vY29hLmNuL2FwaS9xcWN3Zy9sb2dpbi5waHA=").decode()
THIRD_API_URL = base64.b64decode("").decode()

@register("violation_query", "知鱼", "查询QQ违规记录的插件", "1.0")
class ViolationQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
    async def _query_first_api(self, code1: str):
        """查询第一个接口获取ticket和uin"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{FIRST_API_URL}{quote(code1)}") as response2:
                    text2 = await response2.text()
                    json内容2 = json.loads(text2)
                    
                    if json内容2['data'] and json内容2['data']['ticket'] and json内容2['data']['uin']:
                        ticket = json内容2['data']['ticket']
                        uin = json内容2['data']['uin']
                        return {'ticket': ticket, 'uin': uin}, None
                    return None, "获取ticket和uin失败"
        except Exception as e:
            self.context.logger.error(f"第一个API查询失败: {str(e)}")
            return None, f"第一个接口查询失败: {str(e)}"
    
    async def _query_second_api(self, ticket: str):
        """查询第二个接口获取openid和minico_token"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{SECOND_API_URL}{quote(ticket)}") as response3:
                    text3 = await response3.text()
                    json内容3 = json.loads(text3)
                    
                    if json内容3['openid'] and json内容3['minico_token']:
                        openid = json内容3['openid']
                        minico_token = json内容3['minico_token']
                        return {'openid': openid, 'minico_token': minico_token}, None
                    return None, "获取openid和minico_token失败"
        except Exception as e:
            self.context.logger.error(f"第二个API查询失败: {str(e)}")
            return None, f"第二个接口查询失败: {str(e)}"
    
    async def _query_third_api(self, openid: str, minico_token: str, uin: str):
        """查询第三个接口获取违规内容"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{THIRD_API_URL}{quote(openid)}&token={quote(minico_token)}&uin={quote(uin)}"
                async with session.get(url) as response4:
                    text4 = await response4.text()
                    return text4, None
        except Exception as e:
            self.context.logger.error(f"第三个API查询失败: {str(e)}")
            return None, f"第三个接口查询失败: {str(e)}"
    
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        """群聊消息处理器"""
        msg = event.message_str.strip()
        
        if msg == "查违规":
            # 这里需要先获取code1，暂时用固定值
            code1 = "需要获取的code1值"
            
            # 第一步：获取ticket和uin
            yield event.chain_result([Plain(text="正在获取登录凭证...")])
            first_result, first_error = await self._query_first_api(code1)
            
            if first_error:
                yield event.chain_result([Plain(text=first_error)])
                return
            
            # 第二步：获取openid和minico_token
            yield event.chain_result([Plain(text="正在获取用户信息...")])
            second_result, second_error = await self._query_second_api(first_result['ticket'])
            
            if second_error:
                yield event.chain_result([Plain(text=second_error)])
                return
            
            # 第三步：查询违规内容
            yield event.chain_result([Plain(text="正在查询违规记录...")])
            third_result, third_error = await self._query_third_api(
                second_result['openid'], 
                second_result['minico_token'], 
                first_result['uin']
            )
            
            if third_error:
                yield event.chain_result([Plain(text=third_error)])
                return
            
            # 返回结果
            完整内容 = f"{third_result}\n因考虑到霸屏缘故 违规内容只返回十条"
            yield event.chain_result([Plain(text=完整内容)])
