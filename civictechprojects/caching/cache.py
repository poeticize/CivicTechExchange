from collections import Counter
from common.caching.cache import Cache
from common.helpers.dictionaries import merge_dicts


class BaseCacheManager:
    """Shared logic for simple model-keyed cache managers.

    Subclasses pass a zero-arg ``model_loader`` callable that returns the Django
    model class. The import is deferred to first use of ``_get_key`` so this
    module can be imported before Django's app registry is fully populated.
    """

    def __init__(self, model_loader, key_prefix):
        self._model_loader = model_loader
        self._key_prefix = key_prefix
        self._model_class = None  # resolved lazily on first _get_key call

    def get(self, obj):
        return Cache.get(self._get_key(obj))

    def refresh(self, obj, value):
        Cache.refresh(self._get_key(obj), value)
        return value

    def _get_key(self, obj):
        if self._model_class is None:
            self._model_class = self._model_loader()
        obj_id = str(obj.id) if isinstance(obj, self._model_class) else str(obj)
        return self._key_prefix + obj_id


class ProjectCacheManager(BaseCacheManager):
    def __init__(self):
        def _load():
            from civictechprojects.models import Project
            return Project
        super().__init__(_load, 'project_')


class EventCacheManager(BaseCacheManager):
    def __init__(self):
        def _load():
            from civictechprojects.models import Event
            return Event
        super().__init__(_load, 'event_')


class EventProjectCacheManager(BaseCacheManager):
    def __init__(self):
        def _load():
            from civictechprojects.models import EventProject
            return EventProject
        super().__init__(_load, 'eventproject_')


class GroupCacheManager(BaseCacheManager):
    def __init__(self):
        def _load():
            from civictechprojects.models import Group
            return Group
        super().__init__(_load, 'group_')


class ProjectSearchTagsCacheManager:
    _cache_key_prefix = 'project_search_tags_'

    def get(self, event=None, group=None):
        key = self._get_key(event=event, group=group)
        return Cache.get(key) or self.refresh(event=event, group=group)

    def refresh(self, event=None, group=None):
        log_line = 'Re-caching tag counts'
        if event is not None:
            log_line += ' for event:' + str(event.id)
        elif group is not None:
            log_line += ' for group:' + str(group.id)
        print(log_line)
        key = self._get_key(event=event, group=group)
        value = self._projects_tag_counts(event=event, group=group)
        Cache.refresh(key, value)
        return value

    def _get_key(self, event=None, group=None):
        key = self._cache_key_prefix
        if event is not None:
            key += 'event_' + str(event.id)
        elif group is not None:
            key += 'group_' + str(group.id)
        else:
            key += 'all'
        return key

    @staticmethod
    def _projects_tag_counts(event=None, group=None):
        from civictechprojects.models import Project
        if event is not None:
            projects = event.get_linked_projects()
        elif group is not None:
            projects = group.get_group_projects(approved_only=True)
        else:
            projects = Project.objects.filter(is_searchable=True, is_private=False)
        issues, technologies, stage, organization, organization_type, positions = [], [], [], [], [], []
        if projects:
            for project in projects:
                issues += project.project_issue_area.slugs()
                technologies += project.project_technologies.slugs()
                stage += project.project_stage.slugs()
                organization += project.project_organization.slugs()
                organization_type += project.project_organization_type.slugs()
                project_positions = project.get_project_positions().filter(is_hidden=False)
                positions += map(lambda position: position.position_role.slugs()[0], project_positions)
        return merge_dicts(
            Counter(issues), Counter(technologies), Counter(stage),
            Counter(organization), Counter(organization_type), Counter(positions)
        )


class UserContextCacheManager:
    _cache_key_prefix = 'user_'

    def get(self, user):
        return Cache.get(self._get_key(user))

    def refresh(self, user, value):
        print('Re-caching user context for user:' + str(user.id))
        Cache.refresh(self._get_key(user), value, 300)
        return value

    def clear(self, user):
        print('Clearing user context for user:' + str(user.id))
        Cache.clear(self._get_key(user))

    def _get_key(self, user):
        return self._cache_key_prefix + str(user.id)


ProjectCache = ProjectCacheManager()
EventCache = EventCacheManager()
EventProjectCache = EventProjectCacheManager()
GroupCache = GroupCacheManager()
ProjectSearchTagsCache = ProjectSearchTagsCacheManager()
UserContextCache = UserContextCacheManager()
