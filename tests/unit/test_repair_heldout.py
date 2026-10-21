"""Additional held-out analytic and harness-control checks, independent of repo tests.
Author: Hesham Salama <hesham.salama@rub.de>.
No live model calls: evaluation tests run a local subprocess probe.
"""
import json,math,os,subprocess,sys
from pathlib import Path
import numpy as np
import pytest
from tests.unit import test_independent_science as old

@pytest.mark.parametrize('nx,ny',[(9,13),(23,18),(40,51)])
@pytest.mark.parametrize('slope,intercept',[(0,.3),(.2,.2),(-.4,.7),(1.,0.)])
def test_oblique_contour(nx,ny,slope,intercept):
    # y=m*x+b stays inside [0,1]x[0,1]; exact segment length sqrt(1+m²).
    x=np.linspace(0,1,nx); y=np.linspace(0,1,ny)
    field=y[:,None]-slope*x[None,:]-intercept
    out=old.dq.compute_interface_area_2d(field.tolist(),0,1/(nx-1),1/(ny-1))
    assert out['interface_length']==pytest.approx(math.hypot(1,slope),abs=2e-13)

def test_circle_contour_converges():
    errs=[]
    for n in (24,48,96):
        x=np.linspace(-1,1,n)
        field=x[:,None]**2+x[None,:]**2
        length=old.dq.compute_interface_area_2d(field.tolist(),.55**2,2/(n-1),2/(n-1))['interface_length']
        errs.append(abs(length-2*math.pi*.55))
    assert errs[2]<errs[1]/3 and errs[1]<errs[0]/3
    assert errs[-1]<.002

@pytest.mark.parametrize('dimension',[1,2,3])
@pytest.mark.parametrize('n',[5,10,19])
def test_nodal_multilinear_integral(dimension,n):
    coords=np.linspace(0,1,n)
    grids=np.meshgrid(*([coords]*dimension),indexing='ij')
    field=np.ones([n]*dimension)
    for grid in grids: field*=1+grid
    spacing=old.dq.get_grid_spacing(dict(zip(('Lx','Ly','Lz')[:dimension],[1.]*dimension)),list(field.shape))
    result=old.dq.compute_integral(field.tolist(),spacing)
    assert result['integral']==pytest.approx(1.5**dimension,rel=1e-13)
    assert result['domain_volume']==pytest.approx(1.)

@pytest.mark.parametrize('n',[17,33,65])
def test_centroid_uses_same_quadrature(n):
    x=np.linspace(0,1,n);spacing=old.dq.get_grid_spacing({'Lx':1},[n])
    result=old.dq.compute_centroid(x.tolist(),spacing)
    # trapezoidal x² has exact error h²/6; denominator integral x=1/2.
    assert result['centroid_x']==pytest.approx(2/3+1/(3*(n-1)**2),rel=1e-13)

@pytest.mark.parametrize('p',[-2.,-.4,.2,1.7,3.2])
@pytest.mark.parametrize('h',[[.07,.19,.33],[.13,.27,.93],[.2,.4,.8]])
def test_signed_nonuniform_power_law(p,h):
    result=old.gci.compute_gci(h,[7+4*t**p for t in h])['results']
    assert result['observed_order']==pytest.approx(p,abs=1e-9)
    if p>0: assert result['extrapolated_value']==pytest.approx(7,abs=1e-8)
    else: assert result['extrapolated_value'] is None

@pytest.mark.parametrize('origin',[0.,-1e6,1e8])
@pytest.mark.parametrize('scale',[.125,1.,100.])
def test_surrogate_affine_coordinates(origin,scale):
    t=np.arange(-4,5,dtype=float);x=origin+scale*t;y=2+3*t+4*t*t
    result=old.surrogate.build_surrogate(x.tolist(),y.tolist(),'poly')
    assert result['fit_status']=='ok'
    assert result['metrics']['mse']<1e-20
    assert result['metrics']['cv_error']<1e-19
    assert result['fit_diagnostics']['rank']==3

