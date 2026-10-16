import json
import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm
from sector_pairs.evaluation import date_hac
from sector_pairs.data import load_prices,sha256
from sector_pairs.config import Config,UNIVERSE

def test_duplicating_shared_exposure_does_not_create_independent_precision():
    rng=np.random.default_rng(5)
    dates=pd.bdate_range('2020-01-01',periods=100)
    y=rng.normal(size=100)
    fit=sm.OLS(y,np.ones((100,1))).fit()
    original=date_hac(fit,dates,5)
    repeated=sm.OLS(np.tile(y,5),np.ones((500,1))).fit()
    duplicated=date_hac(repeated,np.tile(dates,5),5)
    np.testing.assert_allclose(original,duplicated,rtol=1e-12)

def test_missing_sessions_remain_gaps_in_hac_calendar():
    dates=pd.bdate_range('2020-01-01',periods=3)
    observed=dates[[0,2]]
    fit=sm.OLS([1.,-1.],np.ones((2,1))).fit()
    compressed=date_hac(fit,observed,1)[0]
    with_gap=date_hac(fit,observed,1,calendar=dates)[0]
    assert with_gap>compressed

def test_loader_rejects_missing_provenance_and_modified_snapshot(tmp_path):
    path=tmp_path/'prices.csv'
    idx=pd.bdate_range('2004-09-29',periods=1200)
    pd.DataFrame(100.,index=idx,columns=UNIVERSE).to_csv(path)
    with pytest.raises(ValueError,match='manifest'):
        load_prices(path,Config())
    manifest={'source':'Synthetic unit-test fixture','adjustment':'Unit-test fixture only','sha256':sha256(path)}
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    prices,n_is,audit=load_prices(path,Config())
    assert len(prices)==1200 and n_is==840
    path.write_text(path.read_text().replace('100.0','101.0',1))
    with pytest.raises(ValueError,match='SHA256'):
        load_prices(path,Config())
