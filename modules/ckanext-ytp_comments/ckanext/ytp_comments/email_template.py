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

Avoindata.fi support
avoindata@vrk.fi
""")
