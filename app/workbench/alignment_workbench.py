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

    # Save command
    parser_save = subparsers.add_parser('save', help='Save filter configuration for reuse')
    parser_save.add_argument('input_csv', nargs='?', default='data/output.csv',
                           help='Input CSV file for validation (default: data/output.csv)')
    parser_save.add_argument('--name', required=True,
                           help='Configuration name (alphanumeric, underscores, hyphens)')
    parser_save.add_argument('--sets', required=True,
                           help='Sets filter pattern to save')
    parser_save.add_argument('--types', required=True,
                           help='Types filter pattern to save')
    parser_save.add_argument('--period', default='3M',
                           help='Period filter to save (default: 3M)')
    parser_save.add_argument('--description',
                           help='Optional description for this configuration')

    # List command
    parser_list = subparsers.add_parser('list', help='List saved configurations')
    parser_list.add_argument('--detailed', action='store_true',
                           help='Show detailed information including coverage stats')

    # Run command
    parser_run = subparsers.add_parser('run', help='Execute saved configuration')
    parser_run.add_argument('config_name',
                          help='Name of saved configuration to execute')
    parser_run.add_argument('--input-csv', default='data/output.csv',
                          help='Input CSV file (default: data/output.csv)')
    parser_run.add_argument('--output-name',
                          help='Override output name (default: use config name)')

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


def handle_save_command(args) -> None:
    """Handle the save command"""
    logger = AppLogger.get_logger(__name__)
    logger.info(f"Saving configuration: {args.name}")

    try:
        from common.configuration_manager import ConfigurationManager
        from common.coverage_analyzer import CoverageAnalyzer
        from dataclasses import asdict

        config_manager = ConfigurationManager()
        coverage_analyzer = CoverageAnalyzer(Path(args.input_csv))

        print("✅ Validating configuration...")

        # Validate configuration against dataset
        coverage_result = coverage_analyzer.analyze_filter_combination(
            args.sets, args.types, args.period
        )

        if coverage_result.coverage_percentage == 0:
            print("❌ Configuration validation failed - no alignment possible")
            print("💡 Use 'analyze' command to troubleshoot filter combination")
            return

        # Save configuration
        success = config_manager.save_configuration(
            name=args.name,
            display_name=args.name.replace('_', ' ').title(),
            filters={"sets": args.sets, "types": args.types, "period": args.period},
            validation_metadata=asdict(coverage_result),
            description=args.description
        )

        if success:
            print(f"💾 Saved configuration: {args.name}")
            print()
            print("Configuration Details:")
            print(f"├─ Sets: {args.sets}")
            print(f"├─ Types: {args.types}")
            print(f"├─ Period: {args.period}")
            print(f"├─ Coverage: {coverage_result.coverage_percentage:.1%} perfect alignment" if coverage_result.coverage_percentage == 1.0 else f"├─ Coverage: {coverage_result.coverage_percentage:.1%} ({coverage_result.signatures_found}/{coverage_result.signatures_total} signatures)")
            print(f"├─ Records: {coverage_result.records_aligned} aligned records expected")
            print(f"└─ Description: {args.description or '(none)'}")
            print()
            print(f"💡 Use 'python workbench/alignment_workbench.py run {args.name}' to execute")
        else:
            print("❌ Failed to save configuration")
            print("💡 Check configuration name format and try again")

    except Exception as e:
        logger.error(f"Save failed: {e}")
        print(f"❌ Save failed: {e}")
        sys.exit(1)


