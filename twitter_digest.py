#!/usr/bin/env python3
"""
Twitter 推文收集和邮件发送脚本
功能：定时收集 @fxtrader, @Osint613, @ChineseWSJ 的推文，翻译成中文，发送到邮箱

使用说明：
1. 安装依赖: pip install ntscraper deep-translator yagmail
2. 配置环境变量或直接修改下方配置
3. 运行: python twitter_digest.py
"""

import os
import sys
from datetime import datetime, timedelta
from ntscraper import Nitter
from deep_translator import GoogleTranslator
import yagmail


# ==================== 配置区域 ====================

# 邮箱配置
SENDER_EMAIL = "466919954@qq.com"
SENDER_PASSWORD = "dxgmlsritzwacbcf"  # SMTP 授权码
RECEIVER_EMAIL = "466919954@qq.com"

# 要收集的推特账号
TWITTER_ACCOUNTS = ["fxtrader", "Osint613", "ChineseWSJ"]

# 收集最近多少条推文
TWEETS_PER_ACCOUNT = 10

# ==================== 业务逻辑 ====================


def init_translator():
    """初始化翻译器"""
    return GoogleTranslator(source='auto', target='zh-CN')


def translate_text(translator, text):
    """翻译文本到中文"""
    try:
        # 如果文本太短或包含大量@符号，可能不需要翻译
        if len(text) < 10 or text.startswith('@'):
            return text
        
        # 翻译
        translated = translator.translate(text)
        return translated if translated else text
    except Exception as e:
        print(f"翻译错误: {e}")
        return text


def get_tweets(nitter, username, count):
    """获取用户推文"""
    try:
        tweets = nitter.get_tweets(username, mode='user', number=count)
        return tweets.get('tweets', [])
    except Exception as e:
        print(f"获取 {username} 推文失败: {e}")
        return []


def format_tweet_time(utc_time_str):
    """将UTC时间转换为北京时间"""
    try:
        # 尝试解析各种时间格式
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
            # 如果都无法解析，返回原始字符串
            return utc_time_str
        
        # 转换为北京时间 (UTC+8)
        beijing_time = utc_time + timedelta(hours=8)
        return beijing_time.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return utc_time_str


def build_email_content(all_tweets, translator):
    """构建邮件内容"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 邮件头
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .header {{ background: #1da1f2; color: white; padding: 20px; }}
            .tweet {{ border-bottom: 1px solid #eee; padding: 15px 0; }}
            .username {{ color: #1da1f2; font-weight: bold; }}
            .time {{ color: #657786; font-size: 14px; }}
            .content {{ margin: 10px 0; }}
            .translation {{ background: #f5f8fa; padding: 10px; border-radius: 5px; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🐦 Twitter 推文汇总</h2>
            <p>收集时间: {current_time} 北京时间</p>
            <p>推文数量: {len(all_tweets)} 条</p>
        </div>
    """
    
    # 按时间排序（最新的在前）
    all_tweets.sort(key=lambda x: x['time'], reverse=True)
    
    # 生成邮件主题（取fxtrader最新推文前20字）
    subject = "Twitter 推文汇总"
    for tweet in all_tweets:
        if tweet['username'] == 'fxtrader':
            # 获取原文前20字符作为主题
            content_preview = tweet['original'][:20]
            subject = content_preview
            break
    
    # 推文列表
    for tweet in all_tweets:
        # 翻译
        translated = translate_text(translator,tweet['original'])
        
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
    """发送邮件"""
    try:
        print(f"正在发送邮件，主题: {subject}")
        
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
        
        print("✅ 邮件发送成功！")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🐦 Twitter 推文收集任务开始")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 初始化
    nitter = Nitter(log_level=1)
    translator = init_translator()
    
    # 收集所有推文
    all_tweets = []
    
    for username in TWITTER_ACCOUNTS:
        print(f"\n📱 正在收集 @{username} 的推文...")
        
        tweets = get_tweets(nitter, username, TWEETS_PER_ACCOUNT)
        
        for tweet in tweets:
            tweet_info = {
                'username': username,
                'time': format_tweet_time(tweet.get('date', '')),
                'original': tweet.get('text', ''),
                'link': tweet.get('link', '')
            }
            all_tweets.append(tweet_info)
        
        print(f"   ✓ 已收集 {len(tweets)} 条推文")
    
    print(f"\n📊 总共收集 {len(all_tweets)} 条推文")
    
    if not all_tweets:
        print("⚠️ 没有收集到任何推文")
        return
    
    # 构建邮件
    subject, html_content = build_email_content(all_tweets, translator)
    
    # 发送邮件
    send_email(subject, html_content)
    
    print("\n✅ 任务完成！")


if __name__ == "__main__":
    main()
