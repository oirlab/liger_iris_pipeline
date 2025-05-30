"""
This module supports the entry points for ASDF support for the `liger_iris_pipeline.datamodels`.
"""

import importlib.resources


from asdf.resource import DirectoryResourceMapping
from liger_iris_pipeline import datamodels


def get_resource_mappings():
    """
    Get the `liger_iris_pipeline.datamodels` resource mappings, that is the schemas for the datamodels.

    This method is registered with the `asdf.resource_mappings` entry point for
    the `liger_iris_pipeline.datamodels`.

    Returns
    -------
    list of the `asdf.resource.ResourceMapping` instances containing the `liger_iris_pipeline.datamodels`
    schemas.
    """
    resources_root = importlib.resources.files(datamodels)
    if not resources_root.is_dir():
        raise RuntimeError(f"Missing resources directory: {resources_root=}")
    return [
        DirectoryResourceMapping(
            resources_root / "schemas",
            "https://oirlab.github.io/schemas/",
        )
    ]
