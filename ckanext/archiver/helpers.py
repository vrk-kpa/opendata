from ckan.plugins import toolkit as tk


def archiver_resource_show(resource_id):
    data_dict = {'id': resource_id}
    return tk.get_action('archiver_resource_show')(data_dict)


def archiver_is_resource_broken_html(resource):
    archival = resource.get('archiver')
    if not archival:
        return tk.literal('<!-- No archival info for this resource -->')
    extra_vars = {'resource': resource}
    extra_vars.update(archival)
    return tk.literal(
        tk.render('archiver/is_resource_broken.html',
                  extra_vars=extra_vars))


def archiver_is_resource_cached_html(resource):
    archival = resource.get('archiver')
    if not archival:
        return tk.literal('<!-- No archival info for this resource -->')
    extra_vars = {'resource': resource}
    extra_vars.update(archival)
    return tk.literal(
        tk.render('archiver/is_resource_cached.html',
                  extra_vars=extra_vars))


# Replacement for the core ckan helper 'format_resource_items'
# but with our own blacklist
def archiver_format_resource_items(items):
    blacklist = ['archiver', 'qa']
    items_ = [item for item in items
              if item[0] not in blacklist]
    import ckan.lib.helpers as ckan_helpers
    return ckan_helpers.format_resource_items(items_)
