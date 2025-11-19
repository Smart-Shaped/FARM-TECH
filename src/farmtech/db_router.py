"""
custom_models/db_router.py
"""

class CustomRouter:
    """
    A router to control all database operations on models in the
    auth and contenttypes applications.
    """
    route_app_labels = {'farmtech'}

    def db_for_read(self, model, **hints):
        """
        Attempts to read auth models go to auth db.
        """
        if model._meta.app_label in self.route_app_labels:
            if model and not model._meta.managed:
                return 'datastore'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth models go to auth db.
        """
        if model._meta.app_label in self.route_app_labels:
            if model and not model._meta.managed:
                return 'datastore'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the auth or contenttypes apps is
        involved.
        """
        if (obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the auth and contenttypes apps only appear in the
        'auth_db' database.
        """
        if app_label in self.route_app_labels:
            # avoid migrations for non-managed models
            model = hints.get('model')
            if model and not model._meta.managed:
                return False
            # all other models go to default
            return db == 'default'
        return None
