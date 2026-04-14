from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Optional

import click

from .core.state import SessionState
from .utils.web_to_app_backend import WebToAppBackend


class CliContext:
    def __init__(self):
        self.json_output = False
        self.state = SessionState()
        self.source_root = Path(__file__).resolve().parents[3]
        self.backend = WebToAppBackend(self.source_root)


pass_context = click.make_pass_decorator(CliContext, ensure=True)


def emit(ctx: CliContext, payload):
    if ctx.json_output:
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        if isinstance(payload, (dict, list)):
            click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            click.echo(str(payload))


def run_repl(ctx: CliContext):
    click.echo("cli-anything-web-to-app REPL. Type 'help' or 'exit'.")
    while True:
        try:
            line = input("web-to-app> ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo()
            break
        if not line:
            continue
        if line in {"exit", "quit"}:
            break
        if line == "help":
            click.echo(
                "Examples: inspect summary | inspect feature-map | inspect variants | inspect android-summary | build dry-run"
            )
            continue
        args = shlex.split(line)
        try:
            cli.main(args=args, prog_name="cli-anything-web-to-app", standalone_mode=False, obj=ctx)
        except SystemExit:
            pass
        except Exception as exc:
            click.echo(f"error: {exc}")


@click.group(invoke_without_command=True)
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON")
@click.pass_context
def cli(click_ctx: click.Context, json_output: bool):
    """CLI-Anything harness for web-to-app."""
    ctx = click_ctx.ensure_object(CliContext)
    ctx.json_output = json_output
    if click_ctx.invoked_subcommand is None:
        run_repl(ctx)


@cli.group()
def inspect():
    """Inspect repository structure and Android metadata."""


@inspect.command("summary")
@pass_context
def inspect_summary(ctx: CliContext):
    emit(ctx, ctx.backend.summary())


@inspect.command("tree")
@click.option("--max-depth", default=2, type=int, show_default=True)
@pass_context
def inspect_tree(ctx: CliContext, max_depth: int):
    emit(ctx, ctx.backend.project_tree(max_depth=max_depth))


@inspect.command("modules")
@pass_context
def inspect_modules(ctx: CliContext):
    emit(ctx, ctx.backend.list_modules())


@inspect.command("packages")
@pass_context
def inspect_packages(ctx: CliContext):
    emit(ctx, ctx.backend.list_packages())


@inspect.command("manifest")
@pass_context
def inspect_manifest(ctx: CliContext):
    emit(ctx, ctx.backend.manifest_info())


@inspect.command("gradle")
@pass_context
def inspect_gradle(ctx: CliContext):
    emit(ctx, ctx.backend.gradle_info())


@inspect.command("samples")
@pass_context
def inspect_samples(ctx: CliContext):
    emit(ctx, {"samples": ctx.backend.list_samples()})


@inspect.command("extensions")
@pass_context
def inspect_extensions(ctx: CliContext):
    emit(ctx, {"extensions": ctx.backend.list_extensions()})


@inspect.command("feature-map")
@pass_context
def inspect_feature_map(ctx: CliContext):
    emit(ctx, ctx.backend.feature_module_map())


@inspect.command("variants")
@pass_context
def inspect_variants(ctx: CliContext):
    emit(ctx, ctx.backend.build_variants())


@inspect.command("android-summary")
@pass_context
def inspect_android_summary(ctx: CliContext):
    emit(ctx, ctx.backend.android_resources_summary())


@inspect.command("dependencies")
@pass_context
def inspect_dependencies(ctx: CliContext):
    emit(ctx, ctx.backend.dependency_summary())


@cli.group()
def state():
    """Manage in-session build profile state."""


@state.command("show")
@pass_context
def state_show(ctx: CliContext):
    emit(ctx, ctx.state.snapshot())


@state.command("set")
@click.argument("key", type=click.Choice(["app_name", "package_name", "url", "engine"]))
@click.argument("value")
@pass_context
def state_set(ctx: CliContext, key: str, value: str):
    emit(ctx, ctx.state.set_value(key, value))


@state.command("undo")
@pass_context
def state_undo(ctx: CliContext):
    emit(ctx, ctx.state.undo())


@state.command("redo")
@pass_context
def state_redo(ctx: CliContext):
    emit(ctx, ctx.state.redo())


@cli.group()
def build():
    """Build planning and safe wrappers."""


@build.command("plan")
@pass_context
def build_plan(ctx: CliContext):
    emit(ctx, ctx.backend.build_plan(ctx.state.snapshot()))


@build.command("check")
@pass_context
def build_check(ctx: CliContext):
    emit(ctx, ctx.backend.build_check())


@build.command("readiness")
@pass_context
def build_readiness(ctx: CliContext):
    emit(ctx, ctx.backend.build_readiness())


@build.command("target")
@click.option("--variant", default=None, help="Variant name, e.g. DevDebug or Release")
@click.option("--flavor", default=None, help="Flavor name, e.g. dev")
@click.option("--build-type", default="debug", show_default=True, help="Build type, e.g. debug/release")
@pass_context
def build_target(ctx: CliContext, variant: Optional[str], flavor: Optional[str], build_type: str):
    emit(ctx, ctx.backend.resolve_variant_target(variant=variant, flavor=flavor, build_type=build_type))


@build.command("assemble-simulate")
@click.option("--variant", default=None, help="Variant name, e.g. DevDebug or Release")
@click.option("--flavor", default=None, help="Flavor name, e.g. dev")
@click.option("--build-type", default="debug", show_default=True, help="Build type, e.g. debug/release")
@pass_context
def build_assemble_simulate(ctx: CliContext, variant: Optional[str], flavor: Optional[str], build_type: str):
    emit(ctx, ctx.backend.assemble_simulation(variant=variant, flavor=flavor, build_type=build_type))


@build.command("signing-inspect")
@pass_context
def build_signing_inspect(ctx: CliContext):
    emit(ctx, ctx.backend.signing_config_inspect())


@build.command("dry-run")
@click.option("--task", default="assembleDebug", show_default=True)
@pass_context
def build_dry_run(ctx: CliContext, task: str):
    emit(ctx, ctx.backend.build_dry_run(task=task))


@cli.group("extension")
def extension_group():
    """Extension lifecycle tooling (safe by default)."""


@extension_group.command("discover")
@pass_context
def extension_discover(ctx: CliContext):
    emit(ctx, ctx.backend.discover_installed_extensions())


@extension_group.command("show")
@click.argument("extension_id")
@pass_context
def extension_show(ctx: CliContext, extension_id: str):
    emit(ctx, ctx.backend.extension_metadata(extension_id))


@extension_group.command("validate")
@pass_context
def extension_validate(ctx: CliContext):
    emit(ctx, ctx.backend.validate_extension_compatibility())


@extension_group.command("stub")
@click.argument("extension_id")
@click.option("--manifest-version", default=3, type=click.Choice(["2", "3"]), show_default=True)
@click.option("--write", is_flag=True, help="Write generated stub files to assets/extensions/<id>")
@click.option("--force", is_flag=True, help="Overwrite existing files when used with --write")
@pass_context
def extension_stub(ctx: CliContext, extension_id: str, manifest_version: str, write: bool, force: bool):
    emit(
        ctx,
        ctx.backend.generate_extension_stub(
            extension_id=extension_id,
            manifest_version=int(manifest_version),
            write=write,
            force=force,
        ),
    )


@extension_group.command("plan")
@click.option("--action", type=click.Choice(["install", "remove"]), required=True)
@click.option("--extension-id", required=True)
@click.option("--source", default=None, help="Path/URL for install source")
@click.option("--mutate", is_flag=True, help="Explicitly request mutating mode (still simulated)")
@click.option("--execute", is_flag=True, help="Explicitly request execution (blocked; simulation only)")
@pass_context
def extension_plan(ctx: CliContext, action: str, extension_id: str, source: str | None, mutate: bool, execute: bool):
    emit(
        ctx,
        ctx.backend.simulate_extension_plan(
            action=action,
            extension_id=extension_id,
            source=source,
            mutate=mutate,
            execute=execute,
        ),
    )
