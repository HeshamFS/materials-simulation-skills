#!/usr/bin/env python3
"""
Unit tests for Performance Profiling Skill scripts.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from hypothesis import given, strategies as st, settings
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    # Create dummy decorators if hypothesis not available
    def given(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    settings = lambda **kwargs: lambda func: func
    st = None

# Add scripts directory to path
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / 'skills' / 'simulation-workflow' / 'performance-profiling' / 'scripts'))


class TestTimingAnalyzer(unittest.TestCase):
    """Tests for timing_analyzer.py"""
    
    def setUp(self):
        """Import timing_analyzer module"""
        import timing_analyzer
        self.module = timing_analyzer
    
    def test_parse_empty_log(self):
        """Test parsing an empty log file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("")
            log_path = f.name
        
        try:
            entries = self.module.parse_timing_log(log_path)
            self.assertEqual(entries, [])
        finally:
            os.unlink(log_path)
    
    def test_parse_timing_log_basic(self):
        """Test parsing a log with basic timing entries"""
        log_content = """
        Phase: Mesh Generation, Time: 12.34s
        Phase: Assembly, Time: 45.67s
        Phase: Solve, Time: 89.01s
        """
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(log_content)
            log_path = f.name
        
        try:
            entries = self.module.parse_timing_log(log_path)
            self.assertEqual(len(entries), 3)
            self.assertEqual(entries[0], ('Mesh Generation', 12.34))
            self.assertEqual(entries[1], ('Assembly', 45.67))
            self.assertEqual(entries[2], ('Solve', 89.01))
        finally:
            os.unlink(log_path)
    
    def test_aggregate_timings_single_occurrence(self):
        """Test aggregation with single occurrence per phase"""
        entries = [
            ('Phase A', 10.0),
            ('Phase B', 20.0),
            ('Phase C', 30.0)
        ]
        
        aggregated = self.module.aggregate_timings(entries)
        
        self.assertEqual(len(aggregated), 3)
        self.assertAlmostEqual(aggregated['Phase A']['total_time'], 10.0)
        self.assertAlmostEqual(aggregated['Phase A']['mean_time'], 10.0)
        self.assertEqual(aggregated['Phase A']['count'], 1)
        self.assertAlmostEqual(aggregated['Phase A']['percentage'], 16.666, places=2)
    
    def test_aggregate_timings_multiple_occurrences(self):
        """Test aggregation with multiple occurrences of same phase"""
        entries = [
            ('Solve', 10.0),
            ('Solve', 15.0),
            ('Solve', 20.0)
        ]
        
        aggregated = self.module.aggregate_timings(entries)
        
        self.assertEqual(len(aggregated), 1)
        self.assertAlmostEqual(aggregated['Solve']['total_time'], 45.0)
        self.assertAlmostEqual(aggregated['Solve']['mean_time'], 15.0)
        self.assertAlmostEqual(aggregated['Solve']['min_time'], 10.0)
        self.assertAlmostEqual(aggregated['Solve']['max_time'], 20.0)
        self.assertEqual(aggregated['Solve']['count'], 3)
    
    def test_identify_slowest_phases(self):
        """Test identification of slowest phases"""
        aggregated = {
            'Phase A': {'total_time': 10.0},
            'Phase B': {'total_time': 50.0},
            'Phase C': {'total_time': 30.0},
            'Phase D': {'total_time': 20.0}
        }
        
        slowest = self.module.identify_slowest_phases(aggregated, top_n=2)
        
        self.assertEqual(len(slowest), 2)
        self.assertEqual(slowest[0], 'Phase B')
        self.assertEqual(slowest[1], 'Phase C')
    
    def test_aggregate_empty_entries(self):
        """Test aggregation with empty entries list"""
        aggregated = self.module.aggregate_timings([])
        self.assertEqual(aggregated, {})
    
    def test_identify_slowest_empty(self):
        """Test slowest phase identification with empty data"""
        slowest = self.module.identify_slowest_phases({})
        self.assertEqual(slowest, [])


