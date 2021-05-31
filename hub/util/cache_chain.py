from typing import List
from uuid import uuid1
from hub.constants import MB
from hub.core.storage.lru_cache import LRUCache
from hub.core.storage import StorageProvider, MemoryProvider, LocalProvider
from hub.util.exceptions import ProviderSizeListMismatch, ProviderListEmptyError


def get_cache_chain(storage_list: List[StorageProvider], size_list: List[int]):
    """Returns a chain of storage providers as a cache

    Args:
        storage_list (List[StorageProvider]): The list of storage providers needed in a cache.
            Should have atleast one provider in the list.
            If only one provider, LRU cache isn't created and the provider is returned.
        size_list (List[int]): The list of sizes of the caches.
            Should have size 1 less than provider_list and specifies size of cache for all providers except the last one.
            The last one is the primary storage and is assumed to have infinite space.

    Returns:
        StorageProvider: Returns a cache containing all the storage providers in cache_list if cache_list has 2 or more elements.
            Returns the provider if the provider_list has only one provider.

    Raises:
        ProviderListEmptyError: If the provider list is empty.
        ProviderSizeListMismatch: If the len(size_list) + 1 != len(provider_list)
    """
    if not storage_list:
        raise ProviderListEmptyError
    if len(storage_list) <= 1:
        return storage_list[0]
    if len(size_list) + 1 != len(storage_list):
        raise ProviderSizeListMismatch
    storage_list.reverse()
    size_list.reverse()
    store = storage_list[0]
    for size, cache in zip(size_list, storage_list[1:]):
        store = LRUCache(cache, store, size)
    return store


def generate_chain(
    base_storage: StorageProvider,
    memory_cache_size: int,
    local_cache_size: int,
    path: str,
):
    """Internal function to be used by Dataset, to generate a cache_chain using a base_storage and sizes of memory and local caches.

    Args:
        base_storage (StorageProvider): The underlying actual storage of the Dataset.
        memory_cache_size (int): The size of the memory cache to be used in MB.
        local_cache_size (int): The size of the local filesystem cache to be used in MB.
        path (str): The location of the dataset.

    Returns:
        StorageProvider: Returns a cache containing the base_storage along with memory and local cache if a positive size has been specified for them.
    """
    dataset_id = str(uuid1())
    if path:
        dataset_name = path.split("/")[-1]
        dataset_id = f"{dataset_name}_{dataset_id}"
    storage_list: List[StorageProvider] = []
    size_list: List[int] = []
    if memory_cache_size > 0:
        storage_list.append(MemoryProvider(f"cache/{dataset_id}"))
        size_list.append(memory_cache_size * MB)
    if local_cache_size > 0:
        storage_list.append(LocalProvider(f"~/.activeloop/cache/{dataset_id}"))
        size_list.append(local_cache_size * MB)
    storage_list.append(base_storage)
    return get_cache_chain(storage_list, size_list)
