from __future__ import annotations

import json
import shlex
from pathlib import Path

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
            click.echo("Examples: inspect summary | inspect modules | inspect manifest | build dry-run")
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


@build.command("dry-run")
@click.option("--task", default="assembleDebug", show_default=True)
@pass_context
def build_dry_run(ctx: CliContext, task: str):
    emit(ctx, ctx.backend.build_dry_run(task=task))
