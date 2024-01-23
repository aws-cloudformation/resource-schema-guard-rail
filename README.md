# CloudFormation - Resource Schema Guard Rail
![Apache 2.0 License](https://img.shields.io/github/license/aws-cloudformation/resource-schema-guard-rail)
[![Pull Request CI](https://github.com/aws-cloudformation/resource-schema-guard-rail/actions/workflows/pr-ci.yml/badge.svg?branch=main)](https://github.com/aws-cloudformation/resource-schema-guard-rail/actions/workflows/pr-ci.yml)
[![PyPI](https://img.shields.io/pypi/v/resource-schema-guard-rail?label=pypi)](https://badge.fury.io/py/resource-schema-guard-rail)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/resource-schema-guard-rail?label=python)](https://pypi.org/project/resource-schema-guard-rail/)

### Notes
This is not a stable version (Beta), it's still under development

## Overview
AWS CloudFormation Resource Schema Guard Rail is an open-source tool, which uses [CloudFormation Guard](https://github.com/aws-cloudformation/cloudformation-guard/) policy-as-code evaluation engine to assess resource schema compliance. It validates json resource schemas against the AWS CloudFormation modeling best practices.

### Contribute
See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.
#### Rule Development
Read [Guard Rail: Rule Development](docs/RULE_DEVELOPMENT.md) for more information on how to write resource schema rules.

### How to use it?
Schema guard rail package has a built-in library of rules, that CloudFormation believe are the best practices that resource modelers should follow. It supports two types of evaluation - Basic Linting & Breaking Change;

#### Basic Linter (Stateless)
Linter works only with current version of resource schema and runs CloudFormation authored rules, which will highlight problematic schema constructs. A provider developers can run multiple independent schemas at once as well as attach custom rules.

In order to start using Basic Linting you need to run following command:
```bash
$ guard-rail --schema file://path-to-schema-1 --schema file://path-to-schema-2 --rule file://path-to-custom-ruleset1 --rule file://path-to-custom-ruleset2
```

**[List of Linting Rules](docs/BASIC_LINTING.md)**

#### Breaking Change (Stateful)
Along with basic linting, guard rail supports capability of breaking change evaluation. Provider developer must provider two json objects - previous & current versions of the same resource schema. CloudFormation authored rules will be run and evaluation current version of the schema whether it is compliant or not.

In order to start using Basic Linting you need to run following command:
```bash
$ guard-rail --schema file://path-to-schema-1 --schema file://path-to-schema-2 --rule ... --stateful
```

**[List of Breaking Change Rules](docs/BREAKING_CHANGE.md)**


*Additionally, you can specify `format` argument, which will produce a nicely formatted output.

### How to install it locally?

Use following commands

#### Clone github repo
```bash
$ git clone git@github.com:aws-cloudformation/resource-schema-guard-rail.git
```
#### Create Virtual Environment & Activate
```
python3 -m venv env
source env/bin/activate
```

#### Install Package Locally from the root

```
pip install -e . -r requirements.txt
pre-commit install
```

#### Run CI Locally

```
# run all hooks on all files, mirrors what the CI runs
pre-commit run --all-files
```

## License

This project is licensed under the Apache-2.0 License.

## Community

Join us on Discord! Connect & interact with CloudFormation developers &
experts, find channels to discuss and get help for our CLI, cfn-lint, CloudFormation registry, StackSets,
Guard and more:

[![Join our Discord](https://discordapp.com/api/guilds/981586120448020580/widget.png?style=banner3)](https://discord.gg/9zpd7TTRwq)
