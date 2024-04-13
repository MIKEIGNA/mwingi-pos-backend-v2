from django.contrib.auth.models import Permission

class UserViewPermissionUtils:

    @staticmethod
    def get_user_token_view_permission_dict(user):

        groups = user.groups.all()
        codenames = []
        for g in groups:
            perms = Permission.objects.filter(group=g).values_list('codename')

            for p in perms: codenames.append(p[0])

        return {'user_perms': codenames}





