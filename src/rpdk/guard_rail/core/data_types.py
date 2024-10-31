"""Module that holds custom data types.

Provides custom data types:
- Stateful
- Stateless
- GuardRuleSet
- GuardRuleSetResult

Typical usage example:

    from guard_rail.core.data_types import GuardRuleResult, GuardRuleSetResult, Stateful, Stateless

    payload: Stateless = Stateless(schemas=list_of_schemas, rules=list_of_rules)
    # or
    payload: Stateful = Stateful(
            previous_schema=previous_schema,
            current_schema=current_schema,
            rules=list_of_rules,
        )
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table


@dataclass
class Stateless:
    """Implements Stateless type for stateless compliance assessment
    over specified list of schemas/rules

    Args:
        schemas (List[Dict[str, Any]]): Collection of Resource Provider Schemas
        rules (List[str]): Collection of Custom Compliance Rules
    """

    schemas: List[Dict[str, Any]]
    rules: List[str] = field(default_factory=list)


@dataclass
class Stateful:
    """Implements Stateful type for stateful compliance assessment
    over specified list of rules

    Args:
        current_schema (Dict[str, Any]): Current State of Resource Provider Schema
        previous_schema (Dict[str, Any]): Previous State of Resource Provider Schema
    """

    current_schema: Dict[str, Any]
    previous_schema: Dict[str, Any]
    rules: List[str] = field(default_factory=list)


@dataclass(unsafe_hash=True)
class GuardRuleResult:
    # making this class hashable as guard return output on
    # multiple unmatched properties
    # e.g. primaryIdentifier[*] in createOnlyProperties
    # if there is no match it outputs 4 unmatched properties
    # for user output we only care about unique values that are NOT
    # present anywhere
    check_id: str = field(default="unidentified")
    message: str = field(default="unidentified")
    path: str = field(default="unidentified")


@dataclass
class GuardRuleSetResult:
    """Represents a result of the compliance run.

    Contains passed, failed, skipped and warning rules

    Attributes:
        compliant: rules, that schema(s) passed
        non_compliant: rules, that schema(s) failed
        warning: rules, that schema(s) failed but it's not a hard requirement
        skipped: rules, that are not applicable to the schema(s)
        schema_difference: optional dictionary containing schema difference
    """

    compliant: List[str] = field(default_factory=list)
    non_compliant: Dict[str, List[GuardRuleResult]] = field(default_factory=dict)
    warning: Dict[str, List[GuardRuleResult]] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    schema_difference: Optional[dict] = field(default_factory=dict)

    def merge(self, guard_ruleset_result: Any):
        """Merges the result into a nice mutual set.

        Args:
            guard_ruleset_result (Any): result in a raw form
        """
        if not isinstance(guard_ruleset_result, GuardRuleSetResult):
            raise TypeError("cannot merge with non GuardRuleSetResult type")

        self.compliant.extend(guard_ruleset_result.compliant)
        self.skipped.extend(guard_ruleset_result.skipped)
        self.non_compliant = {
            **self.non_compliant,
            **guard_ruleset_result.non_compliant,
        }
        self.warning = {
            **self.warning,
            **guard_ruleset_result.warning,
        }

    def display(self):
        """Displays a table with compliance results."""
        if (
            not self.compliant
            and not self.non_compliant
            and not self.skipped
            and not self.warning
        ):
            raise ValueError("No Rules have been executed")

        table = Table(title="Schema Compliance Report")

        table.add_column("Rule Name", justify="right", style="cyan", no_wrap=True)
        table.add_column("Check Id", style="magenta")
        table.add_column("Message", style="magenta")
        table.add_column("Path", style="magenta")
        table.add_column("Status", justify="right", style="green")

        for rule in self.skipped:
            table.add_row(rule, "-", "-", "-", "[white]skipped")

        for rule in self.compliant:
            table.add_row(rule, "-", "-", "-", "[green]passed")

        for rule, checks in self.warning.items():
            for check in checks:
                table.add_row(
                    rule,
                    f"[b]{check.check_id}[/b]",
                    f"[b]{check.message}[/b]",
                    "-",
                    "[yellow]warning",
                )

        for rule, checks in self.non_compliant.items():
            for check in checks:
                table.add_row(
                    rule,
                    f"[b]{check.check_id}[/b]",
                    f"[b]{check.message}[/b]",
                    "-" if not check.path else f"[b][red]{check.path}[/b]",
                    "[red]failed",
                )

        console = Console()
        console.print(table)
