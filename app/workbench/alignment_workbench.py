#!/usr/bin/env python3
"""
Interactive Alignment Workbench for TCGPlayer Price Data

Provides interactive CLI commands for guided filter discovery, coverage analysis,
and configuration management to transform the trial-and-error alignment workflow
into an efficient, insight-driven process.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.coverage_analyzer import CoverageAnalyzer, CoverageResult, RecommendationResult
from common.logger import AppLogger


def create_parser():
    """One-liner main argument parser creation with subcommands"""
    parser = argparse.ArgumentParser(description='Interactive Alignment Workbench for TCGPlayer Price Data',
                                   formatter_class=argparse.RawDescriptionHelpFormatter,
                                   epilog="""Commands: discover, analyze, save, list, run
Examples:
  python workbench/alignment_workbench.py discover --min-coverage 0.9
  python workbench/alignment_workbench.py analyze --sets "SV*" --types "Card"
  python workbench/alignment_workbench.py save --name "sv_cards" --sets "SV*" --types "Card"
  python workbench/alignment_workbench.py list --detailed
  python workbench/alignment_workbench.py run sv_cards --output-name "current_analysis"
        """)

    # One-liner common arguments and subparsers setup
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Discover command
    parser_discover = subparsers.add_parser('discover', help='Discover viable filter combinations')
    parser_discover.add_argument('input_csv', nargs='?', default='data/output.csv',
                               help='Input CSV file (default: data/output.csv)')
    parser_discover.add_argument('--format', choices=['summary', 'detailed'], default='summary',
                               help='Output format: summary shows top 3, detailed shows all viable options')
    parser_discover.add_argument('--min-coverage', type=float, default=0.9, metavar='PERCENT',
                               help='Minimum coverage threshold (0.0-1.0, default: 0.9)')
    parser_discover.add_argument('--max-results', type=int, default=10,
                               help='Maximum number of recommendations (default: 10)')

    # Analyze command
    parser_analyze = subparsers.add_parser('analyze', help='Analyze specific filter combinations')
    parser_analyze.add_argument('input_csv', nargs='?', default='data/output.csv',
                              help='Input CSV file (default: data/output.csv)')
    parser_analyze.add_argument('--sets', required=True,
                              help='Sets filter pattern (e.g., "SV*", "SV01,SV02")')
    parser_analyze.add_argument('--types', required=True,
                              help='Types filter pattern (e.g., "*Box", "Card")')
    parser_analyze.add_argument('--period', default='3M',
                              help='Period filter (default: 3M)')
    parser_analyze.add_argument('--suggest-alternatives', action='store_true',
                              help='Show alternative filter suggestions when alignment fails')
    parser_analyze.add_argument('--allow-fallback', action='store_true',
                              help='Enable fallback mode for <100% coverage scenarios')

    return parser


def handle_discover_command(args) -> None:
    """Handle the discover command"""
    logger = AppLogger.get_logger(__name__)
    logger.info("Starting filter discovery process")

    try:
        analyzer = CoverageAnalyzer(Path(args.input_csv))

        # Get dataset summary for context
        summary = analyzer.get_dataset_summary()

        print("🔍 Analyzing dataset...")
        print(f"📊 Dataset: {summary['total_records']} records, {summary['unique_signatures']} signatures")
        print(f"📅 Date range: {summary['date_range'][0]} to {summary['date_range'][1]}")
        print()

        # Discover configurations
        recommendations = analyzer.discover_viable_configurations(
            min_coverage=args.min_coverage,
            max_recommendations=args.max_results,
            include_fallback_options=True
        )

        if not recommendations:
            print(f"❌ No configurations found with coverage ≥ {args.min_coverage:.0%}")
            print("💡 Try lowering --min-coverage threshold (e.g., 0.8 or 0.7)")
            return

        # Display results
        if args.format == 'summary':
            print(f"📊 Top Recommendations (Coverage ≥ {args.min_coverage:.0%}):\n")
            for rec in recommendations[:3]:
                print(f"{rec.rank}. {rec.description}")
                print(f"   Command: {rec.command_string}")
                print(f"   Coverage: {rec.coverage_result.coverage_percentage:.1%} ({rec.coverage_result.signatures_found}/{rec.coverage_result.signatures_total} signatures)")
                print(f"   Records: {rec.estimated_records} aligned, {rec.coverage_result.time_series_points} time series points")
                if rec.coverage_result.fallback_required:
                    print("   ⚠️  Requires fallback mode")
                print()

            if len(recommendations) > 3:
                print(f"💡 Use --format detailed to see all {len(recommendations)} viable combinations")
        else:
            print(f"📈 All Viable Configurations (Coverage ≥ {args.min_coverage:.0%}):\n")
            for rec in recommendations:
                print(f"[{rec.rank}] {rec.description} - {rec.coverage_result.coverage_percentage:.1%} Coverage")
                print(f"├─ Command: {rec.command_string}")
                print(f"├─ Signatures: {rec.coverage_result.signatures_found}/{rec.coverage_result.signatures_total} from {rec.coverage_result.optimal_start_date}")
                print(f"├─ Timeline: {rec.coverage_result.time_series_points} dates")
                print(f"├─ Records: {rec.estimated_records} aligned")
                if rec.coverage_result.gap_fills_required > 0:
                    print(f"├─ Gap fills: {rec.coverage_result.gap_fills_required} required")
                if rec.coverage_result.fallback_required:
                    print("├─ Quality: Requires fallback mode")
                else:
                    print("└─ Quality: Perfect alignment")
                print()

        print("💡 Use 'analyze' command to get detailed insights for specific filters")
        print("💡 Use 'save' command to store successful configurations for reuse")

    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        print(f"❌ Discovery failed: {e}")
        sys.exit(1)


def handle_analyze_command(args) -> None:
    """Handle the analyze command"""
    logger = AppLogger.get_logger(__name__)
    logger.info(f"Analyzing filter combination: {args.sets}, {args.types}, {args.period}")

    try:
        analyzer = CoverageAnalyzer(Path(args.input_csv))

        print("📈 Coverage Analysis Results:\n")

        # Perform analysis
        result = analyzer.analyze_filter_combination(
            args.sets, args.types, args.period, args.allow_fallback
        )

        if result.coverage_percentage > 0:
            # Success case
            print("✅ Filter Configuration:")
            print(f"   Sets: {args.sets}")
            print(f"   Types: {args.types}")
            print(f"   Period: {args.period}")
            print()

            print("📊 Alignment Quality:")
            print(f"   ✅ Coverage: {result.coverage_percentage:.1%} ({result.signatures_found}/{result.signatures_total} signatures)")
            if result.optimal_start_date:
                print(f"   ✅ Optimal start date: {result.optimal_start_date}")
            if result.fallback_required:
                print("   ⚠️  Fallback mode enabled")
            else:
                print("   ✅ Complete temporal alignment achieved")
            print()

            print("📋 Record Summary:")
            print(f"   • Total signatures: {result.signatures_total}")
            print(f"   • Records aligned: {result.records_aligned}")
            print(f"   • Time series points: {result.time_series_points}")
            if result.records_before_start > 0:
                print(f"   • Records excluded (pre-start): {result.records_before_start}")
            if result.gap_fills_required > 0:
                print(f"   • Gap fills required: {result.gap_fills_required}")
            print()

            print("💡 Optimization Notes:")
            if result.coverage_percentage == 1.0 and not result.fallback_required:
                print("   • Perfect alignment achieved - no optimizations needed")
            elif result.fallback_required:
                print("   • Using fallback mode for partial coverage")
            if result.records_before_start > 0:
                print(f"   • {result.records_before_start} early records excluded for alignment quality")

            if result.missing_signatures:
                print(f"   • Missing signatures: {len(result.missing_signatures)} (impacts coverage)")

        else:
            # Failure case
            print("❌ Filter Configuration:")
            print(f"   Sets: {args.sets}")
            print(f"   Types: {args.types}")
            print(f"   Period: {args.period}")
            print()

            print("⚠️  Alignment Issues:")
            print("   ❌ No viable alignment found")
            print("   ❌ Coverage: 0% (no matching data or incompatible signatures)")
            print()

            if args.suggest_alternatives:
                print("🔧 Suggested Solutions:\n")
                alternatives = analyzer.suggest_alternatives(result.filter_config, max_alternatives=3)

                if alternatives:
                    for i, alt in enumerate(alternatives, 1):
                        print(f"Option {i}: {alt.description}")
                        print(f"   Command: {alt.command_string}")
                        print(f"   Result: {alt.coverage_result.coverage_percentage:.1%} coverage, {alt.estimated_records} records")
                        if alt.coverage_result.fallback_required:
                            print("   Trade-off: Requires fallback mode")
                        print()
                else:
                    print("No viable alternatives found with current dataset.")
                    print("💡 Try broader patterns like --sets '*' or --types '*'")
            else:
                print("💡 Use --suggest-alternatives to see improvement options")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if args.verbose:
        # Initialize verbose logging
        logger = AppLogger.get_logger(__name__)
        logger.info("Starting Interactive Alignment Workbench")

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # One-liner command dispatch using dictionary mapping
    command_handlers = {'discover': handle_discover_command, 'analyze': handle_analyze_command}
    unimplemented = {'save', 'list', 'run'}

    if args.command in command_handlers:
        command_handlers[args.command](args)
    elif args.command in unimplemented:
        print(f"❌ {args.command.title()} command not yet implemented\n💡 Coming in next building phase")
        sys.exit(1)
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()