"""
FarmTech Context processors
"""

import json
from .utils.user_utils import get_user_group_data


def farmtech_user(request):
    """
    Add FarmTech user data to the template context

    Usage in templates:
        {{ farmtech_user.auth_groups }}
        {{ farmtech_user.group_members }}
        {{ farmtech_user.area_groups }}
    """
    if not request.user or not request.user.is_authenticated:
        anonymous_user_data = {
            "username": "",
            "is_authenticated": False,
            "is_superuser": False,
            "auth_groups": [],
            "group_members": [],
            "area_groups": [],
            "permissions": [],
        }
        return {
            "farmtech_user": anonymous_user_data,
            "farmtech_user_json": json.dumps(anonymous_user_data),
        }

    user_data = get_user_group_data(request.user)
    permissions = list(request.user.get_all_permissions())

    # Aggiungi informazioni base dell'utente
    farmtech_user_data = {
        "username": request.user.username,
        "is_authenticated": request.user.is_authenticated,
        "is_superuser": request.user.is_superuser,
        "auth_groups": user_data["auth_groups"],
        "group_members": user_data["group_members"],
        "area_groups": user_data["area_groups"],
        "permissions": permissions,
    }

    return {
        "farmtech_user": farmtech_user_data,
        "farmtech_user_json": json.dumps(farmtech_user_data),
    }
