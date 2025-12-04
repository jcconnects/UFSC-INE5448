#!/usr/bin/env python3
"""
n8n Workflow Security Analyzer

This script implements a hybrid security analysis system for n8n workflows,
combining two analysis engines:
- Agentic Radar: Focuses on AI-specific vulnerabilities (prompt injection, PII leakage)
- Semgrep: Custom rules for traditional security issues (SQLi, CMDi, SSRF, secrets)

Components:
A. Input and Validation Module - JSON parsing, structure validation, metadata extraction
B. Hybrid Analysis Engine - Sequential execution of both analysis tools
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import os


@dataclass
class WorkflowMetadata:
    """Metadata extracted from n8n workflow"""
    filepath: str
    workflow_id: str
    workflow_name: str
    node_count: int
    node_types: Dict[str, int]
    has_connections: bool
    connections_count: int


@dataclass
class ValidationResult:
    """Result of workflow validation"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Combined analysis results from both tools"""
    workflow_path: str
    metadata: WorkflowMetadata
    agentic_radar_findings: List[Dict[str, Any]]
    semgrep_findings: List[Dict[str, Any]]
    total_findings: int
    execution_time: float
    timestamp: str


# ============================================================================
# Component A: Input and Validation Module
# ============================================================================

class WorkflowValidator:
    """Validates n8n workflow JSON files and extracts metadata"""

    def __init__(self):
        self.required_fields = ['nodes']

    def load_workflow(self, filepath: str) -> Tuple[Optional[Dict], ValidationResult]:
        """
        Load and parse a workflow JSON file with error handling.

        Args:
            filepath: Path to the workflow JSON file

        Returns:
            Tuple of (workflow_data, validation_result)
        """
        result = ValidationResult(valid=False)

        # Check file exists
        if not os.path.exists(filepath):
            result.errors.append(f"File not found: {filepath}")
            return None, result

        if not os.path.isfile(filepath):
            result.errors.append(f"Path is not a file: {filepath}")
            return None, result

        # Try to read and parse JSON
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
        except json.JSONDecodeError as e:
            result.errors.append(f"Invalid JSON syntax: {e}")
            return None, result
        except IOError as e:
            result.errors.append(f"Cannot read file: {e}")
            return None, result

        # Validate structure
        validation = self.validate_structure(workflow)
        if not validation.valid:
            return workflow, validation

        result.valid = True
        return workflow, result

    def validate_structure(self, workflow: Dict) -> ValidationResult:
        """
        Validate that workflow has required structure.

        Args:
            workflow: Parsed workflow dictionary

        Returns:
            ValidationResult with validation status and messages
        """
        result = ValidationResult(valid=True)

        # Check for nodes array
        if 'nodes' not in workflow:
            result.errors.append("Missing required field: 'nodes'")
            result.valid = False
        elif not isinstance(workflow['nodes'], list):
            result.errors.append("Field 'nodes' must be an array")
            result.valid = False
        else:
            # Validate node structure
            for idx, node in enumerate(workflow['nodes']):
                if not isinstance(node, dict):
                    result.warnings.append(f"Node at index {idx} is not an object")
                    continue

                # Check for required node fields
                required_node_fields = ['id', 'name', 'type']
                for field in required_node_fields:
                    if field not in node:
                        result.warnings.append(
                            f"Node at index {idx} missing field '{field}'"
                        )

        # Check for connections (not required, but note if missing)
        if 'connections' not in workflow:
            result.warnings.append("Workflow has no 'connections' field")
        elif not isinstance(workflow['connections'], dict):
            result.warnings.append("Field 'connections' should be an object")

        return result

    def extract_metadata(self, workflow: Dict, filepath: str) -> WorkflowMetadata:
        """
        Extract metadata from workflow.

        Args:
            workflow: Parsed workflow dictionary
            filepath: Path to workflow file

        Returns:
            WorkflowMetadata object
        """
        # Count node types
        node_types = {}
        for node in workflow.get('nodes', []):
            node_type = node.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1

        # Count connections
        connections = workflow.get('connections', {})
        connections_count = sum(
            len(conns) for conns in connections.values() if isinstance(conns, dict)
        )

        return WorkflowMetadata(
            filepath=filepath,
            workflow_id=workflow.get('id', 'unknown'),
            workflow_name=workflow.get('name', 'unnamed'),
            node_count=len(workflow.get('nodes', [])),
            node_types=node_types,
            has_connections='connections' in workflow,
            connections_count=connections_count
        )

    def scan_directory(self, directory: str, pattern: str = "*.json") -> List[str]:
        """
        Scan directory for workflow files.

        Args:
            directory: Directory path to scan
            pattern: Glob pattern for file matching (default: *.json)

        Returns:
            List of file paths
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []

        if not dir_path.is_dir():
            return []

        return [str(f) for f in dir_path.glob(pattern)]


# ============================================================================
# Component B: Hybrid Analysis Engine
# ============================================================================

class AgenticRadarExecutor:
    """Executes Agentic Radar security analysis"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or "analysis_output"
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def run(self, workflow_path: str) -> Tuple[List[Dict], bool, str]:
        """
        Execute Agentic Radar scan on workflow.

        Args:
            workflow_path: Path to workflow JSON file

        Returns:
            Tuple of (findings_list, success, error_message)
        """
        workflow_name = Path(workflow_path).stem
        output_path = Path(self.output_dir) / f"{workflow_name}_radar"

        # Construct command
        cmd = [
            "agentic-radar",
            "scan",
            workflow_path,
            "--output",
            str(output_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )

            if result.returncode != 0:
                return [], False, f"Agentic Radar failed: {result.stderr}"

            # Parse output - Agentic Radar may produce HTML or JSON
            findings = self._parse_output(output_path, workflow_name)
            return findings, True, ""

        except subprocess.TimeoutExpired:
            return [], False, "Agentic Radar execution timed out"
        except FileNotFoundError:
            return [], False, "Agentic Radar not found. Is it installed?"
        except Exception as e:
            return [], False, f"Agentic Radar execution error: {e}"

    def _parse_output(self, output_path: Path, workflow_name: str) -> List[Dict]:
        """
        Parse Agentic Radar output files.

        Args:
            output_path: Directory containing output files
            workflow_name: Name of the workflow

        Returns:
            List of finding dictionaries
        """
        findings = []

        # Look for JSON output first
        json_file = output_path / f"{workflow_name}.json"
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    # Extract findings from JSON structure
                    if isinstance(data, dict) and 'findings' in data:
                        findings = data['findings']
                    elif isinstance(data, list):
                        findings = data
            except Exception as e:
                print(f"Warning: Could not parse Agentic Radar JSON: {e}", file=sys.stderr)

        # If no JSON, look for HTML and note its presence
        html_file = output_path / f"{workflow_name}.html"
        if html_file.exists() and not findings:
            findings.append({
                'tool': 'agentic-radar',
                'type': 'report_generated',
                'message': f'HTML report generated at {html_file}',
                'severity': 'info'
            })

        return findings


class SemgrepExecutor:
    """Executes Semgrep security analysis with custom n8n rules"""

    def __init__(self, rules_path: Optional[str] = None):
        self.rules_path = rules_path or "rules/n8n-generic-patterns.yaml"

    def run(self, workflow_path: str) -> Tuple[List[Dict], bool, str]:
        """
        Execute Semgrep scan on workflow.

        Args:
            workflow_path: Path to workflow JSON file

        Returns:
            Tuple of (findings_list, success, error_message)
        """
        # Check if rules file exists
        if not os.path.exists(self.rules_path):
            return [], False, f"Semgrep rules not found: {self.rules_path}"

        # Construct command
        cmd = [
            "semgrep",
            "--config", self.rules_path,
            "--json",
            workflow_path
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )

            # Semgrep returns 0 or 1 (1 when findings exist), both are success
            if result.returncode not in [0, 1]:
                return [], False, f"Semgrep failed: {result.stderr}"

            # Parse JSON output
            findings = self._parse_output(result.stdout)
            return findings, True, ""

        except subprocess.TimeoutExpired:
            return [], False, "Semgrep execution timed out"
        except FileNotFoundError:
            return [], False, "Semgrep not found. Is it installed?"
        except Exception as e:
            return [], False, f"Semgrep execution error: {e}"

    def _parse_output(self, stdout: str) -> List[Dict]:
        """
        Parse Semgrep JSON output.

        Args:
            stdout: Semgrep stdout containing JSON

        Returns:
            List of finding dictionaries
        """
        try:
            data = json.loads(stdout)
            findings = []

            # Semgrep native JSON format
            if 'results' in data:
                for result in data['results']:
                    findings.append({
                        'tool': 'semgrep',
                        'rule_id': result.get('check_id', 'unknown'),
                        'message': result.get('extra', {}).get('message', result.get('message', '')),
                        'severity': result.get('extra', {}).get('severity', 'WARNING'),
                        'path': result.get('path', ''),
                        'line': result.get('start', {}).get('line', 0),
                        'code': result.get('extra', {}).get('lines', ''),
                        'metadata': result.get('extra', {}).get('metadata', {})
                    })

            return findings

        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse Semgrep JSON: {e}", file=sys.stderr)
            return []


class HybridAnalyzer:
    """Orchestrates hybrid analysis using both Agentic Radar and Semgrep"""

    def __init__(self, agentic_output_dir: Optional[str] = None,
                 semgrep_rules: Optional[str] = None):
        self.validator = WorkflowValidator()
        self.agentic_executor = AgenticRadarExecutor(agentic_output_dir)
        self.semgrep_executor = SemgrepExecutor(semgrep_rules)

    def analyze(self, workflow_path: str) -> Optional[AnalysisResult]:
        """
        Perform hybrid analysis on a workflow.

        Args:
            workflow_path: Path to workflow JSON file

        Returns:
            AnalysisResult or None if validation fails
        """
        start_time = datetime.now()

        # Load and validate workflow
        print(f"\n[*] Loading workflow: {workflow_path}")
        workflow, validation = self.validator.load_workflow(workflow_path)

        if not validation.valid:
            print(f"[!] Validation failed for {workflow_path}:")
            for error in validation.errors:
                print(f"    ERROR: {error}")
            return None

        if validation.warnings:
            print(f"[!] Validation warnings:")
            for warning in validation.warnings:
                print(f"    WARNING: {warning}")

        # Extract metadata
        metadata = self.validator.extract_metadata(workflow, workflow_path)
        print(f"[*] Workflow metadata:")
        print(f"    Name: {metadata.workflow_name}")
        print(f"    ID: {metadata.workflow_id}")
        print(f"    Nodes: {metadata.node_count}")
        print(f"    Node types: {len(metadata.node_types)}")

        # Execute Agentic Radar (sequential execution)
        print(f"\n[*] Running Agentic Radar analysis...")
        radar_findings, radar_success, radar_error = self.agentic_executor.run(workflow_path)

        if not radar_success:
            print(f"[!] Agentic Radar error: {radar_error}")
            radar_findings = []
        else:
            print(f"[+] Agentic Radar completed: {len(radar_findings)} findings")

        # Execute Semgrep (sequential execution)
        print(f"\n[*] Running Semgrep analysis...")
        semgrep_findings, semgrep_success, semgrep_error = self.semgrep_executor.run(workflow_path)

        if not semgrep_success:
            print(f"[!] Semgrep error: {semgrep_error}")
            semgrep_findings = []
        else:
            print(f"[+] Semgrep completed: {len(semgrep_findings)} findings")

        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # Create analysis result
        result = AnalysisResult(
            workflow_path=workflow_path,
            metadata=metadata,
            agentic_radar_findings=radar_findings,
            semgrep_findings=semgrep_findings,
            total_findings=len(radar_findings) + len(semgrep_findings),
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )

        return result

    def analyze_batch(self, directory: str) -> List[AnalysisResult]:
        """
        Analyze all workflows in a directory.

        Args:
            directory: Directory containing workflow JSON files

        Returns:
            List of AnalysisResult objects
        """
        workflow_files = self.validator.scan_directory(directory)
        print(f"[*] Found {len(workflow_files)} workflow files in {directory}")

        results = []
        for workflow_file in workflow_files:
            result = self.analyze(workflow_file)
            if result:
                results.append(result)

        return results


# ============================================================================
# Report Generation
# ============================================================================

def generate_json_report(results: List[AnalysisResult], output_path: str):
    """Generate JSON report from analysis results"""
    report_data = []

    for result in results:
        report_data.append({
            'workflow_path': result.workflow_path,
            'workflow_name': result.metadata.workflow_name,
            'workflow_id': result.metadata.workflow_id,
            'node_count': result.metadata.node_count,
            'node_types': result.metadata.node_types,
            'analysis': {
                'agentic_radar_findings': result.agentic_radar_findings,
                'semgrep_findings': result.semgrep_findings,
                'total_findings': result.total_findings,
                'execution_time': result.execution_time,
                'timestamp': result.timestamp
            }
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)

    print(f"\n[+] JSON report saved to: {output_path}")


def generate_markdown_report(results: List[AnalysisResult], output_path: str):
    """Generate Markdown report from analysis results"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# n8n Workflow Security Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total workflows analyzed:** {len(results)}\n\n")

        # Summary statistics
        total_findings = sum(r.total_findings for r in results)
        total_radar = sum(len(r.agentic_radar_findings) for r in results)
        total_semgrep = sum(len(r.semgrep_findings) for r in results)

        f.write("## Summary\n\n")
        f.write(f"- Total findings: {total_findings}\n")
        f.write(f"- Agentic Radar findings: {total_radar}\n")
        f.write(f"- Semgrep findings: {total_semgrep}\n\n")

        # Per-workflow results
        for idx, result in enumerate(results, 1):
            f.write(f"## Workflow {idx}: {result.metadata.workflow_name}\n\n")
            f.write(f"**Path:** `{result.workflow_path}`\n\n")
            f.write(f"**Metadata:**\n")
            f.write(f"- Workflow ID: {result.metadata.workflow_id}\n")
            f.write(f"- Node count: {result.metadata.node_count}\n")
            f.write(f"- Execution time: {result.execution_time:.2f}s\n\n")

            # Agentic Radar findings
            f.write(f"### Agentic Radar Findings ({len(result.agentic_radar_findings)})\n\n")
            if result.agentic_radar_findings:
                for finding in result.agentic_radar_findings:
                    f.write(f"- **{finding.get('type', 'Unknown')}**: {finding.get('message', '')}\n")
            else:
                f.write("No findings.\n")
            f.write("\n")

            # Semgrep findings
            f.write(f"### Semgrep Findings ({len(result.semgrep_findings)})\n\n")
            if result.semgrep_findings:
                for finding in result.semgrep_findings:
                    severity = finding.get('severity', 'UNKNOWN')
                    rule = finding.get('rule_id', 'unknown')
                    message = finding.get('message', '')
                    line = finding.get('line', 0)
                    f.write(f"- **[{severity}]** {rule} (line {line}): {message}\n")
            else:
                f.write("No findings.\n")
            f.write("\n")
            f.write("---\n\n")

    print(f"[+] Markdown report saved to: {output_path}")


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Main entry point for the workflow analyzer"""
    parser = argparse.ArgumentParser(
        description="n8n Workflow Security Analyzer - Hybrid analysis using Agentic Radar and Semgrep",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single workflow
  %(prog)s workflow_1.json

  # Analyze with custom output directory
  %(prog)s workflow_1.json --output results/

  # Batch analysis
  %(prog)s --batch ./workflows/

  # Generate JSON report
  %(prog)s workflow_1.json --format json --report output.json
        """
    )

    # Input arguments
    parser.add_argument(
        'workflow',
        nargs='?',
        help='Path to workflow JSON file'
    )
    parser.add_argument(
        '--batch',
        metavar='DIR',
        help='Analyze all workflows in directory'
    )

    # Output arguments
    parser.add_argument(
        '--output',
        metavar='DIR',
        default='analysis_output',
        help='Output directory for analysis results (default: analysis_output)'
    )
    parser.add_argument(
        '--rules',
        metavar='PATH',
        default='rules/n8n-generic-patterns.yaml',
        help='Path to Semgrep rules file (default: rules/n8n-generic-patterns.yaml)'
    )

    # Report arguments
    parser.add_argument(
        '--format',
        choices=['json', 'markdown', 'both'],
        default='markdown',
        help='Report format (default: markdown)'
    )
    parser.add_argument(
        '--report',
        metavar='PATH',
        help='Path for generated report (default: auto-generated in output dir)'
    )

    args = parser.parse_args()

    # Validate input
    if not args.workflow and not args.batch:
        parser.error("Either workflow file or --batch directory must be specified")

    if args.workflow and args.batch:
        parser.error("Cannot specify both workflow file and --batch directory")

    # Initialize analyzer
    analyzer = HybridAnalyzer(
        agentic_output_dir=args.output,
        semgrep_rules=args.rules
    )

    # Perform analysis
    results = []
    if args.batch:
        results = analyzer.analyze_batch(args.batch)
    else:
        result = analyzer.analyze(args.workflow)
        if result:
            results = [result]

    if not results:
        print("\n[!] No successful analyses to report")
        return 1

    # Generate reports
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if args.format in ['json', 'both']:
        json_path = args.report if args.report and args.format == 'json' else \
                    f"{args.output}/report_{timestamp}.json"
        generate_json_report(results, json_path)

    if args.format in ['markdown', 'both']:
        md_path = args.report if args.report and args.format == 'markdown' else \
                  f"{args.output}/report_{timestamp}.md"
        generate_markdown_report(results, md_path)

    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print("="*70)
    print(f"Workflows analyzed: {len(results)}")
    print(f"Total findings: {sum(r.total_findings for r in results)}")
    print(f"Average execution time: {sum(r.execution_time for r in results) / len(results):.2f}s")

    return 0


if __name__ == '__main__':
    sys.exit(main())
