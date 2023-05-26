# CloudFormation - Resource Schema Guard Rail

## Common Requirements:
1. Both types of rules **MUST** follow [cloudformation-guard DSL](https://github.com/aws-cloudformation/cloudformation-guard/#guard-dsl)
2. Rule name **MUST** start with `ensure*`
3. Rule might have multiple checks in it
4. Rule Check **MUST** emit error message of the following format:

    ```json
    {
        "result": "...",
        "check_id": "...",
        "message": "..."
    }
    ```
5. Result **MUST** be either `NON_COMPLIANT` or `WARNING`
6. Check_id **MUST** be a unique check code
7. Message **MUST** be a short description why the check is failing

## Basic Linting Rules
### Rule Mechanics
Stateless rules are run over the resource schemas. There is no concept of previous state. Assumption - it evaluates live state of the schema. Rules are supposed to cover json semantics.

##### Sample Schema Snippet
```json
{
    "properties": {
        "Arn": {
            "type": "string"
        }
    },
    ...
}
```
##### Sample Rule

```
let props = properties[ keys == /(Arn|arn|ARN)/ ]
rule ensure_arn_properties_type_string when %props !empty {
    %props.type == 'string'
    <<
    {
        "result": "NON_COMPLIANT",
        "check_id": "ARN_1",
        "message": "arn related property MUST have pattern specified"
    }
    >>
}
```


***
## Stateful Rules

### Rule Mechanics
Stateful rules are run over the difference between two schemas - previous & current version. Stateful module creates a metadiff object, which is following listed below structure:

```json
{
    "keyword": {
        "added": [],
        "removed": [],
        "changed": []
    }
}
```

It currently supports two types of keywords - CloudFormation built and Json native:

##### CloudFormation Built
* `primaryIdentifier`
* `readOnlyProperties`
* `writeOnlyProperties`
* `createOnlyProperties`
* `additionalIdentifiers`

##### JSON Native
* `type`
* `description`
* `enum`
* `maximum`
* `minimum`
* `maxLength`
* `minLength`
* `required`
* `pattern`
* `maxItems`
* `minItems`
* `contains`
* `items`
* `additionalProperties`

##### Sample MetaDiff
```json
{
    "properties": {
        "added": ["/properties/Arn"]
    },
    "minimum": {
        "changed": [
            {
                "property": "/properties/NumberOfDays",
                "old_value": 7,
                "new_value": 8
            }
        ]
    },
    "minLength": {
        "changed": [
            {
                "property": "/properties/Tags/*/Value",
                "old_value": 0,
                "new_value": 1
            }
        ]
    },
    "readOnlyProperties": {
        "added": ["/properties/Arn"]
    }
}
```

##### Sample Rule
```
rule ensure_min_length_new_value_is_positive when minLength exists
{
    minLength.changed[*] {
        this.new_value > 0
        <<
        {
            "result": "NON_COMPLIANT",
            "check_id": "POSVAL",
            "message": "new value for minLength MUST be positive"
        }
        >>
    }
}
```

##### Limitations
###### Combiners
Currently, Stateful module can only process resource schemas without combiners. Combiners support is planned to be implemented later.

* `allOf`
* `anyOf`
* `oneOf`
