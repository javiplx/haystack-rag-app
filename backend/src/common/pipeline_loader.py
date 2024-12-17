import os
import logging

from haystack import Pipeline


logger = logging.getLogger(__name__)

def load_pipeline(pipelines_dir, filename):
    if not pipelines_dir or not filename:
        return None

    p = Pipeline()
    yaml_path = os.path.join(pipelines_dir, filename)

    try:
        with open(yaml_path, "rb") as f:
            logger.info(f"Loading pipeline definition from {yaml_path}")
            return p.load(f)
    except FileNotFoundError:
        logger.warning(f"Pipeline definition not found: {yaml_path}")
    return None
