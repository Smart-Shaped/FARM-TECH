"""
Custom menu json
"""

import json
from django import template
from django.conf import settings
from django.utils.translation import gettext as _
from avatar.templatetags.avatar_tags import avatar_url
from geonode.base.models import Menu, MenuItem


register = template.Library()


def _get_request_user(context):
    request = context.get("request")
    if request:
        return request.user

def _handle_single_item(menu_item):
    m_item = {}
    m_item["type"] = "link"
    m_item["href"] = menu_item.url
    m_item["label"] = menu_item.title
    if menu_item.blank_target:
        m_item["target"] = "_blank"
    return m_item


def _is_mobile_device(context):
    if context and "request" in context:
        req = context["request"]
        return req.user_agent.is_mobile
    return False

@register.simple_tag(takes_context=True)
def get_custom_base_left_topbar_menu(context):
    """Returns the menu as JSON string with translations already resolved."""
    user = _get_request_user(context)
    items = [
        {
            "type": "link",
            "href": "/research",
            "label": _("menu_research_areas"),
            "id": "menu-research",
        }
    ]


    if user and user.has_perm('farmtech.inference'):
        items += [
             {
                "type": "link",
                "href": "/inference",
                "label": _("menu_inference"),
                "id": "menu-inference",
            }
        ]
    if user and user.has_perm('farmtech.uploader'):
        items += [
            {
                "type": "link",
                "href": "/uploader",
                "label": _("menu_data_upload"),
                "id": "menu-uploader",
            },
            {
                "type": "dropdown",
                "label": _("menu_resources"),
                "id": "menu-resources",
                "items": [
                    {
                        "type": "link",
                        "href": "/catalogue/#/all",
                        "label": _("menu_all_resources"),
                        "id": "menu-all-resources",
                    },
                    {
                        "type": "link",
                        "href": "/catalogue/#/datasets",
                        "label": _("menu_datasets"),
                        "id": "menu-datasets",
                    },
                    {
                        "type": "link",
                        "href": "/catalogue/#/maps",
                        "label": _("menu_maps"),
                        "id": "menu-maps",
                    },
                    {
                        "type": "link",
                        "href": "/catalogue/#/documents",
                        "label": _("menu_documents"),
                        "id": "menu-documents",
                    },
                    {
                        "type": "link",
                        "href": "/catalogue/#/geostories",
                        "label": _("menu_geostories"),
                        "id": "menu-geostories",
                    },
                    {
                        "type": "link",
                        "href": "/catalogue/#/dashboards",
                        "label": _("menu_dashboards"),
                        "id": "menu-dashboards",
                    }
                ]
            }
        ]

    return items

@register.simple_tag(takes_context=True)
def get_custom_base_left_topbar_menu_json(context):
    """Returns the menu as JSON string with translations already resolved."""
    items = get_custom_base_left_topbar_menu(context)
    return json.dumps(items)

@register.simple_tag(takes_context=True)
def get_custom_user_menu(context):
    """Returns the menu as JSON string with translations already resolved."""
    is_mobile = _is_mobile_device(context)

    user = _get_request_user(context)

    if not user or (user and not user.is_authenticated):
        return [
            {"label": "Sign in", "type": "link", "href":
                "/account/login/?next=/catalogue/#/dashboards"},
        ]

    devider = {"type": "divider"}

    profile_link = {
        "type": "link",
        # get href of user profile
        "href": user.get_absolute_url(),
        "label": "Profile",
    }

    logout = {"type": "link", "href": "/auth/logout/", "label": "Log out"}

    if is_mobile:
        return [
            {
                # get src of user avatar
                "image": avatar_url(user),
                "type": "dropdown",
                "className": "gn-user-menu-dropdown",
                "items": [profile_link, devider, logout],
            }
        ]

    profile = {
        # get src of user avatar
        "image": avatar_url(user),
        "type": "dropdown",
        "className": "gn-user-menu-dropdown",
        "items": [
            profile_link,
            {
                "type": "link",
                "href": "/social/recent-activity",
                "label": "Recent activity",
            },
            {
                "type": "link",
                "href": "/catalogue/#/search/?f=favorite",
                "label": "Favorites",
            },
            {"type": "link", "href": "/messages/inbox/", "label": "Inbox"},
            devider,
        ],
    }
    general = [{"type": "link", "href": "/help/", "label": "Help"}, devider, logout]
    monitoring = []
    if settings.MONITORING_ENABLED:
        monitoring = [
            devider,
            {"type": "link", "href": "/monitoring/", "label": "Monitoring & Analytics"},
        ]
    admin_only = (
        [
            {"type": "link", "href": "/admin/", "label": "Admin"},
            {
                "type": "link",
                "href": settings.GEOSERVER_WEB_UI_LOCATION,
                "label": "GeoServer",
            },
        ]
        + monitoring
        + [devider]
        + general
    )

    if user.is_superuser:
        profile["items"].extend(admin_only)
    else:
        profile["items"].extend(general)

    return [profile]


@register.simple_tag
def get_menu_json(placeholder_name):
    """Returns the menu as JSON string with translations already resolved."""
    menus = {
        m: MenuItem.objects.filter(menu=m).order_by("order")
        for m in Menu.objects.filter(placeholder__name=placeholder_name)
    }
    ms = []
    for menu, menu_items in menus.items():
        if len(menu_items) > 1:
            m = {}
            m["label"] = menu.title
            m["type"] = "dropdown"
            m["items"] = []
            for menu_item in menu_items:
                m_item = _handle_single_item(menu_item)
                m["items"].append(m_item)

            ms.append(m)
        if len(menu_items) == 1:
            m = _handle_single_item(menu_items.first())
            ms.append(m)
    return ms


@register.filter
def to_json(value):
    """Converts a Python object to JSON string."""
    return json.dumps(value)
