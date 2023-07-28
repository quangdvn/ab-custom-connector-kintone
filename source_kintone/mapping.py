# kintone Data Type: https://kintone.dev/en/docs/kintone/rest-api/apps/get-form-fields/
# kintone Date formats: https://kintone.dev/en/docs/kintone/rest-api/overview/kintone-rest-api-overview/#date-formats
# CALC: Calculated
# CATEGORY: Category
# CHECK_BOX: Check box
# CREATED_TIME: Created datetime
# CREATOR: Created by
# DATE: Date
# DATETIME: Date and time
# DROP_DOWN: Drop-down
# FILE: Attachment
# LINK: Link
# MODIFIER: Updated by
# MULTI_LINE_TEXT: Text Area
# MULTI_SELECT: Multi-choice
# NUMBER: Number, or Look-up*
# RADIO_BUTTON: Radio button
# RECORD_NUMBER: Record number
# REFERENCE_TABLE: Related Records
# RICH_TEXT: Rich text
# SINGLE_LINE_TEXT: Text, or Look-up*
# STATUS: Process management status
# STATUS_ASSIGNEE: Assignee of the Process Management status
# SUBTABLE: Table
# TIME: Time
# UPDATED_TIME: Updated datetime
# USER_SELECT: User selection
# ==================================================================================================================================
# Airbyte Data Type: https://docs.airbyte.com/understanding-airbyte/supported-data-types/
# String	{"type": "string""}	"foo bar"
# Boolean	{"type": "boolean"}	true or false
# Date	{"type": "string", "format": "date"}	"2021-01-23", "2021-01-23 BC"
# Timestamp with timezone	{"type": "string", "format": "date-time", "airbyte_type": "timestamp_with_timezone"}	"2022-11-22T01:23:45.123456+05:00", "2022-11-22T01:23:45Z BC"
# Timestamp without timezone	{"type": "string", "format": "date-time", "airbyte_type": "timestamp_without_timezone"}	"2022-11-22T01:23:45", "2022-11-22T01:23:45.123456 BC"
# Time without timezone	{"type": "string", "airbyte_type": "time_with_timezone"}	"01:23:45.123456", "01:23:45"
# Time with timezone	{"type": "string", "airbyte_type": "time_without_timezone"}	"01:23:45.123456+05:00", "01:23:45Z"
# Integer	{"type": "integer"} or {"type": "number", "airbyte_type": "integer"}	42
# Number	{"type": "number"}	1234.56
# Array	{"type": "array"}; optionally items	[1, 2, 3]
# Object	{"type": "object"}; optionally properties	{"foo": "bar"}
# ==================================================================================================================================

KINTONE_TO_AIRBYTE_MAPPING = {
    "RECORD_NUMBER": {"type": ["null", "integer"]},
    "__ID__": {"type": ["null", "integer"]},
    "__REVISION__": {"type": ["null", "integer"]},
    # Assign as array of objects with undefined properties for now
    "CREATOR": {"type": ["null", "object"], "additionalProperties": True},

    # Assign as array of objects with undefined properties for now
    "MODIFIER": {"type": ["null", "object"], "additionalProperties": True},

    "CREATED_TIME": {"type": ["null", "string"], "format": "date-time", "airbyte_type": "timestamp_with_timezone"},
    "UPDATED_TIME": {"type": ["null", "string"], "format": "date-time", "airbyte_type": "timestamp_with_timezone"},

    # Assign as string for now, maybe a Look-up
    "SINGLE_LINE_TEXT": {"type": ["null", "string"]},
    # Assign as number and string for now, maybe a Look-up
    "NUMBER": {"type": ["null", "number", "string"]},

    # Assign as string for now
    "CALC": {"type": ["null", "string"]},
    "MULTI_LINE_TEXT": {"type": ["null", "string"]},
    "RICH_TEXT": {"type": ["null", "string"]},

    # Assign as array of strings for now
    "CHECK_BOX": {"type": ["null", "array"], "items": {"type": "string", }},
    # Assign as string for now
    "RADIO_BUTTON": {"type": ["null", "string"]},
    # Assign as string for now
    "DROP_DOWN": {"type": ["null", "string"]},

    # Assign as array of strings for now
    "MULTI_SELECT": {"type": ["null", "array"], "items": {"type": "string", }},

    # Assign as array of objects for now
    "FILE": {"type": ["null", "array"], "items": {"type": ["null", "string"]}},

    "LINK": {"type": ["null", "string"]},
    "DATE": {"type": ["null", "string"], "format": "date", "airbyte_type": "string", "airbyte_format": "%Y-%m-%d"},

    # Consider to remove airbyte_type in the future
    "TIME": {"type": ["null", "string"], "airbyte_type": "time_without_timezone"},
    "DATETIME": {"type": ["null", "string"], "format": "date-time", "airbyte_type": "timestamp_with_timezone"},

    # Assign as array of objects with undefined properties for now
    "USER_SELECT": {"type": ["null", "object"], "additionalProperties": True},
    # Assign as array of objects with undefined properties for now
    "ORGANIZATION_SELECT": {"type": ["null", "array"], "items": {"type": ["null", "string"]}},
    # Assign as array of objects with undefined properties for now
    "GROUP_SELECT": {"type": ["null", "array"], "items": {"type": ["null", "string"]}},

    # Assign as array of strings for now
    "CATEGORY": {"type": ["null", "array"], "items": {"type": ["null", "string"], }},
    "STATUS": {"type": ["null", "string"]},

    # Assign as array of objects with undefined properties for now
    "STATUS_ASSIGNEE": {"type": ["null", "object"], "additionalProperties": True},

    # Assign as array of objects with undefined properties for now
    "SUBTABLE": {"type": ["null", "array"], "items": {"type": ["null", "string"]}},

    # Assign as array of objects with undefined properties for now
    "REFERENCE_TABLE": {"type": ["null", "object"], "additionalProperties": True},
}
