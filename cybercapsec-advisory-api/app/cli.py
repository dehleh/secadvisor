"""Command-line interface for administrative tasks.

Usage:
    python -m app.cli seed         # populate frameworks, controls, mappings, knowledge
    python -m app.cli seed-info    # show what would be loaded without writing
    python -m app.cli sync-plans   # create Flutterwave plans from the catalog
"""
from __future__ import annotations

import argparse
import logging
import sys

from sqlalchemy.orm import Session

from app.database import SessionLocal


def cmd_seed(_: argparse.Namespace) -> int:
    """Run the full seed: frameworks, controls, mappings, knowledge."""
    from app.services.seed import seed_all

    db: Session = SessionLocal()
    try:
        report = seed_all(db)
        print(report.render())
        return 0
    except Exception as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


def cmd_seed_info(_: argparse.Namespace) -> int:
    """Show what would be seeded without writing to the DB."""
    from app.services.seed import (
        discover_framework_files,
        discover_knowledge_files,
        load_knowledge_snippets,
    )
    from app.services.seed.loader import MAPPINGS_FILE, _load_yaml
    from app.services.seed.schema import FrameworkSeed, MappingsFile

    fw_files = discover_framework_files()
    kb_files = discover_knowledge_files()

    print(f"Framework files ({len(fw_files)}):")
    total_controls = 0
    for path in fw_files:
        data = _load_yaml(path)
        seed = FrameworkSeed.model_validate(data)
        print(
            f"  {path.name}: {seed.code.value} v{seed.version} "
            f"- {len(seed.controls)} controls"
        )
        total_controls += len(seed.controls)
    print(f"  TOTAL: {total_controls} controls")

    if MAPPINGS_FILE.exists():
        data = _load_yaml(MAPPINGS_FILE)
        mappings = MappingsFile.model_validate(data)
        print(f"\nMappings ({len(mappings.mappings)}):")
        by_source: dict[str, int] = {}
        for mapping in mappings.mappings:
            by_source[mapping.source_framework.value] = (
                by_source.get(mapping.source_framework.value, 0) + 1
            )
        for fw_code, count in sorted(by_source.items()):
            print(f"  {fw_code}: {count} outgoing mappings")
    else:
        print("\nNo mappings file at " + str(MAPPINGS_FILE))

    print(f"\nKnowledge files ({len(kb_files)}):")
    snippets = load_knowledge_snippets()
    print(f"  TOTAL: {len(snippets)} snippets across {len(kb_files)} files")
    return 0


def cmd_sync_plans(args: argparse.Namespace) -> int:
    """Create Flutterwave plans from the catalog and print env-var setup lines."""
    from app.config import get_settings
    from app.services.billing import CATALOG, get_flutterwave_client
    from app.services.billing.service import _env_var_for_plan

    settings = get_settings()
    use_mock = args.dry_run or settings.USE_MOCK_PAYMENTS

    try:
        client = get_flutterwave_client(
            use_mock=use_mock,
            secret_key=settings.FLUTTERWAVE_SECRET_KEY or None,
        )
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        print(
            "Hint: set FLUTTERWAVE_SECRET_KEY or pass --dry-run to test against the mock.",
            file=sys.stderr,
        )
        return 1

    print(
        f"# Syncing {len(CATALOG)} plans to Flutterwave "
        f"({'mock / dry-run' if use_mock else 'live'})\n"
    )

    env_lines: list[str] = []
    for plan in CATALOG:
        try:
            provider_plan = client.upsert_plan(
                name=plan.provider_name,
                amount_minor=plan.amount_minor,
                currency=plan.currency.value,
                interval=plan.interval.value,
                description=plan.description,
            )
        except Exception as exc:
            print(f"# FAILED {plan.lookup_key}: {exc}", file=sys.stderr)
            continue
        env_var = _env_var_for_plan(plan)
        env_lines.append(f"{env_var}={provider_plan.plan_code}")
        print(
            f"# {plan.lookup_key:30s} {plan.amount_major:>12,.2f} "
            f"{plan.currency.value} -> {provider_plan.plan_code}",
            file=sys.stderr,
        )

    print("\n# Add these to your environment:")
    for line in env_lines:
        print(line)
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    seed_parser = sub.add_parser("seed", help="Run the data seeder")
    seed_parser.set_defaults(func=cmd_seed)

    info_parser = sub.add_parser(
        "seed-info", help="Show what would be loaded without writing"
    )
    info_parser.set_defaults(func=cmd_seed_info)

    sync_parser = sub.add_parser(
        "sync-plans", help="Create Flutterwave plans from the catalog"
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use the mock Flutterwave client; produce fake plan IDs",
    )
    sync_parser.set_defaults(func=cmd_sync_plans)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
