import logging
import sqlalchemy

_and_ = sqlalchemy.and_
_func = sqlalchemy.func
_text = sqlalchemy.text

log = logging.getLogger(__name__)


def get_formats(context, data_dict=None):
    model = context['model']
    session = context['session']

    query = (session.query(
        model.Resource.format,
        _func.count(model.Resource.format).label('total'))
        .filter(_and_(
            model.Resource.state == 'active',
        ))
        .filter(model.Resource.format != '')
        .group_by(model.Resource.format)
        .order_by(_text('total DESC'))
    )

    return [resource.format for resource in query]
