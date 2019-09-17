from amicleaner.cli import App as Cleaner
from amicleaner.utils import parse_args

class ImageCleaner:

    def __init__(self, cleaner_params):

        self.cleaner = Cleaner(parse_args([
            '--ami-min-days', cleaner_params["min_days"],
            '--mapping-key', cleaner_params["mapping_key"],
            '--mapping-values', cleaner_params["mapping_values"]
        ]))

    def clean_images(self):

        images = self.cleaner.prepare_candidates()
        if images:
            self.cleaner.prepare_delete_amis(images)
