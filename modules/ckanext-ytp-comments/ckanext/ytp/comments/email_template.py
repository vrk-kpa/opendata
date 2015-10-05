
"""
    A template file for comment notification emails.
"""

subject = "New comment in dataset '%(dataset)s'"

message = """\
User %(user)s (%(email)s) has left a comment in dataset (%(dataset)s):

--
Subject:
%(comment_subject)s

Message:
%(comment)s
--

%(link)s

Best regards

Avoindata.fi support
valtori@avoindata.fi
"""
