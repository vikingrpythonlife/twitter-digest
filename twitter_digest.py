#!/usr/bin/env python3
"""
Twitter 推文收集和邮件发送脚本 - 稳定版
"""

import os
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import yagmail
import urllib3

urllib3.disable_warnings()

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
    all_tweets = []
    try:
        from ntscraper import Nitter
        nitter = Nitter(log_level=0)
        
        for username in TWITTER_ACCOUNTS:
            try:
                print(f"获取 @{username}...")
                tweets = nitter.get_tweets(username, mode='user', number=10)
                tweet_list = tweets.get('tweets', [])
                
                for tweet in tweet_list:
                    try:
                        date_str = tweet.get('date', '')
                        if 'T' in date_str:
                            utc_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        else:
                            utc_time = datetime.now() - timedelta(hours=1)
                        
                        beijing_time = utc_time + timedelta(hours=8)
                        
                        all_tweets.append({
                            'username': username,
                            'time': beijing_time.strftime("%Y-%m-%d %H:%M:%S"),
                            'original': tweet.get('text', ''),
                        })
                    except:
                        continue
                print(f"从 @{username} 获取 {len(tweet_list)} 条")
            except Exception as e:
                print(f"获取 @{username} 失败: {e}")
    except Exception as e:
        print(f"初始化失败: {e}")
    
    return all_tweets


def send_email(subject, content):
    try:
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
    
    all_tweets = get_tweets()
    print(f"\n共收集 {len(all_tweets)} 条推文")
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if all_tweets:
        all_tweets.sort(key=lambda x: x['time'], reverse=True)
        
        subject = "Twitter 推文汇总"
        for t in all_tweets:
            if t['username'] == 'fxtrader' and t['original']:
                subject = t['original'][:20]
                break
        
        html = f"<h2>Twitter 推文汇总</h2><p>时间: {now_str} 北京时间</p><p>数量: {len(all_tweets)}</p><hr>"
        
        for t in all_tweets:
            trans = translate_text(t['original'])
            html += f"<div><p><strong>@{t['username']}</strong> · {t['time']}</p><p>{t['original']}</p><p>翻译: {trans}</p></div><hr>"
    else:
        subject = "Twitter 推文汇总 - 测试"
        html = f"<h2>Twitter 推文汇总</h2><p>时间: {now_str}</p><p>未能获取推文，这是测试邮件。</p>"
    
    send_email(subject, html)
    print("完成！")


if __name__ == "__main__":
    main()
