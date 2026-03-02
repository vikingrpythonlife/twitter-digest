#!/usr/bin/env python3
"""
Twitter 推文收集 - 使用 Fxtwitter/Nitter API
只收集最近一小时的推文
"""

import os
import re
import json
import requests
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import yagmail

SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL', '466919954@qq.com')

TWITTER_ACCOUNTS = ["fxtrader", "Osint613", "ChineseWSJ"]


def translate_text(text):
    """翻译英文推文到中文"""
    try:
        if len(text) < 5:
            return text
        # 检测是否包含中文字符
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return text  # 已有中文，不翻译
        translator = GoogleTranslator(source='auto', target='zh-CN')
        return translator.translate(text) or text
    except Exception as e:
        print(f"翻译错误: {e}")
        return text


def get_tweets():
    """获取推文"""
    all_tweets = []
    
    # 当前时间
    now_beijing = datetime.now()
    one_hour_ago = now_beijing - timedelta(hours=1)
    
    print(f"筛选最近一小时的推文: {one_hour_ago.strftime('%H:%M')} - {now_beijing.strftime('%H:%M')} 北京时间")
    
    for username in TWITTER_ACCOUNTS:
        print(f"\n获取 @{username}...")
        
        # 方法1: 尝试 fxtwitter.com (vxtwitter的替代)
        try:
            url = f"https://api.fxtwitter.com/v1/user/{username}?count=20"
            print(f"  尝试: {url}")
            
            resp = requests.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if resp.status_code == 200:
                data = resp.json()
                # 解析fxtwitter响应结构
                user_data = data.get('user', {}).get('result', {}) if 'user' in data else data
                tweets_data = user_data.get('timeline', {}).get('timeline', {}).get('instructions', [])
                
                for instruction in tweets_data:
                    entries = instruction.get('entries', [])
                    for entry in entries:
                        content = entry.get('content', {})
                        item = content.get('item', {})
                        tweet_data = item.get('itemContent', {})
                        
                        # 尝试多种结构
                        if not tweet_data:
                            tweet_data = entry.get('content', {})
                        
                        tweet_results = tweet_data.get('tweet_results', {})
                        result = tweet_results.get('result', {})
                        
                        if result:
                            legacy = result.get('legacy', {})
                            created_at_str = legacy.get('created_at', '')
                            
                            if created_at_str:
                                tweet_time = datetime.strptime(created_at_str, '%a %b %d %H:%M:%S +0000 %Y')
                                tweet_time = tweet_time + timedelta(hours=8)  # 转换为北京时间
                                
                                if tweet_time >= one_hour_ago:
                                    text = legacy.get('full_text', '')
                                    all_tweets.append({
                                        'username': username,
                                        'time': tweet_time.strftime("%Y-%m-%d %H:%M:%S"),
                                        'original': text
                                    })
                
                print(f"  fxtwitter 成功获取数据")
                continue
        except Exception as e:
            print(f"  fxtwitter 失败: {e}")
        
        # 方法2: 尝试 Nitter 实例
        nitter_instances = ['nitter.net', 'nitter.privacydev.net', 'nitter.poast.org']
        for nitter_instance in nitter_instances:
            try:
                url = f"https://{nitter_instance}/{username}"
                print(f"  尝试: {url}")
                
                resp = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if resp.status_code == 200:
                    # 解析HTML获取推文
                    html = resp.text
                    
                    # 查找推文时间
                    time_pattern = r'datetime="([^"]+)"'
                    content_pattern = r'class="tweet-content[^>]*>([^<]+)'
                    
                    import re
                    times = re.findall(time_pattern, html)
                    contents = re.findall(content_pattern, html)
                    
                    for i, (t_str, content) in enumerate(zip(times[:10], contents[:10])):
                        try:
                            tweet_time = datetime.fromisoformat(t_str.replace('Z', '+00:00'))
                            tweet_time = tweet_time + timedelta(hours=8)
                            
                            if tweet_time >= one_hour_ago:
                                all_tweets.append({
                                    'username': username,
                                    'time': tweet_time.strftime("%Y-%m-%d %H:%M:%S"),
                                    'original': content.strip()
                                })
                        except:
                            pass
                    
                    if all_tweets:
                        print(f"  从 {nitter_instance} 获取 {len(all_tweets)} 条")
                        break
            except Exception as e:
                print(f"  {nitter_instance} 失败: {e}")
                continue
        
        else:
            print(f"  所有方法都失败")
    
    return all_tweets


def send_email(subject, content):
    """发送邮件"""
    try:
        print(f"\n发送邮件: {subject}")
        yag = yagmail.SMTP(user=SENDER_EMAIL, password=SENDER_PASSWORD, host='smtp.qq.com')
        yag.send(to=RECEIVER_EMAIL, subject=subject, contents=content)
        print("邮件发送成功！")
        return True
    except Exception as e:
        print(f"发送失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    # 验证环境变量
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("错误: 请设置 SENDER_EMAIL 和 SENDER_PASSWORD 环境变量")
        return
    
    print("=" * 50)
    print("开始收集推文...")
    print("=" * 50)
    
    now_beijing = datetime.now()
    one_hour_ago = now_beijing - timedelta(hours=1)
    time_range = f"{one_hour_ago.strftime('%H:%M')} - {now_beijing.strftime('%H:%M')}"
    
    all_tweets = get_tweets()
    print(f"\n最近一小时 ({time_range}) 共收集 {len(all_tweets)} 条推文")
    
    now_str = now_beijing.strftime("%Y-%m-%d %H:%M:%S")
    
    if all_tweets:
        # 按时间排序
        all_tweets.sort(key=lambda x: x['time'], reverse=True)
        
        # 邮件标题使用 fxtrader 的推文前20字
        subject = "Twitter 推文汇总"
        for t in all_tweets:
            if t['username'] == 'fxtrader' and t['original']:
                subject = t['original'][:20]
                break
        
        html = f"<h2>Twitter 推文汇总</h2><p>收集时间: {now_str} 北京时间</p><p>时间范围: {time_range} 北京时间</p><p>推文数量: {len(all_tweets)} 条</p><hr>"
        
        for t in all_tweets:
            trans = translate_text(t['original'])
            html += f"<div><p><strong>@{t['username']}</strong> · {t['time']}</p><p>{t['original']}</p><p><em>翻译: {trans}</em></p></div><hr>"
    else:
        subject = "Twitter 推文汇总"
        html = f"<h2>Twitter 推文汇总</h2><p>收集时间: {now_str} 北京时间</p><p>时间范围: {time_range} 北京时间</p><p>最近一小时没有新推文。</p>"
    
    send_email(subject, html)
    print("\n完成！")


if __name__ == "__main__":
    main()
