#!/usr/bin/env python3
"""
Twitter 推文收集 - 使用 RSSHub API
不需要 Twitter API，通过 RSSHub 获取数据
只收集最近一小时的推文
"""

import os
import re
import requests
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import yagmail

SENDER_EMAIL = os.environ.get('SENDER_EMAIL', '466919954@qq.com')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD', 'dxgmlsritzwacbcf')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL', '466919954@qq.com')

TWITTER_ACCOUNTS = ["fxtrader", "Osint613", "ChineseWSJ"]


def translate_text(text):
    try:
        if len(text) < 5:
            return text
        translator = GoogleTranslator(source='auto', target='zh-CN')
        return translator.translate(text) or text
    except Exception as e:
        print(f"翻译错误: {e}")
        return text


def get_tweets():
    """通过 RSSHub API 获取推文"""
    all_tweets = []
    
    # 当前时间（北京时间）
    now_beijing = datetime.now()
    one_hour_ago = now_beijing - timedelta(hours=1)
    
    print(f"筛选最近一小时的推文: {one_hour_ago.strftime('%H:%M')} - {now_beijing.strftime('%H:%M')} 北京时间")
    
    for username in TWITTER_ACCOUNTS:
        print(f"\n获取 @{username}...")
        
        # 尝试方法1: vxtwitter API
        try:
            url = f"https://api.vxtwitter.com/user/{username}"
            print(f"  尝试: {url}")
            
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                tweets = data.get('tweets', [])
                for t in tweets[:10]:
                    created_at = t.get('created_at', '')
                    tweet_time = None
                    if created_at:
                        try:
                            tweet_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            tweet_time = tweet_time + timedelta(hours=8)
                        except:
                            pass
                    
                    if tweet_time and tweet_time >= one_hour_ago:
                        all_tweets.append({
                            'username': username,
                            'time': tweet_time.strftime("%Y-%m-%d %H:%M:%S"),
                            'original': t.get('text', '')
                        })
                print(f"  成功获取 {len(tweets)} 条")
                continue
        except Exception as e:
            print(f"  vxtwitter 失败: {e}")
        
        # 尝试方法2: Nitter RSS
        for nitter_instance in ['nitter.net', 'nitter.privacydev.net', 'nitter.poast.org']:
            try:
                url = f"https://{nitter_instance}/{username}/rss"
                print(f"  尝试: {url}")
                
                resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(resp.content)
                    
                    items = root.findall('.//item')
                    for item in items[:10]:
                        title = item.find('title')
                        desc = item.find('description')
                        pub = item.find('pubDate')
                        
                        text = title.text if title is not None else ""
                        if desc is not None and desc.text:
                            text = desc.text
                        
                        tweet_time = None
                        if pub is not None and pub.text:
                            try:
                                from email.utils import parsedate_to_datetime
                                dt = parsedate_to_datetime(pub.text)
                                beijing_time = dt + timedelta(hours=8)
                                tweet_time = beijing_time
                                time_str = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
                            except:
                                pass
                        
                        if text and tweet_time:
                            text = re.sub(r'<[^>]+>', '', text)
                            if tweet_time >= one_hour_ago:
                                all_tweets.append({
                                    'username': username,
                                    'time': time_str,
                                    'original': text.strip()
                                })
                    
                    print(f"  从 {nitter_instance} 获取 {len(items)} 条")
                    break
            except Exception as e:
                print(f"  {nitter_instance} 失败: {e}")
                continue
        
        else:
            print(f"  所有方法都失败")
    
    return all_tweets


def send_email(subject, content):
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
        all_tweets.sort(key=lambda x: x['time'], reverse=True)
        
        subject = "Twitter 推文汇总"
        for t in all_tweets:
            if t['username'] == 'fxtrader' and t['original']:
                subject = t['original'][:20]
                break
        
        html = f"<h2>Twitter 推文汇总</h2><p>收集时间: {now_str} 北京时间</p><p>时间范围: {time_range} 北京时间</p><p>推文数量: {len(all_tweets)} 条</p><hr>"
        
        for t in all_tweets:
            trans = translate_text(t['original'])
            html += f"<div><p><strong>@{t['username']}</strong> · {t['time']}</p><p>{t['original']}</p><p>翻译: {trans}</p></div><hr>"
    else:
        subject = "Twitter 推文汇总"
        html = f"<h2>Twitter 推文汇总</h2><p>收集时间: {now_str} 北京时间</p><p>时间范围: {time_range} 北京时间</p><p>最近一小时没有新推文。</p>"
    
    send_email(subject, html)
    print("\n完成！")


if __name__ == "__main__":
    main()
