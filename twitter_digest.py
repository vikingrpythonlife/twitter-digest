#!/usr/bin/env python3
"""
Twitter 推文收集 - 使用 ntscraper (调试版本)
"""

import os
import sys
from datetime import datetime, timedelta
from ntscraper import Nitter
from deep_translator import GoogleTranslator
import yagmail

# 打印 Python 版本和所有导入的模块
print(f"Python版本: {sys.version}")

SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL', '466919954@qq.com')

TWITTER_ACCOUNTS = ["fxtrader", "Osint613", "ChineseWSJ"]

# 初始化 Nitter scraper
print("初始化 Nitter scraper...")
scraper = Nitter(log_level=1)


def translate_text(text):
    """翻译英文推文到中文"""
    try:
        if len(text) < 5:
            return text
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return text
        translator = GoogleTranslator(source='auto', target='zh-CN')
        return translator.translate(text) or text
    except Exception as e:
        print(f"翻译错误: {e}")
        return text


def get_tweets():
    """获取推文"""
    all_tweets = []
    
    now_beijing = datetime.now()
    one_hour_ago = now_beijing - timedelta(hours=1)
    
    print(f"筛选时间范围: {one_hour_ago.strftime('%Y-%m-%d %H:%M:%S')} - {now_beijing.strftime('%Y-%m-%d %H:%M:%S')} 北京时间")
    
    for username in TWITTER_ACCOUNTS:
        print(f"\n{'='*50}")
        print(f"开始获取 @{username} 的推文...")
        
        try:
            print(f"调用 ntscraper.get_tweets()...")
            tweets = scraper.get_tweets(names=[username], number=10)
            
            print(f"原始返回: {type(tweets)}")
            print(f"返回数据: {tweets}")
            
            if not tweets:
                print(f"  返回为空")
                continue
                
            if 'tweets' not in tweets:
                print(f"  返回结构中没有 'tweets' 键")
                print(f"  全部keys: {tweets.keys() if hasattr(tweets, 'keys') else 'N/A'}")
                continue
                
            user_tweets = tweets.get('tweets', [])
            print(f"获取到 {len(user_tweets)} 条推文")
            
            for i, tweet in enumerate(user_tweets):
                print(f"\n--- 推文 {i+1} ---")
                print(f"原始数据: {tweet}")
                
                tweet_time = tweet.get('date')
                text = tweet.get('text', '')
                
                print(f"时间字段: {tweet_time}")
                print(f"内容: {text[:50] if text else '无'}...")
                
                if not tweet_time or not text:
                    print("  跳过: 无时间或内容")
                    continue
                
                # 解析时间
                tweet_datetime = None
                try:
                    if tweet_time and 'T' in str(tweet_time):
                        tweet_datetime = datetime.strptime(str(tweet_time)[:19], '%Y-%m-%dT%H:%M:%S')
                        tweet_datetime = tweet_datetime + timedelta(hours=8)
                    elif tweet_time:
                        tweet_datetime = datetime.strptime(str(tweet_time), '%Y-%m-%d %H:%M:%S')
                        tweet_datetime = tweet_datetime + timedelta(hours=8)
                except Exception as e:
                    print(f"  时间解析失败: {e}")
                    tweet_datetime = now_beijing - timedelta(minutes=5)
                
                print(f"解析后时间: {tweet_datetime}")
                print(f"截止时间: {one_hour_ago}")
                print(f"是否在范围内: {tweet_datetime >= one_hour_ago if tweet_datetime else 'N/A'}")
                
                if tweet_datetime and tweet_datetime >= one_hour_ago:
                    all_tweets.append({
                        'username': username,
                        'time': tweet_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                        'original': text
                    })
                    print(f"  ✓ 添加到列表")
            
            print(f"\n成功获取 {len(user_tweets)} 条推文")
            continue
                
        except Exception as e:
            import traceback
            print(f"  ntscraper 异常: {e}")
            traceback.print_exc()
        
        print(f"  无法获取 @{username} 的推文")
    
    print(f"\n{'='*50}")
    print(f"总计获取: {len(all_tweets)} 条推文")
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
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("错误: 请设置 SENDER_EMAIL 和 SENDER_PASSWORD 环境变量")
        return
    
    print("=" * 50)
    print("开始收集推文 (调试模式)...")
    print("=" * 50)
    
    now_beijing = datetime.now()
    one_hour_ago = now_beijing - timedelta(hours=1)
    time_range = f"{one_hour_ago.strftime('%H:%M')} - {now_beijing.strftime('%H:%M')}"
    
    all_tweets = get_tweets()
    
    print(f"\n最终结果: 最近一小时 ({time_range}) 共 {len(all_tweets)} 条推文")
    
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
            html += f"<div><p><strong>@{t['username']}</strong> · {t['time']}</p><p>{t['original']}</p><p><em>翻译: {trans}</em></p></div><hr>"
    else:
        subject = "Twitter 推文汇总"
        html = f"<h2>Twitter 推文汇总</h2><p>收集时间: {now_str} 北京时间</p><p>时间范围: {time_range} 北京时间</p><p>最近一小时没有新推文。</p>"
    
    send_email(subject, html)
    print("\n完成！")


if __name__ == "__main__":
    main()
