# custom_models/db_router.py
class CustomRouter:
    route_app_labels = {'farmtech'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            if model and not model._meta.managed:
                return 'datastore'
        return None  # lascia decidere il router originale

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            if model and not model._meta.managed:
                return 'datastore'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            # evita migrazioni sui modelli managed=False
            model = hints.get('model')
            if model and not model._meta.managed:
                return False
            # solo sul database default per migrazioni (se necessario)
            return db == 'default'
        return None
