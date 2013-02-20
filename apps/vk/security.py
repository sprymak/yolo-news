from django.contrib.auth.models import User

from utils.django import get_object_or_none
import rbac


class Roles:
    ALL = 'vk.all'
    ANONYMOUS = 'vk.anonymous'
    SUPERUSER = 'vk.superuser'


assign_roles = rbac.assign_roles
has_permissions = rbac.has_permissions
grant_permission = rbac.grant_permission
revoke_permission = rbac.revoke_permission


def get_user_security_subjects(user):
    """ Return collection of security subjects associated with user.
        Currently, this collection includes the user, as well as the groups
        to which he belongs and locations and companies associated with
        the user.

        Subject representing an authenticated user or entity (both referred
        to as "subject").

        :param user: user id or User class instance.
    """
    if isinstance(user, (int, long, basestring)):
        user = get_object_or_none(User, pk=user)
    if not isinstance(user, User) or user.is_anonymous():
        return []
    profile = user.get_profile()
    return ([user] +
        [g for g in user.groups.all()] +
        [c for c in profile.companies.all()] +
        [l for l in profile.cities.all()])


def get_user_roles(user, obj):
    """ Return collection of active user roles associated with object or
        [anonymous] if user is not authenticated or is not User class instance.

        :param user: user id or User class instance.
        :param obj: target object. It can be a Model instance class or its
            descendant.
    """
    roles = [Roles.ALL]
    if isinstance(user, (int, long, basestring)):
        user = get_object_or_none(User, pk=user)
    if isinstance(user, User) and not user.is_anonymous():
        roles.extend(rbac.get_active_roles(obj,
            get_user_security_subjects(user)))
    else:
        roles.extend([Roles.ANONYMOUS])
    return roles


def permission_required(operation, lookup_variables=None, **kwargs):
    """ Decorator for views that checks if user has a particular permission
        enabled.
    """
    def internal(view):
        def wrap(request, *args, **kwargs):
            obj = None
            if lookup_variables:
                model, lookups = lookup_variables[0], lookup_variables[1:]
                if callable(lookup_variables):
                    obj = lookup_variables(**kwargs)
                else:
                    lookup_dict = {}
                    for lookup, view_arg in zip(lookups[::2], lookups[1::2]):
                        if view_arg not in kwargs:
                            raise Exception("Argument %s was not passed "
                                "into view function" % view_arg)
                        lookup_dict[lookup] = kwargs[view_arg]
                    from django.shortcuts import get_object_or_404
                    obj = get_object_or_404(model, **lookup_dict)

            roles = get_user_roles(request.user, obj)
            if not has_permissions(obj, operation, roles):
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied

            return view(request, *args, **kwargs)
        return wrap
    return internal
