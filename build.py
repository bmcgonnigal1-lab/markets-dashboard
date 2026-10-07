import json,datetime,zoneinfo,math
import yfinance as yf
S=json.load(open('static.json'));fail=[]
def rsi(c,n=14):
    if len(c)<n+1: return None
    d=[c[i]-c[i-1] for i in range(1,len(c))]
    ag=sum(max(x,0) for x in d[:n])/n; al=sum(max(-x,0) for x in d[:n])/n
    for x in d[n:]: ag=(ag*(n-1)+max(x,0))/n; al=(al*(n-1)+max(-x,0))/n
    return 100.0 if al==0 else 100-100/(1+ag/al)
out=[]
for s in S:
    d=dict(s); y=s['yahoo']
    try:
        t=yf.Ticker(y); h=t.history(period='2y',interval='1d',auto_adjust=False)
        c=[float(x) for x in h['Close'].dropna()]
        if len(c)<2: raise Exception('no data')
        px=c[-1]; d['Price']=px; d['Chg']=px-c[-2]; d['Chg %']=px/c[-2]-1
        w=h['Close'].dropna(); last=w.index[-1]; yr=w[w.index>last-datetime.timedelta(days=365)]
        hi=float(h['High'][yr.index].max()); lo=float(h['Low'][yr.index].min())
        d['52w High']=hi; d['52w Low']=lo; d['% of 52w Range']=(px-lo)/(hi-lo) if hi>lo else None
        for k,n in (('SMA50',50),('SMA200',200)):
            d[k]=sum(c[-n:])/n if len(c)>=n else None
        d['vs 50d']=px/d['SMA50']-1 if d['SMA50'] else None
        d['vs 200d']=px/d['SMA200']-1 if d['SMA200'] else None
        d['Trend']=('Above 200d' if px>=d['SMA200'] else 'Below 200d') if d['SMA200'] else 'n/a'
        d['RSI(14)']=rsi(c); d['spark']=c[-60:]
        try: d['Mkt Cap (bn, local ccy)']=t.fast_info['market_cap']/1e9
        except Exception: d['Mkt Cap (bn, local ccy)']=None
        try: d['P/E (TTM)']=t.info.get('trailingPE')
        except Exception: d['P/E (TTM)']=None
        d['asof']=str(last.date())
    except Exception as e:
        fail.append(f'{y}: {e}'); d['spark']=[]
    out.append(d)
ts=datetime.datetime.now(zoneinfo.ZoneInfo('America/New_York')).strftime('%b %-d, %Y %-I:%M %p ET')
html=open('template.html').read().replace('__DATA__',json.dumps(out,default=str).replace('NaN','null')).replace('__TS__',ts)
html=html.replace('Google Finance via sheet (quotes may be delayed ~20 min)','Yahoo Finance via yfinance (may be delayed)'+(' · failed: '+', '.join(f.split(':')[0] for f in fail) if fail else ''))
open('index.html','w').write(html); json.dump({'built':ts,'failed':fail},open('status.json','w'))
print(ts,'failed:',fail)