class TestScalingAnalyzer(unittest.TestCase):
    """Tests for scaling_analyzer.py"""
    
    def setUp(self):
        """Import scaling_analyzer module"""
        import scaling_analyzer
        self.module = scaling_analyzer
    
    def test_load_scaling_data_valid(self):
        """Test loading valid scaling data"""
        data = {
            'runs': [
                {'processors': 1, 'problem_size': 1000, 'time': 100.0},
                {'processors': 2, 'problem_size': 1000, 'time': 55.0}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(data, f)
            data_path = f.name
        
        try:
            runs = self.module.load_scaling_data(data_path)
            self.assertEqual(len(runs), 2)
            self.assertEqual(runs[0]['processors'], 1)
            self.assertEqual(runs[1]['processors'], 2)
        finally:
            os.unlink(data_path)
    
    def test_load_scaling_data_insufficient_runs(self):
        """Test error when fewer than 2 runs provided"""
        data = {
            'runs': [
                {'processors': 1, 'problem_size': 1000, 'time': 100.0}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(data, f)
            data_path = f.name
        
        try:
            with self.assertRaises(ValueError) as cm:
                self.module.load_scaling_data(data_path)
            self.assertIn('At least 2 runs required', str(cm.exception))
        finally:
            os.unlink(data_path)
    
    def test_compute_strong_scaling(self):
        """Test strong scaling computation"""
        runs = [
            {'processors': 1, 'time': 100.0},
            {'processors': 2, 'time': 55.0},
            {'processors': 4, 'time': 30.0}
        ]
        
        analysis = self.module.compute_strong_scaling(runs)
        
        self.assertEqual(analysis['type'], 'strong')
        self.assertEqual(analysis['baseline']['processors'], 1)
        self.assertEqual(analysis['baseline']['time'], 100.0)
        self.assertEqual(len(analysis['results']), 3)
        
        # Check first result (baseline)
        self.assertAlmostEqual(analysis['results'][0]['speedup'], 1.0)
        self.assertAlmostEqual(analysis['results'][0]['efficiency'], 1.0)
        
        # Check second result
        self.assertAlmostEqual(analysis['results'][1]['speedup'], 100.0 / 55.0, places=5)
        self.assertAlmostEqual(analysis['results'][1]['efficiency'], (100.0 / 55.0) / 2, places=5)
    
    def test_compute_weak_scaling(self):
        """Test weak scaling computation"""
        runs = [
            {'processors': 1, 'time': 100.0},
            {'processors': 2, 'time': 105.0},
            {'processors': 4, 'time': 110.0}
        ]
        
        analysis = self.module.compute_weak_scaling(runs)
        
        self.assertEqual(analysis['type'], 'weak')
        self.assertEqual(analysis['baseline']['processors'], 1)
        self.assertEqual(analysis['baseline']['time'], 100.0)
        
        # Check efficiencies
        self.assertAlmostEqual(analysis['results'][0]['efficiency'], 1.0)
        self.assertAlmostEqual(analysis['results'][1]['efficiency'], 100.0 / 105.0, places=5)
        self.assertAlmostEqual(analysis['results'][2]['efficiency'], 100.0 / 110.0, places=5)
    
    def test_efficiency_threshold_detection(self):
        """Test detection of efficiency threshold"""
        runs = [
            {'processors': 1, 'time': 100.0},
            {'processors': 2, 'time': 55.0},
            {'processors': 4, 'time': 35.0},  # efficiency = (100/35)/4 = 0.714
            {'processors': 8, 'time': 20.0}   # efficiency = (100/20)/8 = 0.625 < 0.70
        ]
        
        analysis = self.module.compute_strong_scaling(runs)
        
        self.assertEqual(analysis['efficiency_threshold_processors'], 8)


class TestMemoryProfiler(unittest.TestCase):
    """Tests for memory_profiler.py"""
    
    def setUp(self):
        """Import memory_profiler module"""
        import memory_profiler
        self.module = memory_profiler
    
    def test_estimate_field_memory(self):
        """Test field memory estimation"""
        mesh = {'nx': 100, 'ny': 100, 'nz': 100}
        fields = {
            'concentration': {'components': 2, 'bytes_per_value': 8},
            'temperature': {'components': 1, 'bytes_per_value': 8}
        }
        
        memory_gb = self.module.estimate_field_memory(mesh, fields)
        
        # Expected: 100*100*100 * (2+1) * 8 bytes = 24 MB = 0.0224 GB
        expected_gb = (100 * 100 * 100 * 3 * 8) / (1024 ** 3)
        self.assertAlmostEqual(memory_gb, expected_gb, places=5)
    
    def test_compute_total_memory(self):
        """Test total memory computation"""
        params = {
            'mesh': {'nx': 256, 'ny': 256, 'nz': 1},
            'fields': {
                'phi': {'components': 1, 'bytes_per_value': 8}
            },
            'solver': {'type': 'iterative', 'workspace_multiplier': 5},
            'processors': 4
        }
        
        profile = self.module.compute_total_memory(params)
        
        self.assertEqual(profile['mesh_points'], 256 * 256)
        self.assertGreater(profile['total_memory_gb'], 0)
        self.assertAlmostEqual(profile['per_process_gb'], profile['total_memory_gb'] / 4, places=5)
    
    def test_memory_warning_generation(self):
        """Test memory warning when usage exceeds available"""
        params = {
            'mesh': {'nx': 1000, 'ny': 1000, 'nz': 1000},
            'fields': {
                'phi': {'components': 10, 'bytes_per_value': 8}
            },
            'solver': {'type': 'iterative', 'workspace_multiplier': 10},
            'processors': 1
        }
        
        profile = self.module.compute_total_memory(params, available_gb=1.0)
        
        # Should have warnings since memory will exceed 1 GB
        self.assertGreater(len(profile['warnings']), 0)


class TestMemoryProfilerRobustness(unittest.TestCase):
    """Regression tests for memory_profiler.py bug fixes."""

    def setUp(self):
        import memory_profiler
        self.module = memory_profiler

    def test_negative_nx_raises(self):
        """Negative mesh dimension must raise ValueError."""
        mesh = {'nx': -10, 'ny': 100, 'nz': 100}
        fields = {'phi': {'components': 1, 'bytes_per_value': 8}}
        with self.assertRaises(ValueError):
            self.module.estimate_field_memory(mesh, fields)

    def test_zero_processors_raises(self):
        """Zero processors must raise ValueError (division by zero guard)."""
        params = {
            'mesh': {'nx': 10, 'ny': 10, 'nz': 1},
            'fields': {'phi': {'components': 1, 'bytes_per_value': 8}},
            'processors': 0
        }
        with self.assertRaises(ValueError):
            self.module.compute_total_memory(params)

    def test_negative_bytes_per_value_raises(self):
        """Negative bytes_per_value must raise ValueError."""
        mesh = {'nx': 10, 'ny': 10, 'nz': 1}
        fields = {'phi': {'components': 1, 'bytes_per_value': -8}}
        with self.assertRaises(ValueError):
            self.module.estimate_field_memory(mesh, fields)


class TestBottleneckDetector(unittest.TestCase):
    """Tests for bottleneck_detector.py"""
    
    def setUp(self):
        """Import bottleneck_detector module"""
        import bottleneck_detector
        self.module = bottleneck_detector
    
    def test_detect_timing_bottlenecks(self):
        """Test detection of timing bottlenecks"""
        timing_data = {
            'timing_data': {
                'phases': [
                    {'name': 'Linear Solver', 'percentage': 65.0},
                    {'name': 'Assembly', 'percentage': 25.0},
                    {'name': 'I/O', 'percentage': 10.0}
                ]
            }
        }
        
        bottlenecks = self.module.detect_timing_bottlenecks(timing_data, threshold=50.0)
        
        self.assertEqual(len(bottlenecks), 1)
        self.assertEqual(bottlenecks[0]['phase'], 'Linear Solver')
        self.assertEqual(bottlenecks[0]['severity'], 'medium')
    
    def test_generate_recommendations_solver_bottleneck(self):
        """Test recommendation generation for solver bottleneck"""
        bottlenecks = [
            {
                'type': 'timing',
                'phase': 'Linear Solver',
                'severity': 'high',
                'value': 70.0
            }
        ]
        
        recommendations = self.module.generate_recommendations(bottlenecks)
        
        self.assertGreater(len(recommendations), 0)
        self.assertEqual(recommendations[0]['category'], 'solver')
        self.assertIn('preconditioner', recommendations[0]['strategies'][0].lower())
    
    def test_generate_recommendations_no_bottlenecks(self):
        """Test recommendations when no bottlenecks detected"""
        recommendations = self.module.generate_recommendations([])
        
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]['priority'], 'low')
        self.assertIn('No significant bottlenecks', recommendations[0]['issue'])


# Property-Based Tests
@unittest.skipIf(not HYPOTHESIS_AVAILABLE, "Hypothesis not installed")
class TestTimingAnalyzerProperties(unittest.TestCase):
    """Property-based tests for timing analyzer"""
    
    def setUp(self):
        """Import timing_analyzer module"""
        import timing_analyzer
        self.module = timing_analyzer
    
    @given(
        timing_entries=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))),
                st.floats(min_value=0.001, max_value=10000.0, allow_nan=False, allow_infinity=False)
            ),
            min_size=1,
            max_size=100
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_aggregation_correctness(self, timing_entries):
        """
        Feature: performance-profiling, Property 3: Aggregation correctness
        
        For any set of timing entries for the same phase, the aggregated sum should equal
        the sum of all individual times, the mean should equal sum/count, the min should be
        the minimum value, and the max should be the maximum value.
        """
        aggregated = self.module.aggregate_timings(timing_entries)
        
        # Group entries by phase
        phase_times = {}
        for phase, time_val in timing_entries:
            if phase not in phase_times:
                phase_times[phase] = []
            phase_times[phase].append(time_val)
        
        # Verify aggregation correctness for each phase
        for phase, times in phase_times.items():
            self.assertIn(phase, aggregated)
            stats = aggregated[phase]
            
            # Check sum
            self.assertAlmostEqual(stats['total_time'], sum(times), places=5)
            
            # Check mean
            self.assertAlmostEqual(stats['mean_time'], sum(times) / len(times), places=5)
            
            # Check min
            self.assertAlmostEqual(stats['min_time'], min(times), places=5)
            
            # Check max
            self.assertAlmostEqual(stats['max_time'], max(times), places=5)
            
            # Check count
            self.assertEqual(stats['count'], len(times))
    
    @given(
        timing_entries=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))),
                st.floats(min_value=0.001, max_value=10000.0, allow_nan=False, allow_infinity=False)
            ),
            min_size=1,
            max_size=100
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_slowest_phase_identification(self, timing_entries):
        """
        Feature: performance-profiling, Property 2: Slowest phase identification correctness
        
        For any set of aggregated timing data, the identified slowest phases should be
        those with the highest total time values.
        """
        aggregated = self.module.aggregate_timings(timing_entries)
        
        if not aggregated:
            return
        
        slowest = self.module.identify_slowest_phases(aggregated, top_n=3)
        
        # Get all phases sorted by total time
        all_phases_sorted = sorted(aggregated.items(), key=lambda x: x[1]['total_time'], reverse=True)
        expected_slowest = [phase for phase, _ in all_phases_sorted[:3]]
        
        # Verify slowest phases match expected
        self.assertEqual(slowest, expected_slowest)


