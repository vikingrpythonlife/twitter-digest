#!/usr/bin/env python3
"""
Twitter 推文收集和邮件发送脚本
功能：定时收集 @fxtrader, @Osint613, @ChineseWSJ 的推文，翻译成中文，发送到邮箱
"""

import os
import sys
from datetime import datetime, timedelta
from ntscraper import Nitter
from deep_translator import GoogleTranslator
import yagmail


# ==================== 配置区域 ====================

# 优先使用环境变量（GitHub Secrets），其次使用默认值
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', '466919954@qq.com')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD', 'dxgmlsritzwacbcf')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL', '466919954@qq.com')

# 要收集的推特账号
TWITTER_ACCOUNTS = ["fxtrader", "Osint613", "ChineseWSJ"]

# 收集最近多少条推文
TWEETS_PER_ACCOUNT = 10


def init_translator():
    return GoogleTranslator(source='auto', target='zh-CN')


def translate_text(translator, text):
    try:
        if len(text) < 10 or text.startswith('@'):
            return text
        translated = translator.translate(text)
        return translated if translated else text
    except Exception as e:
        print(f"翻译错误: {e}")
        return text


def get_tweets(nitter, username, count):
    try:
        tweets = nitter.get_tweets(username, mode='user', number=count)
        return tweets.get('tweets', [])
    except Exception as e:
        print(f"获取 {username} 推文失败: {e}")
        return []


def format_tweet_time(utc_time_str):
    try:
        time_formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
        ]
        
        for fmt in time_formats:
            try:
                utc_time = datetime.strptime(utc_time_str.replace('+0000', '').strip(), fmt)
                break
            except:
                continue
        else:
            return utc_time_str
        
        beijing_time = utc_time + timedelta(hours=8)
        return beijing_time.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return utc_time_str


def build_email_content(all_tweets, translator):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            .header { background: #1da1f2; color: white; padding: 20px; }
            .tweet { border-bottom: 1px solid #eee; padding: 15px 0; }
            .username { color: #1da1f2; font-weight: bold; }
            .time { color: #657786; font-size: 14px; }
            .content { margin: 10px 0; }
            .translation { background: #f5f8fa; padding: 10px; border-radius: 5px; margin-top: 5px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>Twitter 推文汇总</h2>
            <p>收集时间: {current_time} 北京时间</p>
            <p>推文数量: {len(all_tweets)} 条</p>
        </div>
    """
    
    all_tweets.sort(key=lambda x: x['time'], reverse=True)
    
    subject = "Twitter 推文汇总"
    for tweet in all_tweets:
        if tweet['username'] == 'fxtrader':
            content_preview = tweet['original'][:20]
            subject = content_preview
            break
    
    for tweet in all_tweets:
        translated = translate_text(translator, tweet['original'])
        
        html_content += f"""
        <div class="tweet">
            <p class="username">@{tweet['username']}</p>
            <p class="time">🕐 {tweet['time']} 北京时间</p>
            <div class="content">
                <p><strong>原文:</strong> {tweet['original']}</p>
                <div class="translation">
                    <p><strong>翻译:</strong> {translated}</p>
                </div>
            </div>
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    return subject, html_content


def send_email(subject, html_content):
    try:
        print(f"正在发送邮件，主题: {subject}")
        print(f"发件人: {SENDER_EMAIL}")
        print(f"收件人: {RECEIVER_EMAIL}")
        
        yag = yagmail.SMTP(
            user=SENDER_EMAIL,
            password=SENDER_PASSWORD,
            host='smtp.qq.com'
        )
        
        yag.send(
            to=RECEIVER_EMAIL,
            subject=subject,
            contents=html_content
        )
        
        print("邮件发送成功！")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("Twitter 推文收集任务开始")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"发件邮箱: {SENDER_EMAIL}")
    print("=" * 60)
    
    nitter = Nitter(log_level=1)
    translator = init_translator()
    
    all_tweets = []
    
    for username in TWITTER_ACCOUNTS:
        print(f"\n正在收集 @{username} 的推文...")
        
        tweets = get_tweets(nitter, username, TWEETS_PER_ACCOUNT)
        
        for tweet in tweets:
            tweet_info = {
                'username': username,
                'time': format_tweet_time(tweet.get('date', '')),
                'original': tweet.get('text', ''),
                'link': tweet.get('link', '')
            }
            all_tweets.append(tweet_info)
        
        print(f"   已收集 {len(tweets)} 条推文")
    
    print(f"\n总共收集 {len(all_tweets)} 条推文")
    
    if not all_tweets:
        print("没有收集到任何推文")
        subject = "Twitter 推文汇总 - 没有新推文"
        html_content = f"""
        <html>
        <body>
            <h2>Twitter 推文汇总</h2>
            <p>收集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 北京时间</p>
            <p>最近一小时没有新推文。</p>
        </body>
        </html>
        """
        send_email(subject, html_content)
        return
    
    subject, html_content = build_email_content(all_tweets, translator)
    send_email(subject, html_content)
    
    print("\n任务完成！")


if __name__ == "__main__":
    main()
