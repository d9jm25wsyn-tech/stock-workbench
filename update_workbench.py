#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026丙午年上证指数行情预测工作台 - 自动更新脚本
功能：获取上证指数最新数据 → 计算干支 → 匹配命理预测 → 生成HTML工作台
用法：python3 update_workbench.py
"""

import akshare as ak
import pandas as pd
import datetime
import json
import os
import sys

# 导入命理预测表
from gz_predict import GZ_PREDICT

TIANGAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
DIZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
WEEKDAYS = ['一','二','三','四','五','六','日']

# 2026年法定节假日（休市日）
HOLIDAYS_2026 = {
    '2026-01-01','2026-01-02','2026-01-03',
    '2026-02-15','2026-02-16','2026-02-17','2026-02-18','2026-02-19','2026-02-20','2026-02-21','2026-02-22','2026-02-23',
    '2026-04-04','2026-04-05','2026-04-06',
    '2026-05-01','2026-05-02','2026-05-03','2026-05-04','2026-05-05',
    '2026-06-19','2026-06-20','2026-06-21',
    '2026-09-25','2026-09-26','2026-09-27',
    '2026-10-01','2026-10-02','2026-10-03','2026-10-04','2026-10-05','2026-10-06','2026-10-07',
}

def ganzhi_of_date(y, m, d):
    """计算某日的日柱干支"""
    if m <= 2:
        m += 12; y -= 1
    c = y // 100; yy = y % 100
    i = 0 if m % 2 == 1 else 6
    g = (4*c + c//4 + 5*yy + yy//4 + 3*(m+1)//5 + d - 4) % 10
    z = (8*c + c//4 + 5*yy + yy//4 + 3*(m+1)//5 + d + 6 + i) % 12
    return TIANGAN[g] + DIZHI[z]

def get_month_pillar(y, m, d):
    """计算月柱（按节气）"""
    if (m == 1 and d < 4) or (m == 2 and d < 4):
        return '己丑', '腊月(丑月)'
    elif (m == 2 and d >= 4) or (m == 3 and d < 5):
        return '庚寅', '正月(寅月)'
    elif (m == 3 and d >= 5) or (m == 4 and d < 4):
        return '辛卯', '二月(卯月)'
    elif (m == 4 and d >= 4) or (m == 5 and d < 5):
        return '壬辰', '三月(辰月)'
    elif (m == 5 and d >= 5) or (m == 6 and d < 5):
        return '癸巳', '四月(巳月)'
    elif (m == 6 and d >= 5) or (m == 7 and d < 7):
        return '甲午', '五月(午月)'
    elif (m == 7 and d >= 7) or (m == 8 and d < 7):
        return '乙未', '六月(未月)'
    elif (m == 8 and d >= 7) or (m == 9 and d < 7):
        return '丙申', '七月(申月)'
    elif (m == 9 and d >= 7) or (m == 10 and d < 8):
        return '丁酉', '八月(酉月)'
    elif (m == 10 and d >= 8) or (m == 11 and d < 7):
        return '戊戌', '九月(戌月)'
    elif (m == 11 and d >= 7) or (m == 12 and d < 7):
        return '己亥', '十月(亥月)'
    else:
        return '庚子', '冬月(子月)'

def get_trend_class(trend):
    """判断走势分类（用于颜色）"""
    bull = ['暴涨','普涨','缓涨','涨势如潮','疯狂上涨','继续暴涨','稳步上涨','大涨','暴力拉升','个股普涨','政策救市','救市','政策出手','指数拉升','见底企稳','暴涨企稳','终结熊市']
    bear = ['暴跌','普跌','缓跌','崩盘','连续暴跌','高位雪崩','上攻受制','指数跌','指数徘徊']
    if trend in bull: return 'trend-bull'
    if trend in bear: return 'trend-bear'
    return 'trend-neutral'

def fetch_stock_data():
    """获取上证指数2026年数据"""
    print("正在获取上证指数数据...")
    try:
        df = ak.stock_zh_index_daily(symbol="sh000001")
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['date'] >= '2026-01-01'].copy()
        df = df.sort_values('date').reset_index(drop=True)
        print(f"获取到 {len(df)} 条数据，最新日期: {df.iloc[-1]['date'].strftime('%Y-%m-%d')}")
        return df
    except Exception as e:
        print(f"获取数据失败: {e}")
        print("尝试备用接口...")
        try:
            df = ak.index_zh_a_hist(symbol="000001", period="daily", start_date="20260101", end_date="20261231")
            df = df.rename(columns={'日期':'date','开盘':'open','收盘':'close','最高':'high','最低':'low','成交量':'volume'})
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            print(f"备用接口获取到 {len(df)} 条数据")
            return df
        except Exception as e2:
            print(f"备用接口也失败: {e2}")
            sys.exit(1)

def build_records(df):
    """构建全年每日记录（实际行情+预测）"""
    actual_dict = {}
    for _, row in df.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        actual_dict[date_str] = {
            'open': round(float(row['open']), 2),
            'close': round(float(row['close']), 2),
            'high': round(float(row['high']), 2),
            'low': round(float(row['low']), 2),
            'volume': int(float(row['volume']))
        }

    records = []
    prev_close = None
    cur = datetime.date(2026, 1, 1)
    end = datetime.date(2026, 12, 31)

    while cur <= end:
        date_str = cur.strftime('%Y-%m-%d')
        if cur.weekday() < 5 and date_str not in HOLIDAYS_2026:
            mp, mpn = get_month_pillar(cur.year, cur.month, cur.day)
            gz = ganzhi_of_date(cur.year, cur.month, cur.day)
            info = GZ_PREDICT.get(gz, {})

            if date_str in actual_dict:
                a = actual_dict[date_str]
                if prev_close is None:
                    # 找前一个交易日的收盘价
                    prev_d = cur - datetime.timedelta(days=1)
                    while prev_d.strftime('%Y-%m-%d') not in actual_dict and prev_d >= datetime.date(2025,12,1):
                        prev_d -= datetime.timedelta(days=1)
                    if prev_d.strftime('%Y-%m-%d') in actual_dict:
                        prev_close = actual_dict[prev_d.strftime('%Y-%m-%d')]['close']
                    else:
                        prev_close = a['open']

                open_chg = round((a['open'] - prev_close) / prev_close * 100, 2)
                close_chg = round((a['close'] - prev_close) / prev_close * 100, 2)
                intraday_chg = round((a['close'] - a['open']) / a['open'] * 100, 2)
                amplitude = round((a['high'] - a['low']) / prev_close * 100, 2)

                records.append({
                    'date': date_str, 'weekday': '周'+WEEKDAYS[cur.weekday()],
                    'lunar_month': mpn, 'month_pillar': mp, 'day_pillar': gz,
                    'open': a['open'], 'close': a['close'], 'prev_close': round(prev_close, 2),
                    'open_chg': open_chg, 'close_chg': close_chg,
                    'intraday_chg': intraday_chg, 'amplitude': amplitude,
                    'high': a['high'], 'low': a['low'], 'volume': a['volume'],
                    'mz_combo': info.get('combo',''), 'mz_trend': info.get('trend',''),
                    'mz_detail': info.get('detail',''), 'has_actual': True
                })
                prev_close = a['close']
            else:
                records.append({
                    'date': date_str, 'weekday': '周'+WEEKDAYS[cur.weekday()],
                    'lunar_month': mpn, 'month_pillar': mp, 'day_pillar': gz,
                    'open': None, 'close': None, 'prev_close': None,
                    'open_chg': None, 'close_chg': None, 'intraday_chg': None,
                    'amplitude': None, 'high': None, 'low': None, 'volume': None,
                    'mz_combo': info.get('combo',''), 'mz_trend': info.get('trend',''),
                    'mz_detail': info.get('detail',''), 'has_actual': False
                })
        cur += datetime.timedelta(days=1)

    return records

def calc_monthly_chg(records):
    """计算月度涨跌幅"""
    monthly = {}
    for r in records:
        if r['has_actual']:
            m = r['date'][:7]
            if m not in monthly:
                monthly[m] = {'first_open': r['open'], 'last_close': r['close'], 'days': 0}
            monthly[m]['last_close'] = r['close']
            monthly[m]['days'] += 1

    result = {}
    prev_close = None
    for m in sorted(monthly.keys()):
        d = monthly[m]
        if prev_close:
            chg = round((d['last_close'] - prev_close) / prev_close * 100, 2)
        else:
            chg = round((d['last_close'] - d['first_open']) / d['first_open'] * 100, 2)
        result[m] = chg
        prev_close = d['last_close']
    return result

def calc_trend_uprate(records):
    """计算各走势的上涨率"""
    groups = {}
    for r in records:
        if r['has_actual']:
            t = r['mz_trend']
            if t not in groups:
                groups[t] = {'up': 0, 'down': 0, 'total': 0}
            groups[t]['total'] += 1
            if r['close_chg'] > 0:
                groups[t]['up'] += 1
            else:
                groups[t]['down'] += 1
    return {t: round(g['up']/g['total']*100) for t, g in groups.items()}

def generate_html(records, monthly_chg, trend_uprate):
    """生成完整HTML工作台"""
    actual = [r for r in records if r['has_actual']]
    forecast = [r for r in records if not r['has_actual']]

    # 统计
    total = len(actual)
    up = len([r for r in actual if r['close_chg'] > 0])
    down = len([r for r in actual if r['close_chg'] < 0])
    flat = total - up - down
    max_up = max(actual, key=lambda x: x['close_chg'])
    max_down = min(actual, key=lambda x: x['close_chg'])
    start_close = actual[0]['prev_close']
    end_close = actual[-1]['close']
    period_chg = round((end_close - start_close) / start_close * 100, 2)

    stats = {
        'total': total, 'up': up, 'down': down, 'flat': flat,
        'max_up_date': max_up['date'], 'max_up_val': max_up['close_chg'],
        'max_down_date': max_down['date'], 'max_down_val': max_down['close_chg'],
        'start_close': start_close, 'end_close': end_close, 'period_chg': period_chg,
        'start_date': actual[0]['date'], 'end_date': actual[-1]['date'],
        'forecast_count': len(forecast),
        'forecast_start': forecast[0]['date'] if forecast else ''
    }

    # 1966年道琼斯历史参照
    dj_1966 = [
        ('正月(寅月)','庚寅',-3.22), ('二月(卯月)','辛卯',-2.85),
        ('三月(辰月)','壬辰',0.96), ('四月(巳月)','癸巳',-5.31),
        ('五月(午月)','甲午',-1.58), ('六月(未月)','乙未',-2.61),
        ('七月(申月)','丙申',-6.96), ('八月(酉月)','丁酉',-1.80),
        ('九月(戌月)','戊戌',4.24), ('十月(亥月)','己亥',-1.92),
        ('冬月(子月)','庚子',-0.75),
    ]
    dj_1966_layue = ('腊月(丑月)','己丑',1.47)

    # 2026年每月预测
    month_forecast_data = [
        ('腊月(丑月)','己丑','1月1日-2月3日','正印','正官','印泄官','平缓震荡','政策热议 走势疲软','2026-01'),
        ('正月(寅月)','庚寅','2月4日-3月5日','偏印','食神','枭神夺食','普跌','普跌 偶尔反弹','2026-02'),
        ('二月(卯月)','辛卯','3月6日-4月4日','正印','伤官','印制伤官','普跌震荡','节节抵抗性下跌','2026-03'),
        ('三月(辰月)','壬辰','4月5日-5月5日','比肩','七杀','比肩抗杀','普跌','指数跌幅少 个股跌幅大','2026-04'),
        ('四月(巳月)','癸巳','5月6日-6月5日','劫财','正财','劫夺财','大震荡','个股反复震荡 指数震荡','2026-05'),
        ('五月(午月)','甲午','6月6日-7月6日','食神','正财','食神生财','震荡见底','震荡中见到大底','2026-06'),
        ('六月(未月)','乙未','7月7日-8月7日','伤官','正官','伤官见官','暴涨','暴涨后 被政策调控','2026-07'),
        ('七月(申月)','丙申','8月8日-9月7日','偏财','偏印','财克印','暴涨','上半年涨 下半年盘整','2026-08'),
        ('八月(酉月)','丁酉','9月8日-10月7日','正财','正印','财克印','暴涨','上半年涨 下半年调整','2026-09'),
        ('九月(戌月)','戊戌','10月8日-11月6日','七杀','七杀','杀攻身','暴跌','金融危机 崩盘','2026-10'),
        ('十月(亥月)','己亥','11月7日-12月6日','正官','比肩','官临身','缓涨','政策刺激 温和牛市','2026-11'),
        ('冬月(子月)','庚子','12月7日-2027年1月4日','偏印','劫财','枭劫聚会','暴力震荡','暴涨 暴跌 暴涨 暴跌 暴跌','2026-12'),
    ]

    data_json = json.dumps(records, ensure_ascii=False)
    stats_json = json.dumps(stats, ensure_ascii=False)
    forecast_json = json.dumps([{
        'month': m[0], 'pillar': m[1], 'period': m[2],
        'tg_shs': m[3], 'dz_shs': m[4], 'combo': m[5],
        'trend': m[6], 'detail': m[7],
        'actual_chg': monthly_chg.get(m[8])
    } for m in month_forecast_data], ensure_ascii=False)
    dj1966_json = json.dumps(dj_1966, ensure_ascii=False)
    dj1966_layue_json = json.dumps(dj_1966_layue, ensure_ascii=False)
    uprate_json = json.dumps(trend_uprate, ensure_ascii=False)

    # 读取HTML模板
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 替换数据占位符
    html = html.replace('/*DATA_JSON*/', data_json)
    html = html.replace('/*STATS_JSON*/', stats_json)
    html = html.replace('/*FORECAST_JSON*/', forecast_json)
    html = html.replace('/*DJ1966_JSON*/', dj1966_json)
    html = html.replace('/*DJ1966_LAYUE_JSON*/', dj1966_layue_json)
    html = html.replace('/*UPRATE_JSON*/', uprate_json)

    return html

def main():
    print("=" * 50)
    print("2026丙午年上证指数行情预测工作台 - 数据更新")
    print("=" * 50)

    # 1. 获取数据
    df = fetch_stock_data()

    # 2. 构建记录
    print("正在计算干支并匹配命理预测...")
    records = build_records(df)
    actual_count = len([r for r in records if r['has_actual']])
    forecast_count = len([r for r in records if not r['has_actual']])
    print(f"实际行情: {actual_count}天, 预测数据: {forecast_count}天")

    # 3. 计算月度涨跌幅
    monthly_chg = calc_monthly_chg(records)
    print("月度涨跌幅计算完成")

    # 4. 计算走势上涨率
    trend_uprate = calc_trend_uprate(records)
    print("走势上涨率计算完成")

    # 5. 生成HTML
    print("正在生成HTML工作台...")
    html = generate_html(records, monthly_chg, trend_uprate)

    # 6. 保存
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n工作台已生成: {output_path}")
    print(f"文件大小: {len(html)/1024:.1f} KB")
    print("数据更新完成!")

if __name__ == '__main__':
    main()
