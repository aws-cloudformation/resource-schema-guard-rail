# CloudFormation - Resource Schema Guard Rail
## Basic Linting
### Library
#### Arn Related
| Rule Name   |      Check Id      |  Message |
|----------|-------------|------|
| `ensure_arn_properties_type_string` |  `ARN001` | `"arn related property MUST have pattern specified"` |
| `ensure_arn_properties_contain_pattern` |  `ARN002` | `"arn related property MUST have pattern specified"` |

#### Property Related CloudFormation Construct
| Rule Name   |      Check Id      |  Message |
|----------|-------------|------|
| `ensure_primary_identifier_exists_and_not_empty` |  `PID001` | `"primaryIdentifier MUST exist"` |
| |  `PID002` | `"primaryIdentifier MUST contain values"` |
| `ensure_primary_identifier_is_read_or_create_only` |  `PID003` | `"primaryIdentifier MUST be either readOnly or createOnly"` |
| `ensure_create_and_read_only_intersection_is_empty` |  `PR001` | `"read/createOnlyProperties MUST NOT have common properties"` |
| |  `PR002` | `"create/readOnlyProperties MUST NOT have common properties"` |
| `ensure_write_and_read_only_intersection_is_empty` |  `PR003` | `"read/writeOnlyProperties MUST NOT have common properties"` |
| |  `PR004` | `"write/readOnlyProperties MUST NOT have common properties"` |
| `verify_property_notation` |  `PR005` | `"primaryIdentifier MUST have properties defined in the schema"` |
| |  `PR006` | `"createOnlyProperties MUST have properties defined in the schema"` |
| |  `PR007` | `"readOnlyProperties MUST have properties defined in the schema"` |
| |  `PR008` | `"writeOnlyProperties MUST have properties defined in the schema"` |


#### Combiners
| Rule Name   |      Check Id      |  Message |
|----------|-------------|------|
| `ensure_properties_do_not_support_multitype` | `COM001` | `"each property MUST specify type"` |
| | `COM002` | `"type MUST NOT have combined types` |
| | `COM003` | `"property array MUST be modeled via items` |
| | `COM004` | `"property array MUST NOT specify items via anyOf` |
| | `COM005` | `"property array MUST NOT specify items via allOf` |
| | `COM006` | `"property array MUST NOT specify items via oneOf` |

#### Tagging
| Rule Name   |      Check Id      |  Message |
|----------|-------------|------|
| `check_if_taggable_is_used` | `TAG001` | `"'taggable' is deprecated, please used 'tagging' property"` |
| `ensure_tagging_is_specified` | `TAG002` | `"'tagging' MUST be specified"` |
| `ensure_taggable_and_tagging_do_not_coexist` | `TAG003` | `"'taggable' and 'tagging' MUST NOT coexist"` |
| `ensure_property_tags_exists_v1` | `TAG004` | `"Resource MUST implement Tags property if 'taggable' is true"` |
| `ensure_property_tags_exists_v2` | `TAG005` | `"'tagging' MUST BE a struct"` |
| | `TAG006` | `"'taggable' MUST BE specified when 'tagging' is provided"` |
| | `TAG007` | `"Resource MUST provide 'tagOnCreate' {true\|false} if 'tagging.taggable' is true"` |
| | `TAG008` | `"Resource MUST provide 'tagUpdatable' {true\|false} if 'tagging.taggable' is true"` |
| | `TAG009` | `"Resource MUST provide 'cloudFormationSystemTags' {true\|false} if 'tagging.taggable' is true"` |
| | `TAG010` | `"Resource MUST provide 'tagProperty' {/properties/Tags} if 'tagging.taggable' is true"` |
| | `TAG011` | `"Resource MUST implement Tags property if 'tagging.taggable' is true"` |
| | `TAG012` | `"Resource MUST implement Tags property if 'tagging.taggable' is true"` |
| | `TAG013` | `"'tagProperty' MUST specify property defined in the schema"` |
| | `TAG014` | `"Resource MUST provide `permission` if `tagging.taggable` is true"` |

#### Permissions
| Rule Name   |      Check Id      |  Message |
|----------|-------------|------|
| `ensure_resource_create_handler_exists_and_have_permissions` | `PER001` | `"Resource MUST implement create handler"` |
| | `PER002` | `"Resource MUST NOT specify wildcard permissions for create handler"` |
| `ensure_resource_read_handler_exists_and_have_permissions` | `PER003` | `"Resource MUST implement read handler"` |
| | `PER004` | `"Resource MUST NOT specify wildcard permissions for read handler"` |
| `ensure_resource_update_handler_exists_and_have_permissions` | `PER005` | `"Resource SHOULD implement update handler"` |
| | `PER006` | `"Resource update handler MUST have permissions list specified"` |
| | `PER006` | `"Resource update handler MUST have non-empty permissions"` |
| | `PER007` | `"Resource MUST NOT specify wildcard permissions for update handler"` |
| `ensure_resource_delete_handler_exists_and_have_permissions` | `PER008` | `"Resource MUST implement delete handler"` |
| | `PER009` | `"Resource MUST NOT specify wildcard permissions for delete handler"` |
| `ensure_resource_list_handler_exists_and_have_permissions` | `PER010` | `"Resource MUST implement list handler"` |
| | `PER011` | `"Resource MUST NOT specify wildcard permissions for list handler"` |

#### Other Checks
| Rule Name   |      Check Id      |  Message |
|----------|-------------|------|
| `ensure_description_is_descriptive` | `GN001` | `"description should start with 'Resource Type definition for ...'"` |
| `ensure_sourceUrl_uses_https` | `GN002` | `"sourceUrl should use https protocol"` |
| `ensure_default_replacementStrategy` | `GN003` | `"replacement strategy should not implement create_then_delete"` |
