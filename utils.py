
JSM_STATE_FILE = "jsm_state.json"

CUSTOM_FIELDS_TO_CREATE = [
    {
        "name": "vm_provisioning_disk_size",
        "description": "La taille du disque à attacher à une VM",
        "type": "com.atlassian.jira.plugin.system.customfieldtypes:float",
        "searcherKey": "com.atlassian.jira.plugin.system.customfieldtypes:exactnumber",
        "defaultValue": 20
    },
    {
        "name": "vm_provisioning_disk_fs_type",
        "description": "Le type de file system du disque à attacher à une VM",
        "type": "com.atlassian.jira.plugin.system.customfieldtypes:select",
        "searcherKey": "com.atlassian.jira.plugin.system.customfieldtypes:multiselectsearcher",
        "options": [
            {"value": "NFS"},
            {"value": "XFS"},
            {"value": "ZFS"},
            {"value": "EXT4"},
            {"value": "EXT3"},
            {"value": "EXT2"},
            {"value": "BTRFS"},
        ],
        "defaultValue": "NFS",
    },
    {
        "name": "vm_provisioning_disk_mount_point",
        "description": "Le point de montage du disque à attacher à une VM",
        "type": "com.atlassian.jira.plugin.system.customfieldtypes:textfield",
        "searcherKey": "com.atlassian.jira.plugin.system.customfieldtypes:textsearcher",
        "defaultValue": "/mnt/data"
    },
]

