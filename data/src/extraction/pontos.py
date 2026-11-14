from chuva import *
from padronizacao import salvar_padronizado
from concurrent.futures import ThreadPoolExecutor
POINTS='-22.9110137,-43.2093727+-23.5506507,-46.6333824+-18.5264844,-44.1588654+-19.5687682,-40.1721991+-24.4842187,-51.8148872+-29.8425284,-53.7680577+-27.0628367,-51.114965+-15.9323662,-50.1392928+-12.2115009,-55.5716547+-19.5852564,-54.4794731+-15.7754462,-47.7970891+-9.6611661,-36.6502426+-12.285251,-41.9294776+-5.3264703,-39.7156073+-5.2085503,-45.3930262+-7.1219366,-36.7246845+-8.4116316,-37.5919699+-7.6992782,-42.5043787+-5.6781175,-36.4781776+-10.6743911,-37.3773519+-9.0478679,-70.5264976+1.3545442,-51.9161977+-3.1316333,-59.9825041+-4.7493933,-52.8973006+-10.943145,-62.8277863+2.135138,-61.3631922+-10.8855129,-48.3716912'
NAMES='RJ SP MG ES PR RS SC GO MT MS DF AL BA CE MA PB PE PI RN SE AC AP AM PA RO RR TO'.split()
OUT=ROOT/'dados_pontos';OUT.mkdir(exist_ok=True)

def fetch(year):
 raw=OUT/'brutos';raw.mkdir(exist_ok=True)
 p=raw/f'bruto_{year}.csv'
 if not p.exists():
  period=f'{year}-01-02T00:00:00Z--{year+1}-01-01T00:00:00Z:P1D'
  r=session().get(f'https://api.meteomatics.com/{period}/{PARAM}/{POINTS}/csv',params={'source':'mix'},timeout=180)
  if not r.ok:raise RuntimeError(f'{year}: HTTP {r.status_code}: {r.text[:250]}')
  p.write_text(r.text)
 d=pd.read_csv(p,sep=';')
 print(year,len(d),list(d.columns),flush=True)
 return d

def process(frames):
 d=pd.concat(frames,ignore_index=True)
 # Associação por coordenada, independente da ordem da resposta.
 latcol=next(c for c in d if c.lower() in ('lat','latitude'))
 loncol=next(c for c in d if c.lower() in ('lon','longitude'))
 coords=np.array([[float(x) for x in p.split(',')] for p in POINTS.split('+')])
 distance=np.max(np.abs(d[[latcol,loncol]].to_numpy()[:,None,:]-coords[None,:,:]),axis=2)
 nearest=distance.argmin(axis=1)
 if (distance[np.arange(len(d)),nearest]>1e-5).any():raise ValueError('Coordenada inesperada')
 if set(nearest)!=set(range(27)):raise ValueError('Faltam pontos na resposta')
 data=pd.DataFrame({'uf':np.array(NAMES)[nearest],'date':pd.to_datetime(d.validdate,utc=True)-pd.Timedelta(days=1),'mm':d[PARAM]})
 daily,monthly,annual,audit=aggregate(data)
 pontos=pd.DataFrame(coords,columns=['latitude','longitude']);pontos.insert(0,'uf',NAMES)
 for name,t in [('diaria',daily),('mensal',monthly),('anual',annual)]:
  salvar_padronizado(t,name,pontos,OUT/f'precipitacao_{name}_27_pontos_2005_2025.csv')
 audit.update({'ufs':sorted(daily.uf.unique()),'registros_diarios':len(daily),'ausentes':int(daily.mm.isna().sum()),'meses_incompletos':int((~monthly.completo).sum()),'anos_incompletos':int((~annual.completo).sum()),'fonte':'mix','representacao':'Pontos fornecidos pelo usuário, não médias estaduais','periodo':'2005-01-01/2025-12-31','dias':'UTC'})
 (OUT/'auditoria.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False))
 print(json.dumps(audit,ensure_ascii=False),flush=True)
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=2) as pool:frames=list(pool.map(fetch,range(2005,2026)))
 process(frames)
