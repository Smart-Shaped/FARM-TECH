"""
Utility functions for user group management and filtering
"""


def get_user_group_data(user):
    """
    Ottiene i dati dei gruppi dell'utente con mapping tra GroupProfile e AuthGroup.

    Returns:
        dict: {
            'auth_groups': [{'id': int, 'pk': int, 'name': str}, ...],
            'group_members': [{
                'membership_id': int,
                'group_profile_id': int,
                'group_profile_pk': int,
                'group_slug': str,
                'role': str,
                'auth_group_id': int  # ID del gruppo auth corrispondente allo slug
            }, ...],
            'area_groups': [str, ...]  # Lista dei nomi dei gruppi area-*-manager
        }
    """
    if not user or not user.is_authenticated:
        return {
            'auth_groups': [],
            'group_members': [],
            'area_groups': []
        }

    # Ottieni tutti i gruppi auth dell'utente
    auth_groups = []
    auth_groups_map = {}  # name -> id mapping

    for group in user.groups.all():
        group_data = {
            'id': group.id,
            'pk': group.pk,
            'name': group.name
        }
        auth_groups.append(group_data)
        auth_groups_map[group.name] = group.id

    # Ottieni i GroupProfile (groupmember_set)
    group_members = []
    group_members_set = user.groupmember_set.all()

    for gm in group_members_set:
        # Trova l'ID del gruppo auth che corrisponde allo slug del GroupProfile
        auth_group_id = auth_groups_map.get(gm.group.slug)

        member_data = {
            'membership_id': gm.id,
            'group_profile_id': gm.group.id,
            'group_profile_pk': gm.group.pk,
            'group_slug': gm.group.slug,
            'role': gm.role,
            'auth_group_id': auth_group_id
        }
        group_members.append(member_data)

    #TODO: modificare con i nomei che useremo nelle fixture - Estrai i gruppi area-*-manager (usati per i template Excel)
    area_groups = [
        group['name']
        for group in auth_groups
        if group['name'].startswith('azione-')
    ]

    return {
        'auth_groups': auth_groups,
        'group_members': group_members,
        'area_groups': area_groups
    }


def get_area_groups(user):
    """
    Estrae solo i nomi dei gruppi area-X-manager dell'utente.
    Funzione di compatibilità con il codice esistente.
    """
    user_data = get_user_group_data(user)
    return user_data['area_groups']
