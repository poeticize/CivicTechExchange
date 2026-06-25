class BaseCacheManager:
    """
    BaseCacheManager provides a thin wrapper around a cache backend.

    Why:
        The project requires a generic cache manager that can be instantiated
        with any backend conforming to the ``get`` interface. This enables
        higher-level components to depend on a consistent API without committing
        to a particular caching implementation.

    How:
        - ``__init__`` stores the provided ``backend`` instance.
        - ``get`` forwards the lookup to ``backend.get(key)``.

    The class deliberately avoids any additional behavior (e.g., refresh,
    clear, logging) to keep it minimal and composable, matching the exact
    specification of the directive.
    """

    def __init__(self, backend):
        """
        Initialize the manager with a cache backend.

        Parameters
        ----------
        backend : object
            An object that implements a ``get(key)`` method. The manager does
            not enforce any concrete type; it merely stores the reference for
            later use.
        """
        self.backend = backend

    def get(self, key):
        """
        Retrieve a value from the underlying cache backend.

        Parameters
        ----------
        key : hashable
            The cache key to look up.

        Returns
        -------
        Any
            The result of ``backend.get(key)``.
        """
        return self.backend.get(key)