"""Regression oracles from live-solver integration failures.
Author: Hesham Salama <hesham.salama@rub.de>.
"""
import importlib.util,json,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'skills/simulation-workflow/simulation-orchestrator/scripts/result_aggregator.py'
spec=importlib.util.spec_from_file_location('agg_live',P);agg=importlib.util.module_from_spec(spec);spec.loader.exec_module(agg)
@pytest.mark.parametrize('scale',[1e-300,1e-18,1.,1e150,1e300])
def test_statistics_scale_invariance(scale):
    r=agg.compute_statistics([scale,2*scale,3*scale])
    for key,value in [('min',1),('max',3),('mean',2),('std',1),('median',2)]:
        assert r[key]/scale==pytest.approx(value,rel=2e-14)
def test_cli_keeps_tiny_physical_statistics(tmp_path):
    campaign={'jobs':[{'job_id':'job_0000','config_file':'config_0000.json','config_path':str(tmp_path/'config_0000.json'),'status':'completed'}]}
    (tmp_path/'campaign.json').write_text(json.dumps(campaign))
    (tmp_path/'result_job_0000.json').write_text(json.dumps({'diffusion':1.234567891234e-12}))
    p=subprocess.run([sys.executable,str(P),'--campaign-dir',str(tmp_path),'--metric','diffusion','--json'],capture_output=True,text=True,check=True)
    out=json.loads(p.stdout)
    assert out['statistics']['min']==1.234567891234e-12
    assert out['statistics']['mean']==out['best_run']['value']
def test_md_correction_applicability():
    p=ROOT/'skills/simulation-workflow/md-analysis-planner/scripts/md_analysis_planner.py'
    result=json.loads(subprocess.check_output([sys.executable,str(p),'--system','solid','--goals','diffusion','--json'],text=True))
    warnings=' '.join(result['results']['warnings'])
    assert 'Do not apply' in warnings and 'ballistic' in warnings and 'isotropic bulk fluids' in warnings
