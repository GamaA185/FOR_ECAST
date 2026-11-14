import unittest
import pandas as pd
import numpy as np
from chuva import aggregate,clean
class Tests(unittest.TestCase):
 def data(self,year=2020):
  dates=pd.date_range(f'{year}-01-01',f'{year}-12-31',tz='UTC')
  return pd.DataFrame({'uf':'RJ','date':dates,'mm':1.})
 def test_leap(self):
  _,m,a,_=aggregate(self.data(),'2020-01-01','2020-12-31')
  self.assertEqual(m.iloc[1].mm,29);self.assertEqual(a.iloc[0].mm,366)
 def test_normal_year(self):
  self.assertEqual(aggregate(self.data(2021),'2021-01-01','2021-12-31')[2].iloc[0].mm,365)
 def test_missing_not_zero(self):
  _,m,a,_=aggregate(self.data().iloc[1:],'2020-01-01','2020-12-31')
  self.assertTrue(pd.isna(m.iloc[0].mm));self.assertTrue(pd.isna(a.iloc[0].mm))
 def test_duplicate_identical(self):
  d=self.data();out,report=clean(pd.concat([d,d.iloc[:1]]))
  self.assertEqual(len(out),366);self.assertEqual(report['duplicatas_identicas_removidas'],1)
 def test_duplicate_conflict(self):
  d=self.data();extra=d.iloc[:1].copy();extra['mm']=2
  with self.assertRaises(ValueError):clean(pd.concat([d,extra]))
 def test_equal_values_different_dates_valid(self):
  self.assertEqual(clean(self.data())[1]['duplicatas_identicas_removidas'],0)
 def test_invalid(self):
  d=self.data();d.loc[0,'mm']=-999;d.loc[1,'mm']=np.inf
  out,r=clean(d);self.assertEqual(r['valores_invalidos'],2);self.assertTrue(out.mm.iloc[:2].isna().all())
 def test_separate_states(self):
  d=self.data();e=d.copy();e.uf='SP';e.mm=2
  a=aggregate(pd.concat([d,e]),'2020-01-01','2020-12-31')[2]
  self.assertEqual(a.set_index('uf').loc['SP','mm'],732)
 def test_incomplete_boundary(self):
  d=self.data().iloc[:10]
  self.assertTrue(pd.isna(aggregate(d,'2020-01-01','2020-01-10')[1].iloc[0].mm))
 def test_shift(self):
  dates=pd.to_datetime(['2005-01-02T00:00:00Z','2006-01-01T00:00:00Z'])-pd.Timedelta(days=1)
  self.assertEqual(str(dates[0].date()),'2005-01-01');self.assertEqual(str(dates[1].date()),'2005-12-31')
if __name__=='__main__':unittest.main()
