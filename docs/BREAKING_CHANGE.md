# CloudFormation - Resource Schema Guard Rail
## Breaking Change Rules
### Library
#### Property Related CloudFormation Construct

| Rule Name   |      Check Id      |  Message |
|----------|-------------|------|
| `ensure_old_property_not_removed` |  `PR001` | `"Resource properties MUST NOT be removed"` |
|`ensure_old_property_not_turned_immutable`|`PR002`|`"Only NEWLY ADDED properties can be marked as createOnlyProperties"`|
|`ensure_old_property_not_turned_writeonly`|`PR003`|`"Only NEWLY ADDED properties can be marked as writeOnlyProperties"`|
|`ensure_old_property_not_removed_from_readonly`|`PR004`|`"Only NEWLY ADDED properties can be marked as readOnlyProperties"`|
||`PR005`|`"Resource properties MUST NOT be removed from readOnlyProperties"`|

***
#### Primary Identifier
| Rule Name   |      Check Id      |  Message |
|----------|------------|------|
|`ensure_primary_identifier_not_changed`|`PID001`|`"primaryIdentifier cannot add more members"`|
||`PID002`|`"primaryIdentifier cannot remove members"`|

***
#### Required
| Rule Name   |      Check Id      |  Message |
|----------|-------------|------|
|`ensure_no_more_required_properties`|`RQ001`|`"cannot add more REQUIRED properties"`|

***
#### Type
| Rule Name   |      Check Id      |  Message |
|----------|-------------|------|
|`ensure_property_type_not_changed`|`TP001`|`"Only NEWLY ADDED properties can have new type added"`|
||`TP002`|`"cannot remove TYPE from a property"`|
||`TP003`|`"cannot change TYPE of a property"`|

***
#### Json Related Validation Constructs
| Rule Name   |      Check Id      | Message                                                    |
|----------|-------------|------------------------------------------------------------|
|`ensure_enum_not_changed`|`ENM001`| `"CANNOT remove values from enum"`                         |
|`ensure_minlength_not_contracted`|`ML001`| `"cannot remove minLength from properties"`                |
||`ML002`|`"only NEWLY ADDED properties can have additional minLength constraint"`|
||`ML003`|`"new minLength value cannot exceed old value"`|
|`ensure_maxlength_not_contracted`|`ML004`| `"cannot remove maxLength from properties"`                |
||`ML005`|`"only NEWLY ADDED properties can have additional maxLength constraint"`|
||`ML006`|`"new maxLength value cannot be less than the old value"`|
|`ensure_property_string_pattern_not_changed`|`PAT001`| `"Only NEWLY ADDED properties can have new pattern added"` |
||`PAT002`|`"cannot remove PATTERN from a property"`|
||`PAT003`|`"cannot change PATTERN of a property"`|
|`ensure_minitems_not_contracted`|`MI001`| `"cannot remove minItems from properties"`                 |
||`MI002`|`"only NEWLY ADDED properties can have additional minItems constraint"`|
||`MI003`|`"new minItems value cannot exceed old value"`|
|`ensure_maxitems_not_contracted`|`MI004`| `"cannot remove maxItems from properties"`                 |
||`MI005`|`"only NEWLY ADDED properties can have additional maxItems constraint"`|
||`MI006`|`"new maxItems value cannot be less than the old value"`|
|`ensure_minimum_not_contracted`|`MI007`| `cannot remove minimum from properties`                    |
||`MI008`|`"only NEWLY ADDED properties can have additional minimum constraint"`|
||`MI009`|`"new minimum value cannot exceed old value"`|
||`MI010`|`"cannot remove maximum from properties"`|
||`MI011`|`"only NEWLY ADDED properties can have additional maximum constraint"`|
||`MI012`|`"new maximum value cannot be less than the old value"`|