@pytest.mark.parametrize('sg,bravais',[(1,'aP'),(5,'mC'),(22,'oF'),(79,'tI'),(146,'hR'),(168,'hP'),(225,'cF'),(229,'cI')])
def test_space_group_centering(sg,bravais):
    good=old.crystal.map_crystal(space_group=sg,bravais=bravais)
    assert not good['validation_warnings']
    wrong='cP' if bravais!='cP' else 'cI'
    assert old.crystal.map_crystal(space_group=sg,bravais=wrong)['validation_warnings']

@pytest.mark.parametrize('value',[float('nan'),float('inf'),'-Infinity'])
@pytest.mark.parametrize('key',['field_min','mass_initial'])
def test_bad_metrics_never_green(value,key):
    result=old.rv.validate_metrics({key:value,'mass_final':1,'field_max':2},0,2,.01)
    assert result['status']=='FAIL'

@pytest.mark.parametrize('velocity,diffusion,decay',[(.7,.2,.4),(.1,.9,0.),(0.,.8,.9)])
def test_recommended_combined_step_evolves_positive(velocity,diffusion,decay):
    out=old.check_cfl(velocity=velocity,diffusivity=diffusion,reaction_rate=decay,safety=.9)
    dt=out['recommended_dt']; u=np.zeros(80);u[40]=1
    for _ in range(100):
        u=u-velocity*dt*(u-np.roll(u,1))+diffusion*dt*(np.roll(u,1)-2*u+np.roll(u,-1))-decay*dt*u
        assert u.min()>=-1e-15 and u.max()<=1
    assert u.sum()==pytest.approx((1-decay*dt)**100,abs=1e-13)

def test_failed_and_corrupt_job(tmp_path):
    job={'job_id':'x','config_file':'config_x.json','status':'pending','end_time':None,'exit_code':None}
    (tmp_path/'result_x.json').write_text('{')
    assert old.jobs.detect_job_status(job.copy(),str(tmp_path))['status']=='pending'
    (tmp_path/'result_x.json').write_text('{}')
    (tmp_path/'error_x.log').write_text('solver failed')
    assert old.jobs.detect_job_status(job.copy(),str(tmp_path))['status']=='failed'

quality=old.module('skill-evaluator','run_quality_eval')
aggregate=old.module('skill-evaluator','aggregate_benchmark')
isolation=sys.modules['evaluation_isolation']

def test_real_child_process_environment_isolated(tmp_path,monkeypatch):
    monkeypatch.setenv('AMBIENT_AGENT_SENTINEL','contaminated')
    env=isolation.isolated_environment(tmp_path)
    proc=subprocess.run([sys.executable,'-c','import os,json;print(json.dumps(dict(home=os.environ["HOME"],ambient=os.getenv("AMBIENT_AGENT_SENTINEL"),codex=os.environ["CODEX_HOME"])))'],cwd=tmp_path,env=env,capture_output=True,text=True,check=True)
    data=json.loads(proc.stdout)
    assert data['ambient'] is None
    assert Path(data['home']).is_relative_to(tmp_path) and Path(data['codex']).is_relative_to(tmp_path)

def test_baseline_and_skill_workdirs(tmp_path):
    skill=tmp_path/'sample';skill.mkdir();(skill/'SKILL.md').write_text('sample')
    for cfg in (False,True):
        run=tmp_path/str(cfg)
        work=quality.prepare_run_dir(skill,run,'openai-codex',cfg,[],skill)
        skills=list(work.rglob('SKILL.md'))
        assert len(skills)==int(cfg)
        # Freshness enforcement rejects reusing a nonempty working directory.
        (work/'marker').write_text('used')
        with pytest.raises(ValueError): quality.prepare_run_dir(skill,run,'openai-codex',cfg,[],skill)

