import aiohttp
import json
from urllib.parse import quote_async

async def main_function(code1, e):
    async with aiohttp.ClientSession() as session:
        try:
            # 第一个请求
            async with session.get(f"链接1{quote_async(code1)}") as response2:
                text2 = await response2.text()
                json_content2 = json.loads(text2)
                
                if json_content2.get('data') and json_content2['data'].get('ticket') and json_content2['data'].get('uin'):
                    ticket = json_content2['data']['ticket']
                    uin = json_content2['data']['uin']
                    
                    # 第二个请求
                    async with session.get(f"链接2{quote_async(ticket)}") as response3:
                        text3 = await response3.text()
                        json_content3 = json.loads(text3)
                        
                        if json_content3.get('openid') and json_content3.get('minico_token'):
                            openid = json_content3['openid']
                            minico_token = json_content3['minico_token']
                            
                            # 第三个请求
                            params = {
                                'openid': quote_async(openid),
                                'token': quote_async(minico_token),
                                'uin': quote_async(uin)
                            }
                            url = f"链接3{params['openid']}&token={params['token']}&uin={params['uin']}"
                            
                            async with session.get(url) as response4:
                                text4 = await response4.text()
                                
                                full_content = f"{text4}\n因考虑到霸屏缘故 违规内容只返回十条"
                                # 假设有相应的回复函数
                                await e.reply(full_content)
                        else:
                            print("缺少openid或minico_token")
                else:
                    print("缺少ticket或uin数据")
                    
        except Exception as error:
            print(f"请求出错: {error}")

# 注意：需要安装aiohttp: pip install aiohttp