@unittest.skipIf(not HYPOTHESIS_AVAILABLE, "Hypothesis not installed")
class TestScalingAnalyzerProperties(unittest.TestCase):
    """Property-based tests for scaling analyzer"""
    
    def setUp(self):
        """Import scaling_analyzer module"""
        import scaling_analyzer
        self.module = scaling_analyzer
    
    @given(
        runs=st.lists(
            st.tuples(
                st.integers(min_value=1, max_value=1024),  # processors
                st.floats(min_value=0.1, max_value=10000.0, allow_nan=False, allow_infinity=False)  # time
            ),
            min_size=2,
            max_size=20,
            unique_by=lambda x: x[0]  # unique processor counts
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_strong_scaling_efficiency_formula(self, runs):
        """
        Feature: performance-profiling, Property 5: Strong scaling efficiency formula
        
        For any set of strong scaling runs with fixed problem size, the computed efficiency
        for N processors should equal (T_baseline / (N * T_N)) where T_baseline is the time
        for the smallest processor count and T_N is the time for N processors.
        """
        # Convert to dict format
        runs_dict = [{'processors': p, 'time': t} for p, t in runs]
        
        analysis = self.module.compute_strong_scaling(runs_dict)
        
        # Get baseline
        sorted_runs = sorted(runs_dict, key=lambda x: x['processors'])
        baseline_time = sorted_runs[0]['time']
        baseline_procs = sorted_runs[0]['processors']
        
        # Verify efficiency formula for each result
        for result in analysis['results']:
            procs = result['processors']
            time = result['time']
            
            # Expected efficiency = (T_baseline / T_N) / (N / N_baseline)
            expected_efficiency = (baseline_time / time) / (procs / baseline_procs)
            
            self.assertAlmostEqual(result['efficiency'], expected_efficiency, places=5)
    
    @given(
        runs=st.lists(
            st.tuples(
                st.integers(min_value=1, max_value=1024),  # processors
                st.floats(min_value=0.1, max_value=10000.0, allow_nan=False, allow_infinity=False)  # time
            ),
            min_size=2,
            max_size=20,
            unique_by=lambda x: x[0]  # unique processor counts
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_baseline_selection(self, runs):
        """
        Feature: performance-profiling, Property 7: Baseline selection correctness
        
        For any set of scaling runs, the baseline should be the run with the
        smallest processor count.
        """
        # Convert to dict format
        runs_dict = [{'processors': p, 'time': t} for p, t in runs]
        
        analysis = self.module.compute_strong_scaling(runs_dict)
        
        # Find minimum processor count
        min_procs = min(p for p, _ in runs)
        
        # Verify baseline matches minimum
        self.assertEqual(analysis['baseline']['processors'], min_procs)


if __name__ == '__main__':
    unittest.main()
