"""Independent analytic oracles and counterexamples; no source modifications.

Author: Hesham Salama <hesham.salama@rub.de>
Passing tests qualify only the equations and domains explicitly tested here.
"""
import importlib.util
import math
from pathlib import Path
import sys
import numpy as np
import pytest

SRC = Path(__file__).resolve().parents[2]
def module(skill, name):
    p = next(SRC.glob('skills/*/' + skill + '/scripts/' + name + '.py'))
    spec = importlib.util.spec_from_file_location('audit_'+skill.replace('-','_')+'_'+name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod

cfl = module('numerical-stability','cfl_checker')
vn = module('numerical-stability','von_neumann_analyzer')
stencil = module('differentiation-schemes','stencil_generator')
gci = module('convergence-study','gci_calculator')
href = module('convergence-study','h_refinement')
dtref = module('convergence-study','dt_refinement')
rv = module('simulation-validator','result_validator')
dq = module('post-processing','derived_quantities')
jac = module('nonlinear-solvers','jacobian_diagnostics')
res = module('linear-solvers','residual_norms')
tp = module('time-stepping','timestep_planner')
md = module('md-analysis-planner','md_analysis_planner')
crystal = module('ontology-mapper','crystal_mapper')
surrogate = module('parameter-optimization','surrogate_builder')
doe = module('parameter-optimization','doe_generator')
grid = module('mesh-generation','grid_sizing')
error = module('numerical-integration','error_norm')
statistics = module('post-processing','statistical_analyzer')
jobs = module('simulation-orchestrator','job_tracker')
condition = module('numerical-stability','matrix_condition')

def check_cfl(**kw):
    args = dict(dx=1.,dt=1.,velocity=None,diffusivity=None,reaction_rate=None,dimensions=1,
                scheme='explicit',advection_limit=None,diffusion_limit=None,reaction_limit=None,safety=1.)
    args.update(kw)
    return cfl.compute_cfl(**args)

@pytest.mark.parametrize('dimension',[1,2,3])
@pytest.mark.parametrize('fraction',[0.01,0.3,0.99,1.0,1.01,2.0])
@pytest.mark.parametrize('dx',[1e-5,0.1,10.])
def test_pure_diffusion_stability_matches_nyquist(dimension,fraction,dx):
    # Cartesian centered Laplacian: Nyquist eigenvalue is -4*d*D/dx**2.
    D=0.17
    dt=fraction*dx*dx/(2*dimension*D)
    gain=abs(1.-4*dimension*D*dt/dx**2)
    assert check_cfl(dx=dx,dt=dt,diffusivity=D,dimensions=dimension)['stable'] == (gain<=1.+1e-12)

def test_combined_advection_diffusion_must_not_false_certify():
    # Forward Euler + first-order upwind advection + centered diffusion.
    # C=0.8 and Fo=0.4 separately pass, but C+2Fo=1.6>1.
    result=check_cfl(velocity=.8,diffusivity=.4)
    nyquist_gain=abs(1-2*.8-4*.4)
    assert nyquist_gain == pytest.approx(2.2)
    assert result['stable'] is not True, result

def test_negative_diffusion_must_not_be_certified_dissipative():
    result=check_cfl(diffusivity=-.1)
    # u_t=-0.1 u_xx has growing Fourier modes, not the heat stability bound.
    assert result['stable'] is not True, result

def test_cfl_safety_factor_must_not_recommend_unstable_dt():
    try:
        result=check_cfl(diffusivity=1.,dt=.1,safety=2.)
    except ValueError:
        return
    assert result['recommended_dt']<=.5, result

@pytest.mark.parametrize('r',[0.,.01,.25,.49,.5,.5001,.75,2.])
def test_von_neumann_ftcs_analytic_maximum(r):
    out=vn.compute_amplification(np.array([r,1-2*r,r]),1.,2049,None,None,None)['results']
    assert out['max_amplification']==pytest.approx(max(1.,abs(1-4*r)),abs=1e-12)

@pytest.mark.parametrize('order',range(1,7))
@pytest.mark.parametrize('accuracy',[2,4,6,8])
@pytest.mark.parametrize('scheme',['central','forward','backward'])
def test_stencil_polynomial_moments(order,accuracy,scheme):
    # Taylor identities independently define a valid derivative stencil.
    result=stencil.generate_stencil(order,accuracy,scheme,1.,None)
    x=np.array(result['offsets'],dtype=float)
    w=np.array(result['coefficients'])
    for power in range(len(x)):
        terms=w*x**power
        expected=math.factorial(order) if power==order else 0.
        residual=abs(math.fsum(terms)-expected)
        # Account for cancellation/conditioning in high-order one-sided moments.
        assert residual<=2e-12*max(1.,math.fsum(abs(terms))), (power,residual)

@pytest.mark.parametrize('p',[.5,1.,2.,3.,4.])
@pytest.mark.parametrize('offset',[-2.,0.,3.])
@pytest.mark.parametrize('ratios',[(2.,2.),(1.5,2.),(2.,1.5)])
def test_gci_power_law_oracle(p,offset,ratios):
    h=[.1,.1*ratios[0],.1*ratios[0]*ratios[1]]
    f=[offset+2*x**p for x in h]
    result=gci.compute_gci(h,f)['results']
    assert result['observed_order']==pytest.approx(p,rel=1e-7,abs=1e-7)
    assert result['extrapolated_value']==pytest.approx(offset,abs=1e-8)

def test_gci_divergence_must_not_be_certified():
    # q(h)=100+1/h diverges; no finite Richardson estimate is justified.
    result=gci.compute_gci([1.,.5,.25],[101.,102.,104.])['results']
    assert result['in_asymptotic_range'] is not True, result
    assert result['extrapolated_value'] is None, result

@pytest.mark.parametrize('spacings',[[1.,1.,1.],[1.,.5,.5]])
def test_gci_duplicate_grids_rejected_cleanly(spacings):
    with pytest.raises(ValueError):
        gci.compute_gci(spacings,[3.,2.,1.])

@pytest.mark.parametrize('p',[1.,2.,3.])
def test_h_refinement_unequal_ratios_correct_or_rejected(p):
    h=[.9,.3,.15]
    f=[2+3*x**p for x in h]
    try:
        result=href.compute_h_refinement(h,f,p)['results']
    except ValueError:
        return
    assert result['mean_order']==pytest.approx(p,rel=1e-8), result

def test_h_refinement_oscillatory_sequence_not_green():
    result=href.compute_h_refinement([.4,.2,.1,.05],[1.16,.96,1.01,.9975],2.)['results']
    assert result['in_asymptotic_range'] is not True, result

@pytest.mark.parametrize('energies',[[float('inf'),1.],[1.,float('-inf')],[float('nan')]])
def test_validator_nonfinite_energy_not_pass(energies):
    result=rv.validate_metrics({'energy_history':energies},None,None,1e-3,True)
    assert result['status']!='PASS', result

def test_validator_detects_energy_spike():
    result=rv.validate_metrics({'energy_history':[3.,2.,2.5,1.]},None,None,1e-3,True)
    assert result['status']=='FAIL'

def test_validator_missing_data_is_not_validation():
    assert rv.validate_metrics({},None,None,1e-3)['status']=='INSUFFICIENT_DATA'

@pytest.mark.parametrize('n',[3,5,11,21])
def test_node_centered_constant_integral(n):
    # get_grid_spacing explicitly derives nodal spacing L/(n-1).
    # A constant must integrate exactly to domain length under either convention.
    field=[1.]*n
    spacing=dq.get_grid_spacing({'Lx':1.},[n])
    result=dq.compute_integral(field,spacing)
    assert result['integral']==pytest.approx(1.,abs=1e-12),result

@pytest.mark.parametrize('nx,ny',[(4,7),(17,11)])
def test_affine_2d_gradient(nx,ny):
    dx,dy=.12,.37
    field=[[2*i*dx-3*j*dy+5 for i in range(nx)] for j in range(ny)]
    result=dq.compute_gradient_magnitude(field,{'dx':dx,'dy':dy,'dz':1.})
    assert np.allclose(result['gradient_magnitude'],math.sqrt(13),atol=1e-12)

def test_degenerate_2d_gradient_handled():
    try:
        result=dq.compute_gradient_magnitude([[0.,1.,2.]],{'dx':1.,'dy':1.,'dz':1.})
    except ValueError:
        return
    assert np.allclose(result['gradient_magnitude'],1.)

@pytest.mark.parametrize('n',[11,21,41])
def test_anisotropic_straight_interface_length(n):
    # Vertical iso-line in a 1x4 box has exact length 4 independent of grid.
    field=[[i/(n-1) for i in range(n)] for j in range(n)]
    result=dq.compute_interface_area_2d(field,.53,1/(n-1),4/(n-1))
    assert result['interface_length']==pytest.approx(4.,rel=.05), result

@pytest.mark.parametrize('scale',[1e-40,1e-20,1.,1e20])
def test_jacobian_condition_invariant_under_unit_scaling(scale):
    result=jac.diagnose_jacobian(np.eye(3)*scale)
    assert result['condition_number']==pytest.approx(1.),result
    assert result['rank_deficient'] is False
    assert result['jacobian_quality']!='near-singular',result

@pytest.mark.parametrize('scale',[1e-200,1e-100,1.,1e100,1e200])
def test_residual_norm_matches_hypot_without_over_underflow(scale):
    result=res.compute_norms([3*scale,4*scale])
    assert result['l2']==pytest.approx(math.hypot(3*scale,4*scale),rel=1e-14,abs=0),result

def test_timestep_infeasible_lower_bound_not_recommended():
    try:
        result=tp.plan_timestep(1.,.01,1.,.1,None,0,'linear',10)
    except ValueError:
        return
    assert result['dt_recommended']<=.01,result

@pytest.mark.parametrize('goal',['vacf','vdos','stress-strain'])
def test_md_missing_required_observable_stays_blocked(goal):
    result=md.plan_md_analysis('test',[goal],'lammps',False,False,False,None)
    assert result['analysis_plan'][0]['status']=='blocked'

@pytest.mark.parametrize('n',[32,64,128])
def test_real_heat_evolution_conserves_mass_and_dissipates(n):
    # Actual periodic heat integration using shipped stencil and time limit.
    # Analytic u=2+exp(-4*pi^2*t)*sin(2*pi*x); no external solver is claimed.
    dx=1/n
    dt0=check_cfl(dx=dx,dt=1e-8,diffusivity=1.,safety=.8)['recommended_dt']
    steps=math.ceil(.01/dt0)
    dt=.01/steps
    weights=stencil.generate_stencil(2,2,'central',dx,None)
    x=np.arange(n)*dx
    u=2+np.sin(2*np.pi*x)
    e0=float(np.sum((u-2)**2))
    for _ in range(steps):
        lap=sum(w*np.roll(u,-o) for w,o in zip(weights['coefficients'],weights['offsets']))
        u=u+dt*lap
    exact=2+np.exp(-4*np.pi*np.pi*.01)*np.sin(2*np.pi*x)
    assert abs(np.mean(u)-2)<2e-13
    assert np.sum((u-2)**2)<e0
    assert np.max(abs(u-exact))<2/n**2

@pytest.mark.parametrize('p',[1.,2.,3.])
def test_dt_refinement_unequal_ratios_correct_or_rejected(p):
    dt=[.9,.3,.15]
    f=[2+3*x**p for x in dt]
    try:
        result=dtref.compute_dt_refinement(dt,f,p)['results']
    except ValueError:
        return
    assert result['mean_order']==pytest.approx(p,rel=1e-8),result

def test_crystal_impossible_metric_rejected_or_warned():
    # Every individual angle is within (0,180), but Gram determinant < 0.
    a,b,g=map(math.radians,[10,10,170])
    gram=1+2*math.cos(a)*math.cos(b)*math.cos(g)-math.cos(a)**2-math.cos(b)**2-math.cos(g)**2
    assert gram<0
    try:
        result=crystal.map_crystal(system='triclinic',a=1.,b=2.,c=3.,alpha=10.,beta=10.,gamma=170.)
    except ValueError:
        return
    assert result['validation_warnings'],result

def test_crystal_incompatible_bravais_and_space_group_flagged():
    # SG 225 Fm-3m is cubic F, incompatible with hexagonal primitive hP.
    try:
        result=crystal.map_crystal(bravais='hP',space_group=225,a=3.)
    except ValueError:
        return
    assert result['validation_warnings'],result

@pytest.mark.parametrize('shift',[0.,100.,1e4,1e6])
def test_polynomial_surrogate_coordinate_origin_invariance(shift):
    x=[shift+t for t in [-2.,-1.,0.,1.,2.]]
    y=[4.,1.,0.,1.,4.]
    result=surrogate.build_surrogate(x,y,'poly')
    assert result['metrics']['mse']<1e-10,result

@pytest.mark.parametrize('seed',[0,1,917])
@pytest.mark.parametrize('dim',[1,3,10])
def test_lhs_stratification_and_reproducibility(seed,dim):
    a=doe.generate_doe(dim,17,'lhs',seed)['samples']
    b=doe.generate_doe(dim,17,'lhs',seed)['samples']
    assert a==b
    for column in zip(*a):
        assert sorted(int(x*17) for x in column)==list(range(17))

@pytest.mark.parametrize('n',[3,10,500])
@pytest.mark.parametrize('dim',[1,2,3])
def test_grid_resolution_and_length_consistent(n,dim):
    result=grid.compute_grid(1.,n,dim,None)
    assert result['counts']==[n]*dim
    assert result['dx']*n==pytest.approx(1.)

@pytest.mark.parametrize('scale',[1e-200,1.,1e200])
def test_error_rms_stable_floating_point_scale(scale):
    norm,*_=error.compute_error_norm([3*scale,4*scale],None,[1.,1.],1e-3,1e-6,'rms',0.)
    assert norm==pytest.approx(math.hypot(3*scale,4*scale)/math.sqrt(2),rel=1e-14,abs=0)

@pytest.mark.parametrize('power',[3,4])
def test_reported_standardized_moments_match_definition(power):
    # Independently compute moments using the empirical distribution (1/n).
    values=[0.,1.,2.,6.]
    mean=sum(values)/len(values)
    m2=sum((v-mean)**2 for v in values)/len(values)
    expected=sum((v-mean)**power for v in values)/len(values)/m2**(power/2)
    stats=statistics.compute_basic_statistics(values)
    if power==3:
        actual=statistics.compute_skewness(values,stats['mean'],stats['std'])
    else:
        expected-=3
        actual=statistics.compute_kurtosis(values,stats['mean'],stats['std'])
    assert actual==pytest.approx(expected,abs=1e-12)

def test_failed_job_not_overridden_by_existing_result(tmp_path):
    # Failed solvers can leave a partially written result. An explicit nonzero
    # exit status must not be changed to completed merely because that file exists.
    (tmp_path/'result_job_0000.json').write_text('{')
    job=dict(job_id='job_0000',config_file='config_0000.json',status='failed',exit_code=1,end_time=None)
    result=jobs.detect_job_status(job,str(tmp_path))
    assert result['status']=='failed',result

@pytest.mark.parametrize('name,order',[('1',1),('2',2),('-1',-1),('inf',np.inf),('-inf',-np.inf),('fro','fro')])
def test_all_advertised_matrix_norms_work(name,order):
    matrix=np.array([[4.,1.],[1.,3.]])
    result=condition.compute_condition(matrix,condition.parse_norm(name),1e-8,False)
    assert result['condition_number']==pytest.approx(np.linalg.cond(matrix,p=order))
