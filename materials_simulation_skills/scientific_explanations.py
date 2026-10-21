"""Deterministic explanations for four audited tool outputs.

Author: Hesham Salama <hesham.salama@rub.de>.
Consume JSON captured directly from a trusted tool invocation after validating
input fidelity. This renderer is not a validator for arbitrary or model-written
JSON. It deliberately does not accept, edit, or repeat a model's free prose.
"""
import argparse
import json
import math
import sys

TOOLS = ('crystal_mapper', 'h_refinement', 'cfl_checker', 'md_analysis_planner')

def finite(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError('Expected a finite numeric tool result')
    return f'{value:.12g}'

def explain(tool, payload):
    """Render task-scoped evidence; None means no justified yes/no decision."""
    if tool not in TOOLS:
        raise ValueError('Unsupported tool; no grounded explanation available')
    if tool == 'crystal_mapper':
        r=payload['results'];e=r['bravais_evidence'];declared=e['declared_bravais'];required=e['space_group_required_bravais']
        reason=f"Declared Bravais type: {declared or 'unresolved'}. Space group {e['space_group']} requires {required or 'unresolved'} in its standard setting."
        decision=None if declared is None or required is None else declared==required and not r['validation_warnings']
        reason+=' These declarations '+('agree.' if declared==required else 'conflict.') if declared and required else ' The declarations are incomplete.'
        if r['validation_warnings']:reason+=' Warnings: '+'; '.join(r['validation_warnings'])
        reason+=' BCC means cI and FCC means cF; a conflict does not rename either lattice. This checks declarations, not atomic symmetry.'
    elif tool == 'h_refinement':
        r=payload['results'];e=r['order_comparison'];x=r['extrapolation_evidence']
        decision=e['matches_expected']
        reason='Observed order p='+finite(e['observed'])+' (dimensionless).' if e['observed'] is not None else 'Observed order is unresolved.'
        if e['expected'] is not None:
            reason+=' Expected order='+finite(e['expected'])+'.'
        if e['relative_difference'] is not None:
            reason+=' Relative order difference='+finite(e['relative_difference'])+'; allowed tolerance='+finite(e['relative_tolerance'])+'.'
        elif e.get('relative_difference_overflow'):
            reason+=' Relative order difference exceeds finite floating-point range and fails the tolerance.'
        if x['value'] is not None:
            reason+=' Extrapolated observable='+finite(x['value'])+' in input-observable units, using '+x['order_basis']+' order. This value is not the convergence order.'
        else:reason+=' No justified Richardson estimate is available.'
        reason+=' Order agreement is not proof of physical accuracy or of an asymptotic regime.'
    elif tool == 'cfl_checker':
        decision=payload['stable'];parts=[]
        for e in payload['component_checks']:
            relation='within' if e['within_separate_limit'] else 'above'
            parts.append(e['component']+' metric '+finite(e['value'])+' is '+relation+' its separate limit '+finite(e['limit'])+'.')
        if payload['combined_load'] is not None:
            parts.append('Combined normalized load='+finite(payload['combined_load'])+'; sufficient unsplit monotonicity bound=1 (tolerance 1e-12).')
        parts.append('The bound is '+('satisfied.' if decision is True else 'not satisfied.' if decision is False else 'not certified.'))
        parts.append(payload['assumptions']);reason=' '.join(parts)
    else:
        r=payload['results'];plan=r['analysis_plan'];states=[p['status'] for p in plan]
        decision=False if 'blocked' in states else True if states and all(s=='ready' for s in states) else None
        reason='; '.join(p['goal']+': '+p['status'] for p in plan)+'.'
        reason+=' Required data: '+', '.join(r['required_data'])+'.'
        if r['warnings']:reason+=' '+' '.join(r['warnings'])
        reason+=' This is data-readiness planning, not validation of an estimated material property.'
    if decision is not None and not isinstance(decision,bool):raise ValueError('Invalid decision type')
    return dict(tool=tool,decision=decision,reason=reason,provenance='deterministic rendering of trusted tool output',model_prose_used=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tool',choices=TOOLS,required=True);args=p.parse_args()
    try:
        result=explain(args.tool,json.load(sys.stdin));print(json.dumps(result,indent=2,allow_nan=False))
    except (KeyError,TypeError,ValueError) as exc:
        print(json.dumps({'error':str(exc)}),file=sys.stderr);return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
