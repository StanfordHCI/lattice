MOCK_INTERACTION_DATA = [
    {
    "interactions": [
        {
            "interaction": "User opens Slack and messages Nitya about the party. They discuss the details of the party and agree to meet at the venue. User then closes Slack.",
            "metadata": {"time": "2026-04-21 10:00:00"}
        },
        {
            "interaction": "User opens Figma and starts designing the party invitation. They spend 10 minutes designing the invitation and then saves it as a draft. User then closes Figma.",
            "metadata": {"time": "2026-04-21 10:05:00"}
        }
    ],
    "time": "2026-04-21 10:00:00"
    }, 
    {
        "interactions": [
            {
                "interaction": "User opens Jira and starts working on the party invitation. They spend 10 minutes working on the invitation and then saves it as a draft. User then closes Jira.",
                "metadata": {"time": "2026-04-21 10:10:00"}
            },
            {
                "interaction": "User opens Figma and starts designing the party invitation. They spend 10 minutes designing the invitation and then saves it as a draft. User then closes Figma.",
                "metadata": {"time": "2026-04-21 10:15:00"}
            }
        ],
        "time": "2026-04-21 10:10:00"
    }
]

MOCK_OBSERVATIONS = [
    {
        "id": 0,
        "observation": "User is feeling happy about the party",
        "confidence": 10,
        "metadata": {"input_session": 0, "time": "2026-04-21 10:00:00"}
    },
    {
        "id": 1,
        "observation": "User is feeling sad about the party",
        "confidence": 10,
        "metadata": {"input_session": 0, "time": "2026-04-21 10:05:00"}
    },
    {
        "id": 2,
        "observation": "User is feeling happy about the party",
        "confidence": 10,
        "metadata": {"input_session": 0, "time": "2026-04-21 10:10:00"}
    },
    {
        "id": 3,
        "observation": "User is feeling sad about the party",
        "confidence": 10,
        "metadata": {"input_session": 0, "time": "2026-04-21 10:15:00"}
    },
    {
        "id": 4,
        "observation": "User is feeling happy about the party",
        "confidence": 10,
        "metadata": {"input_session": 1, "time": "2026-04-29 10:00:00"}
    },
    {
        "id": 5,
        "observation": "User is feeling sad about the party",
        "confidence": 10,
        "metadata": {"input_session": 1, "time": "2026-05-22 10:05:00"}
    }
]