"""Precipitação por UF, dias UTC, 2005–2025. Execute python chuva.py."""
import argparse, json, os
from io import StringIO
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER = os.getenv('METEOMATICS_USER', 'hackathon_nasa_space_apps_gama_andrew')
PASSWORD = os.getenv('METEOMATICS_PASSWORD', '93xz2fk508WegR36vb6I')
PARAM = 'precip_24h:mm'
ROOT = Path(__file__).resolve().parent
UF = dict(zip('11 12 13 14 15 16 17 21 22 23 24 25 26 27 28 29 31 32 33 35 41 42 43 50 51 52 53'.split(), 'RO AC AM RR PA AP TO MA PI CE RN PB PE AL SE BA MG ES RJ SP PR SC RS MS MT GO DF'.split()))

def session():
    s = requests.Session()
    s.auth = (USER, PASSWORD)
    s.mount('https://', HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429,500,502,503,504])))
    return s

def polygon(geometry):
    polys = [geometry['coordinates']] if geometry['type']=='Polygon' else geometry['coordinates']
    if any(len(p)>1 for p in polys):
        raise ValueError('Polígono com buracos: exige tratamento espacial explícito.')
    return 'U'.join('_'.join(f'{lat:.6f},{lon:.6f}' for lon,lat in p[0][:-1]) for p in polys)+':mean'

def clean(df):
    df = df.copy()
    if df.empty or df[['uf','date']].isna().any().any():
        raise ValueError('Dados vazios ou chave ausente.')
    df['date'] = pd.to_datetime(df['date'], utc=True, errors='raise')
    if not (df.date == df.date.dt.normalize()).all():
        raise ValueError('Horários não correspondem a dias UTC.')
    df['mm'] = pd.to_numeric(df.mm, errors='raise')
    bad = ~np.isfinite(df.mm) | (df.mm < 0)
    invalid = int(bad.sum())
    df.loc[bad,'mm'] = np.nan
    key = ['uf','date']
    if (df.groupby(key).mm.nunique(dropna=False)>1).any():
        raise ValueError('Duplicatas conflitantes por UF e data; não foram descartadas.')
    duplicates = int(df.duplicated(key).sum())
    return df.drop_duplicates(key).sort_values(key), {'duplicatas_identicas_removidas':duplicates,'valores_invalidos':invalid}

def aggregate(df, start='2005-01-01', end='2025-12-31'):
    daily, audit = clean(df)
    idx = pd.date_range(start,end,freq='D',tz='UTC')
    if not daily.date.isin(idx).all():
        raise ValueError('Datas fora do período.')
    frames=[]; monthly=[]; annual=[]
    for uf, part in daily.groupby('uf'):
        s = part.set_index('date').mm.reindex(idx)
        frames.append(pd.DataFrame({'uf':uf,'date':idx,'mm':s.to_numpy()}))
        for freq, target in [('MS',monthly),('YS',annual)]:
            count=s.resample(freq).count()
            expected = pd.Series(count.index.days_in_month,index=count.index) if freq=='MS' else pd.Series(np.where(count.index.is_leap_year,366,365),index=count.index)
            total=s.resample(freq).sum(min_count=1).where(count==expected)
            target.append(pd.DataFrame({'uf':uf,'period':count.index,'mm':total.to_numpy(),'dias_validos':count.to_numpy(),'dias_esperados':expected.to_numpy(),'completo':(count==expected).to_numpy()}))
    return pd.concat(frames,ignore_index=True),pd.concat(monthly,ignore_index=True),pd.concat(annual,ignore_index=True),audit

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',default='mix',help='Fonte; mix é exploratório, sem garantia de homogeneidade histórica.')
    ap.add_argument('--ufs',nargs='+',default=list(UF.values()),choices=list(UF.values()))
    a=ap.parse_args()
    out=ROOT/'dados'/a.source;out.mkdir(parents=True,exist_ok=True)
    features=json.loads((ROOT/'ufs.geojson').read_text())['features']
    s=session();all_rows=[]
    for f in features:
        code=str(f['properties']['codarea']);uf=UF[code]
        if uf not in a.ufs:continue
        loc=polygon(f['geometry'])
        for year in range(2005,2026):
            path=out/f'{uf}_{year}_bruto.csv'
            if not path.exists():
                # Cada intervalo termina no início do dia seguinte.
                period=f'{year}-01-02T00:00:00Z--{year+1}-01-01T00:00:00Z:P1D'
                url=f'https://api.meteomatics.com/{period}/{PARAM}/{loc}/csv'
                r=s.get(url,params={'source':a.source},timeout=180)
                if not r.ok:raise RuntimeError(f'{uf}/{year}: HTTP {r.status_code}: {r.text[:400]}')
                frame=pd.read_csv(StringIO(r.text),sep=';')
                if not {'validdate',PARAM}.issubset(frame):raise ValueError('Resposta sem colunas esperadas.')
                path.write_text(r.text)
            frame=pd.read_csv(path,sep=';')
            all_rows.append(pd.DataFrame({'uf':uf,'date':pd.to_datetime(frame.validdate,utc=True)-pd.Timedelta(days=1),'mm':frame[PARAM]}))
            print(uf,year,len(frame),flush=True)
        # Salva também progresso: nunca mistura regiões ainda não coletadas.
        daily,month,annual,audit=aggregate(pd.concat(all_rows,ignore_index=True))
        for name,table in [('diaria',daily),('mensal',month),('anual',annual)]:table.to_csv(out/f'{name}.csv',index=False)
        audit.update({'fonte':a.source,'ufs_concluidas':sorted(daily.uf.unique()),'periodo':'2005-01-01 a 2025-12-31','dias_ausentes':int(daily.mm.isna().sum()),'meses_incompletos':int((~month.completo).sum()),'anos_incompletos':int((~annual.completo).sum()),'espacial':'Média do serviço no polígono IBGE simplificado; não afirmar ponderação exata por área.','homogeneidade':'mix exploratório; validar fonte consistente antes de inferir tendências.'})
        (out/'auditoria.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