def test_token_totals_and_unknowns():
    assert quality._extract_tokens(json.dumps({'usage':{'total_tokens':30,'input_tokens':20,'output_tokens':10}}),'claude-code')==30
    assert quality._extract_tokens(json.dumps({'usage':{'input_tokens':0,'output_tokens':0}}),'claude-code')==0
    assert quality._extract_tokens(json.dumps({'usage':{'input_tokens':10}}),'claude-code') is None
    assert aggregate.stats([None,None])['mean'] is None
    result=aggregate.aggregate({'with_skill':[{'eval_id':1,'pass_rate':1.,'tokens':None}], 'without_skill':[{'eval_id':1,'pass_rate':0.,'tokens':50}]})
    assert result['delta']['tokens'] is None and result['delta']['pass_rate']=='+1.00'

def test_nonfinite_diagnostics_strict_json():
    result=old.condition.compute_condition(np.zeros((2,2)),2,1e-12,False)
    clean=old.condition.strict_payload({'results':result})
    json.dumps(clean,allow_nan=False)
    assert clean['results']['condition_number'] is None
    assert clean['nonfinite_diagnostics']['paths']

@pytest.mark.parametrize('configuration',['with_skill','without_skill'])
def test_quality_runner_real_controlled_process(tmp_path,monkeypatch,configuration):
    skill=tmp_path/'sample';skill.mkdir();(skill/'SKILL.md').write_text('fixture skill')
    (skill/'evals').mkdir();(skill/'evals/evals.json').write_text('GOLD_ANSWER_MUST_NOT_LEAK')
    monkeypatch.setenv('AMBIENT_AGENT_SENTINEL','contaminated')
    script='import os,json,pathlib;print(json.dumps(dict(home=os.environ["HOME"],ambient=os.getenv("AMBIENT_AGENT_SENTINEL"),skills=len(list(pathlib.Path.cwd().rglob("SKILL.md"))))))'
    def argv(cli,prompt,**kwargs):
        assert 'GOLD_ANSWER_MUST_NOT_LEAK' not in prompt
        return [sys.executable,'-c',script]
    monkeypatch.setattr(quality.A,'build_argv',argv)
    run=tmp_path/'run'
    result=quality.run_one(skill,{'id':1,'prompt':'controlled subprocess','expected_output':'GOLD_ANSWER_MUST_NOT_LEAK'},'openai-codex',configuration,run,None,skill,30,False)
    output=json.loads((run/'response.txt').read_text())
    assert result['exit_code']==0 and output['ambient'] is None
    assert output['skills']==int(configuration=='with_skill')
    assert Path(output['home']).is_relative_to(run)
    assert not list((run/'workdir').rglob('evals.json'))
    with pytest.raises(ValueError): quality.run_one(skill,{'prompt':'reuse'},'openai-codex',configuration,run,None,skill,30,False)

def test_trigger_process_failure_is_ungraded(tmp_path,monkeypatch):
    trigger=old.module('skill-evaluator','run_trigger_eval')
    skill=tmp_path/'sample';skill.mkdir();(skill/'SKILL.md').write_text('fixture')
    monkeypatch.setattr(trigger.A,'build_argv',lambda *a,**k:[sys.executable,'-c','print("SKILL.md");raise SystemExit(1)'])
    result=trigger.run_query(skill,'fixture','openai-codex',None,tmp_path/'run',30,False)
    assert result['exit_code']==1 and result['triggered'] is None and result['error']

def test_missing_usage_viewer_is_renderable(tmp_path):
    import importlib.util
    p=old.SRC/'skills/meta/skill-evaluator/eval-viewer/generate_review.py'
    spec=importlib.util.spec_from_file_location('heldout_viewer',p);viewer=importlib.util.module_from_spec(spec);spec.loader.exec_module(viewer)
    benchmark={'metadata':{'skill_name':'synthetic','evals_run':[]},'runs':[],
               'run_summary':{'with_skill':{'tokens':aggregate.stats([None])}}}
    html=viewer.render(benchmark)
    assert 'unknown' in html