def handle_list_command(args) -> None:
    """Handle the list command"""
    logger = AppLogger.get_logger(__name__)
    logger.info("Listing saved configurations")

    try:
        from common.configuration_manager import ConfigurationManager

        config_manager = ConfigurationManager()
        configurations = config_manager.list_configurations(detailed=args.detailed)

        if not configurations:
            print("📋 No saved configurations found")
            print("💡 Use 'save' command to create your first configuration")
            return

        if args.detailed:
            print("📋 Saved Configurations (Detailed):\n")
            for i, config in enumerate(configurations, 1):
                print(f"[{i}] {config.name}")
                print(f"├─ Command: --sets \"{config.filters['sets']}\" --types \"{config.filters['types']}\" --period \"{config.filters['period']}\"")
                print(f"├─ Coverage: {config.validation_metadata['coverage_percentage']:.1%} ({config.validation_metadata['signatures_found']}/{config.validation_metadata['signatures_total']} signatures)")
                print(f"├─ Records: {config.validation_metadata['records_aligned']} aligned, {config.validation_metadata['time_series_points']} time series points")
                print(f"├─ Created: {config.usage_statistics['created_at']}")
                print(f"├─ Last used: {config.usage_statistics['last_used'] or 'Never'}")
                print(f"└─ Description: {config.description or '(none)'}")
                print()
        else:
            print("📋 Saved Configurations:\n")
            for i, config in enumerate(configurations, 1):
                coverage = config.validation_metadata['coverage_percentage']
                records = config.validation_metadata['records_aligned']
                print(f"{i}. {config.name}")
                print(f"   └─ {config.filters['sets']} {config.filters['types']}, {coverage:.0%} coverage, {records} records")
                print()

        print("💡 Use --detailed for coverage statistics and descriptions")
        print("💡 Use 'run CONFIG_NAME' to execute a saved configuration")

    except Exception as e:
        logger.error(f"List failed: {e}")
        print(f"❌ List failed: {e}")
        sys.exit(1)


def handle_run_command(args) -> None:
    """Handle the run command"""
    logger = AppLogger.get_logger(__name__)
    logger.info(f"Running configuration: {args.config_name}")

    try:
        from common.configuration_manager import ConfigurationManager
        from chart.index_aggregator import IndexAggregator
        from datetime import datetime, timezone

        config_manager = ConfigurationManager()
        config = config_manager.load_configuration(args.config_name)

        if not config:
            print(f"❌ Configuration '{args.config_name}' not found")
            print("💡 Use 'list' command to see available configurations")
            return

        print(f"🚀 Executing saved configuration: {args.config_name}")
        print()
        print("📋 Configuration:")
        print(f"   Sets: {config.filters['sets']}")
        print(f"   Types: {config.filters['types']}")
        print(f"   Period: {config.filters['period']}")
        print()

        # Execute using existing IndexAggregator
        aggregator = IndexAggregator()
        output_name = args.output_name or args.config_name

        # Run aggregation with saved filters
        subset_df = aggregator.create_subset(
            Path(args.input_csv),
            config.filters['sets'],
            config.filters['types'],
            config.filters['period']
        )

        if not subset_df.empty:
            # Generate time series
            ts_df = aggregator.aggregate_time_series(subset_df, output_name)

            # Save outputs
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            raw_output = data_dir / f"{output_name}_time_series_raw.csv"
            ts_output = data_dir / f"{output_name}_time_series.csv"

            aggregator.write_csv(subset_df.sort_values(['period_end_date', 'set']), raw_output)
            aggregator.write_csv(ts_df, ts_output)

            print("📊 Execution Results:")
            print(f"   ✅ Alignment successful: {len(subset_df)} records processed")
            print(f"   ✅ Time series generated: {len(ts_df)} data points")
            print(f"   ✅ Files created:")
            print(f"      • {raw_output} ({len(subset_df)} records)")
            print(f"      • {ts_output} ({len(ts_df)} aggregated points)")
            print()

            # Update usage statistics
            config_manager.update_usage_statistics(args.config_name)
            print(f"🕐 Last used updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("❌ Execution failed: No data matches the configuration filters")
            print("💡 The dataset may have changed since configuration was saved")
            print("💡 Use 'analyze' command to check current filter compatibility")

    except Exception as e:
        logger.error(f"Run failed: {e}")
        print(f"❌ Run failed: {e}")
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

    # Command dispatch using dictionary mapping
    command_handlers = {
        'discover': handle_discover_command, 
        'analyze': handle_analyze_command,
        'save': handle_save_command,
        'list': handle_list_command,
        'run': handle_run_command
    }

    if args.command in command_handlers:
        command_handlers[args.command](args)
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()