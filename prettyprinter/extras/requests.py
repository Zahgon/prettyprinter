from prettyprinter import pretty_call_alt, comment, register_pretty


MAX_CONTENT_CHARS = 500


def pretty_headers(headers, ctx):
    pass


def pretty_request(request, ctx):

    pass


def pretty_prepared_request(request, ctx):
    pass


def pretty_response(resp, ctx):
    pass


def pretty_session(session, ctx):
    pass


def install():
    register_pretty('requests.structures.CaseInsensitiveDict')(pretty_headers)
    register_pretty('requests.sessions.Session')(pretty_session)
    register_pretty('requests.models.Response')(pretty_response)
    register_pretty('requests.models.Request')(pretty_request)
    register_pretty('requests.models.PreparedRequest')(pretty_prepared_request)
