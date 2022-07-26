import ckan.model as model
from ckan.plugins import toolkit as tk

c = tk.c
get_action = tk.get_action


def get_featured_showcases():
    context = {'model': model, 'user': c.user, 'auth_user_obj': c.userobj}
    limit = 4

    data_dict = {
        'fq': 'featured:true +dataset_type:showcase',
        'rows': limit,
        'start': 0,
        'sort': 'metadata_created desc',
        'include_private': False
    }

    query = get_action('package_search')(context, data_dict)

    results = []
    for item in query['results']:
        results.append(get_action('package_show')(context, {'id': item['id']}))

    return results


def get_showcases_by_author(author, limit, exclude_id):
    context = {'model': model, 'user': c.user, 'auth_user_obj': c.userobj}
    fq = ''
    fq += u'author:{author_name}'.format(author_name=author.replace(' ', r'\ '))
    fq += ' -id:{exclude_id}'.format(exclude_id=exclude_id)
    fq += ' +dataset_type:showcase'

    data_dict = {
        'fq': fq,
        'rows': limit,
        'start': 0,
        'sort': 'metadata_created desc',
        'include_private': False
    }

    query = get_action('package_search')(context, data_dict)

    return query['results']


def get_vocabulary(vocab_id):
    context = {'model': model, 'user': c.user, 'auth_user_obj': c.userobj}

    data_dict = {
        'id': vocab_id
    }

    results = get_action('vocabulary_show')(context, data_dict)

    return results


def translate_list_items(old_list):
    translated_list = []
    for item in old_list:
        translated_list.append(tk._(item))
    return translated_list


def get_showcase_pkgs(showcase_id):

    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj}

    showcase_pkgs = get_action('ckanext_showcase_package_list')(
        context, {'showcase_id': showcase_id})

    return showcase_pkgs
