"""Contrato único para os CSVs analíticos de precipitação."""
import pandas as pd

COLUNAS = ['ponto_id','uf','latitude','longitude','data_inicio','data_fim_exclusiva',
           'frequencia','precipitacao_mm','dias_validos','dias_esperados',
           'cobertura','completo','fonte']

def salvar_padronizado(tabela, frequencia, pontos, destino):
    d=tabela.rename(columns={'date':'data_inicio','period':'data_inicio','mm':'precipitacao_mm'}).copy()
    d['data_inicio']=pd.to_datetime(d.data_inicio,utc=True)
    offset={'diaria':pd.offsets.Day(1),'mensal':pd.offsets.MonthBegin(1),'anual':pd.offsets.YearBegin(1)}[frequencia]
    d['data_fim_exclusiva']=d.data_inicio+offset
    if frequencia=='diaria':
        d['dias_validos']=d.precipitacao_mm.notna().astype(int)
        d['dias_esperados']=1
        d['completo']=d.dias_validos.eq(1)
    d['cobertura']=d.dias_validos/d.dias_esperados
    d['frequencia']=frequencia
    d['fonte']='meteomatics_mix'
    d=d.merge(pontos,on='uf',how='left',validate='many_to_one')
    if d[['latitude','longitude']].isna().any().any():raise ValueError('Ponto sem coordenadas')
    d['ponto_id']='ponto_'+d.uf.str.lower()+'_01'
    for c in ['data_inicio','data_fim_exclusiva']:d[c]=d[c].dt.strftime('%Y-%m-%d')
    d=d[COLUNAS].sort_values(['ponto_id','data_inicio'])
    if d.duplicated(['ponto_id','data_inicio','frequencia']).any():raise ValueError('Chave duplicada')
    d.to_csv(destino,index=False,encoding='utf-8',sep=',',decimal='.',na_rep='')
    return d
