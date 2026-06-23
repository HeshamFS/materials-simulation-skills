#!/usr/bin/env python3
"""
Integration tests for Performance Profiling Skill CLI tools.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / 'skills' / 'simulation-workflow' / 'performance-profiling' / 'scripts'
FIXTURES_DIR = REPO_ROOT / 'tests' / 'fixtures' / 'performance-profiling'


class TestPerformanceProfilingCLI(unittest.TestCase):
    """Integration tests for performance profiling CLI tools"""
    
    def run_script(self, script_name, args):
        """Helper to run a script and return output"""
        script_path = SCRIPTS_DIR / script_name
        cmd = [sys.executable, str(script_path)] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result
    
    def test_timing_analyzer_cli(self):
        """Test timing analyzer CLI with example data"""
        log_file = FIXTURES_DIR / 'sample_timing_log.txt'
        result = self.run_script('timing_analyzer.py', [
            '--log', str(log_file),
            '--json'
        ])
        
        self.assertEqual(result.returncode, 0)
        
        # Parse JSON output
        output = json.loads(result.stdout)
        self.assertIn('inputs', output)
        self.assertIn('results', output)
        self.assertIn('phases', output['results'])
        self.assertGreater(len(output['results']['phases']), 0)
    
    def test_scaling_analyzer_cli(self):
        """Test scaling analyzer CLI with example data"""
        data_file = FIXTURES_DIR / 'sample_scaling_data.json'
        result = self.run_script('scaling_analyzer.py', [
            '--data', str(data_file),
            '--type', 'strong',
            '--json'
        ])
        
        self.assertEqual(result.returncode, 0)
        
        # Parse JSON output
        output = json.loads(result.stdout)
        self.assertIn('inputs', output)
        self.assertIn('results', output)
        self.assertEqual(output['results']['type'], 'strong')
        self.assertGreater(len(output['results']['results']), 0)
    
    def test_memory_profiler_cli(self):
        """Test memory profiler CLI with example data"""
        params_file = FIXTURES_DIR / 'sample_simulation_params.json'
        result = self.run_script('memory_profiler.py', [
            '--params', str(params_file),
            '--available-gb', '16.0',
            '--json'
        ])
        
        self.assertEqual(result.returncode, 0)
        
        # Parse JSON output
        output = json.loads(result.stdout)
        self.assertIn('inputs', output)
        self.assertIn('results', output)
        self.assertGreater(output['results']['total_memory_gb'], 0)
    
    def test_bottleneck_detector_cli(self):
        """Test bottleneck detector CLI with chained outputs"""
        # First, generate timing analysis
        log_file = FIXTURES_DIR / 'sample_timing_log.txt'
        timing_result = self.run_script('timing_analyzer.py', [
            '--log', str(log_file),
            '--json'
        ])
        
        # Write timing results to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write(timing_result.stdout)
            timing_file = f.name
        
        try:
            # Run bottleneck detector
            result = self.run_script('bottleneck_detector.py', [
                '--timing', timing_file,
                '--json'
            ])
            
            self.assertEqual(result.returncode, 0)
            
            # Parse JSON output
            output = json.loads(result.stdout)
            self.assertIn('inputs', output)
            self.assertIn('results', output)
            self.assertIn('bottlenecks', output['results'])
            self.assertIn('recommendations', output['results'])
            # Regression guard (finding performance-profiling-F1/F4): the
            # detector must actually consume the analyzer's `results.phases`
            # schema and flag the solver-dominated fixture. A weak
            # len(recommendations) > 0 check passed even when the detector
            # silently found nothing, because of the "No significant
            # bottlenecks detected" placeholder. Assert real detection.
            bottlenecks = output['results']['bottlenecks']
            self.assertGreaterEqual(
                len(bottlenecks), 1,
                "detector found no bottleneck on a solver-dominated log "
                "(schema mismatch regression)",
            )
            phases = {b.get('phase') for b in bottlenecks}
            self.assertIn('Linear Solver', phases)
            categories = {
                (r.get('category') if isinstance(r, dict) else None)
                for r in output['results']['recommendations']
            }
            self.assertIn('solver', categories)
        finally:
            os.unlink(timing_file)
    
    def test_error_handling_missing_file(self):
        """Test error handling for missing input file"""
        result = self.run_script('timing_analyzer.py', [
            '--log', 'nonexistent_file.log',
            '--json'
        ])
        
        self.assertNotEqual(result.returncode, 0)
        
        # Should output error in JSON format
        output = json.loads(result.stdout)
        self.assertIn('error', output)
    
    def test_cross_platform_paths(self):
        """Test that scripts handle cross-platform paths correctly"""
        log_file = FIXTURES_DIR / 'sample_timing_log.txt'
        
        # Test with forward slashes
        result = self.run_script('timing_analyzer.py', [
            '--log', str(log_file).replace('\\', '/'),
            '--json'
        ])
        self.assertEqual(result.returncode, 0)
        
        # Test with backslashes (Windows)
        if sys.platform == 'win32':
            result = self.run_script('timing_analyzer.py', [
                '--log', str(log_file).replace('/', '\\'),
                '--json'
            ])
            self.assertEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
