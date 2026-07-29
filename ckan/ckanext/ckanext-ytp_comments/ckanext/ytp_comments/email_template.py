from ckan.common import _

"""
    A template file for comment notification emails.
"""

subject = _("New comment in dataset '{dataset}'")

message = _("""\
User {user} ({email}) has left a comment in dataset ({dataset}):

--
Subject:
{comment_subject}

Message:
{comment}
--

{link}

Best regards

Suomi.fi Open Data support
avoindata@dvv.fi
""")
