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
from typing import Any, Dict, List

from colorama import Fore, init
from rpdk.guard_rail.utils.miscellaneous import jinja_loader

init()

FAILED_HEADER = f"{Fore.RED}[FAILED]:{Fore.RESET}"
WARNING_HEADER = f"{Fore.YELLOW}[WARNING]:{Fore.RESET}"
PASSED_HEADER = f"{Fore.GREEN}[PASSED]:{Fore.RESET}"


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
    """

    compliant: List[str] = field(default_factory=list)
    non_compliant: Dict[str, List[GuardRuleResult]] = field(default_factory=dict)
    warning: Dict[str, List[GuardRuleResult]] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)

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

    def __str__(self):
        if (
            not self.compliant
            and not self.non_compliant
            and not self.skipped
            and not self.warning
        ):
            return "Couldn't retrieve the result"

        environment = jinja_loader(__name__)
        template = environment.get_template("guard-result-pojo.output")
        return template.render(
            skipped_rules=self.skipped,
            passed_rules=self.compliant,
            failed_rules=self.non_compliant,
            warning_rules=self.warning,
            failed_header=FAILED_HEADER,
            warning_header=WARNING_HEADER,
            passed_header=PASSED_HEADER,
        )
