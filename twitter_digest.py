#!/usr/bin/env python3
"""
Twitter 推文收集 - 使用 snscrape
"""

import os
import snscrape.modules.twitter as sntwitter
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import yagmail

SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL', '466919954@qq.com')

TWITTER_ACCOUNTS = ["fxtrader", "Osint613", "ChineseWSJ"]


def translate_text(text):
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
    all_tweets = []
    
    now_beijing = datetime.now()
    one_hour_ago = now_beijing - timedelta(hours=1)
    
    print(f"筛选时间: {one_hour_ago.strftime('%H:%M')} - {now_beijing.strftime('%H:%M')} 北京时间")
    
    for username in TWITTER_ACCOUNTS:
        print(f"\n获取 @{username}...")
        
        try:
            # 使用 snscrape 抓取用户推文
            query = f"from:{username}"
            scraper = sntwitter.TwitterSearchScraper(query)
            
            count = 0
            for i, tweet in enumerate(scraper.get_items()):
                if i >= 10:  # 最多获取10条
                    break
                
                # 时间处理
                tweet_time = tweet.date
                if tweet_time.tzinfo is not None:
                    tweet_time = tweet_time.replace(tzinfo=None)
                tweet_time = tweet_time + timedelta(hours=8)  # 转为北京时间
                
                print(f"  推文 {i+1}: {tweet_time} - {tweet.content[:30]}...")
                
                if tweet_time >= one_hour_ago:
                    all_tweets.append({
                        'username': username,
                        'time': tweet_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'original': tweet.content
                    })
                    count += 1
            
            print(f"  获取 {count} 条新推文")
            
        except Exception as e:
            print(f"  snscrape 失败: {e}")
            import traceback
            traceback.print_exc()
    
    return all_tweets


def send_email(subject, content):
    try:
        print(f"\n发送邮件: {subject}")
        yag = yagmail.SMTP(user=SENDER_EMAIL, password=SENDER_PASSWORD, host='smtp.qq.com')
        yag.send(to=RECEIVER_EMAIL, subject=subject, contents=content)
        print("邮件发送成功！")
    except Exception as e:
        print(f"发送失败: {e}")


def main():
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("错误: 请设置环境变量")
        return
    
    print("=" * 50)
    print("开始收集推文...")
    print("=" * 50)
    
    now_beijing = datetime.now()
    one_hour_ago = now_beijing - timedelta(hours=1)
    
    all_tweets = get_tweets()
    print(f"\n最近一小时获取 {len(all_tweets)} 条推文")
    
    now_str = now_beijing.strftime("%Y-%m-%d %H:%M:%S")
    
    if all_tweets:
        all_tweets.sort(key=lambda x: x['time'], reverse=True)
        
        subject = "Twitter 推文汇总"
        for t in all_tweets:
            if t['username'] == 'fxtrader' and t['original']:
                subject = t['original'][:20]
                break
        
        html = f"<h2>Twitter 推文汇总</h2><p>收集时间: {now_str} 北京时间</p><p>推文数量: {len(all_tweets)} 条</p><hr>"
        
        for t in all_tweets:
            trans = translate_text(t['original'])
            html += f"<div><p><strong>@{t['username']}</strong> · {t['time']}</p><p>{t['original']}</p><p><em>翻译: {trans}</em></p></div><hr>"
    else:
        subject = "Twitter 推文汇总"
        html = f"<h2>Twitter 推文汇总</h2><p>收集时间: {now_str} 北京时间</p><p>最近一小时没有新推文。</p>"
    
    send_email(subject, html)
    print("\n完成！")


if __name__ == "__main__":
    main()
