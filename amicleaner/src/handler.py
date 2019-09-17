from os import environ
from cleaner import ImageCleaner

def handle(event, context):
    
    # Define minimum days to keep images and
    # mapping key and value to use for selecting images

    cleaner_params = {
      "min_days": environ["MIN_DAYS"],
      "mapping_key": environ["MAPPING_KEY"],
      "mapping_values": environ["MAPPING_VALUES"]
    }

    ImageCleaner(cleaner_params).clean_images()
