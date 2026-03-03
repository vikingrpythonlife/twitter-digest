#!/usr/bin/env python3
"""
Twitter 推文收集 - 使用 ntscraper
只收集最近一小时的推文
"""

import os
from datetime import datetime, timedelta
from ntscraper import Nitter
from deep_translator import GoogleTranslator
import yagmail

SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL', '466919954@qq.com')

TWITTER_ACCOUNTS = ["fxtrader", "Osint613", "ChineseWSJ"]

# 初始化 Nitter scraper
scraper = Nitter(log_level=0)


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
        
        try:
            # 使用 ntscraper 获取推文
            tweets = scraper.get_tweets(names=[username], number=10)
            
            if tweets and 'tweets' in tweets:
                user_tweets = tweets.get('tweets', [])
                
                for tweet in user_tweets:
                    # 获取推文时间和内容
                    tweet_time = tweet.get('date')
                    text = tweet.get('text', '')
                    
                    if not tweet_time or not text:
                        continue
                    
                    # 解析时间
                    try:
                        # 尝试解析多种时间格式
                        if 'T' in tweet_time:
                            tweet_datetime = datetime.strptime(tweet_time[:19], '%Y-%m-%dT%H:%M:%S')
                            tweet_datetime = tweet_datetime + timedelta(hours=8)
                        else:
                            # 尝试其他格式
                            tweet_datetime = datetime.strptime(tweet_time, '%Y-%m-%d %H:%M:%S')
                            tweet_datetime = tweet_datetime + timedelta(hours=8)
                    except:
                        # 如果解析失败，使用当前时间减去一个估计值
                        tweet_datetime = now_beijing - timedelta(minutes=30)
                    
                    # 只保留最近一小时的推文
                    if tweet_datetime >= one_hour_ago:
                        all_tweets.append({
                            'username': username,
                            'time': tweet_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                            'original': text
                        })
                        print(f"  获取到推文: {text[:30]}...")
                
                print(f"  成功获取 {len(user_tweets)} 条推文")
                continue
                
        except Exception as e:
            print(f"  ntscraper 失败: {e}")
        
        print(f"  无法获取 @{username} 的推文")
    
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
