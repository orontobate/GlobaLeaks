# -*- coding: utf-8
#   API
#   ***
#
#   This file defines the URI mapping for the GlobaLeaks API and its factory

import json
import re
import types
import urlparse

from twisted.internet import defer
from twisted.internet.abstract import isIPAddress, isIPv6Address
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.handlers import custodian, \
                                exception, \
                                file, \
                                receiver, \
                                public, \
                                submission, \
                                rtip, wbtip, \
                                attachment, authentication, token, \
                                export, l10n, wizard, \
                                base, user, shorturl, \
                                robots, \
                                staticfile

from globaleaks.handlers.admin import config as admin_config
from globaleaks.handlers.admin import context as admin_context
from globaleaks.handlers.admin import field as admin_field
from globaleaks.handlers.admin import file as admin_file
from globaleaks.handlers.admin import https
from globaleaks.handlers.admin import l10n as admin_l10n
from globaleaks.handlers.admin import manifest as admin_manifest
from globaleaks.handlers.admin import modelimgs as admin_modelimgs
from globaleaks.handlers.admin import node as admin_node
from globaleaks.handlers.admin import notification as admin_notification
from globaleaks.handlers.admin import overview as admin_overview
from globaleaks.handlers.admin import questionnaire as admin_questionnaire
from globaleaks.handlers.admin import receiver as admin_receiver
from globaleaks.handlers.admin import shorturl as admin_shorturl
from globaleaks.handlers.admin import statistics as admin_statistics
from globaleaks.handlers.admin import step as admin_step
from globaleaks.handlers.admin import tenant as admin_tenant
from globaleaks.handlers.admin import user as admin_user
from globaleaks.rest import apicache, requests, errors
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils.mailutils import extract_exception_traceback_and_schedule_email


uuid_regexp = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
key_regexp = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}|[a-z_]{0,100})'

api_spec = [
    (r'/exception', exception.ExceptionHandler),

    ## Authentication Handlers ##
    (r'/authentication', authentication.AuthenticationHandler),
    (r'/receiptauth', authentication.ReceiptAuthHandler),
    (r'/session', authentication.SessionHandler),

    ## Public API ##
    (r'/public', public.PublicResource),

    # User Preferences Handler
    (r'/preferences', user.UserInstance),

    ## Token Handlers ##
    (r'/token', token.TokenCreate),
    (r'/token/' + requests.token_regexp, token.TokenInstance),

    # Shorturl Handler
    (requests.shorturl_regexp, shorturl.ShortUrlInstance),

    ## Submission Handlers ##
    (r'/submission/' + requests.token_regexp, submission.SubmissionInstance),
    (r'/submission/' + requests.token_regexp + r'/file', attachment.SubmissionAttachment),

    ## Receiver Tip Handlers ##
    (r'/rtip/' + uuid_regexp, rtip.RTipInstance),
    (r'/rtip/' + uuid_regexp + r'/comments', rtip.RTipCommentCollection),
    (r'/rtip/' + uuid_regexp + r'/messages', rtip.ReceiverMsgCollection),
    (r'/rtip/' + uuid_regexp + r'/identityaccessrequests', rtip.IdentityAccessRequestsCollection),
    (r'/rtip/' + uuid_regexp + r'/export', export.ExportHandler),
    (r'/rtip/' + uuid_regexp + r'/wbfile', rtip.WhistleblowerFileHandler),
    (r'/rtip/rfile/' + uuid_regexp, rtip.ReceiverFileDownload),
    (r'/rtip/wbfile/' + uuid_regexp, rtip.RTipWBFileHandler),

    ## Whistleblower Tip Handlers
    (r'/wbtip', wbtip.WBTipInstance),
    (r'/wbtip/comments', wbtip.WBTipCommentCollection),
    (r'/wbtip/messages/' + uuid_regexp, wbtip.WBTipMessageCollection),
    (r'/wbtip/rfile', attachment.PostSubmissionAttachment),
    (r'/wbtip/wbfile/' + uuid_regexp, wbtip.WBTipWBFileHandler),
    (r'/wbtip/' + uuid_regexp + r'/provideidentityinformation', wbtip.WBTipIdentityHandler),

    ## Receiver Handlers ##
    (r'/receiver/preferences', receiver.ReceiverInstance),
    (r'/receiver/tips', receiver.TipsCollection),
    (r'/rtip/operations', receiver.TipsOperations),

    (r'/custodian/identityaccessrequests', custodian.IdentityAccessRequestsCollection),
    (r'/custodian/identityaccessrequest/' + uuid_regexp, custodian.IdentityAccessRequestInstance),

    ## Admin Handlers ##
    (r'/admin/node', admin_node.NodeInstance),
    (r'/admin/users', admin_user.UsersCollection),
    (r'/admin/users/' + uuid_regexp, admin_user.UserInstance),
    (r'/admin/contexts', admin_context.ContextsCollection),
    (r'/admin/contexts/' + uuid_regexp, admin_context.ContextInstance),
    (r'/admin/(users|contexts)/' + uuid_regexp  + r'/img', admin_modelimgs.ModelImgInstance),
    (r'/admin/questionnaires', admin_questionnaire.QuestionnairesCollection),
    (r'/admin/questionnaires/' + key_regexp, admin_questionnaire.QuestionnaireInstance),
    (r'/admin/receivers', admin_receiver.ReceiversCollection),
    (r'/admin/receivers/' + uuid_regexp, admin_receiver.ReceiverInstance),
    (r'/admin/notification', admin_notification.NotificationInstance),
    (r'/admin/notification/mail', admin_notification.NotificationTestInstance),
    (r'/admin/fields', admin_field.FieldsCollection),
    (r'/admin/fields/' + key_regexp, admin_field.FieldInstance),
    (r'/admin/steps', admin_step.StepCollection),
    (r'/admin/steps/' + uuid_regexp, admin_step.StepInstance),
    (r'/admin/fieldtemplates', admin_field.FieldTemplatesCollection),
    (r'/admin/fieldtemplates/' + key_regexp, admin_field.FieldTemplateInstance),
    (r'/admin/shorturls', admin_shorturl.ShortURLCollection),
    (r'/admin/shorturls/' + uuid_regexp, admin_shorturl.ShortURLInstance),
    (r'/admin/stats/(\d+)', admin_statistics.StatsCollection),
    (r'/admin/activities/(summary|details)', admin_statistics.RecentEventsCollection),
    (r'/admin/anomalies', admin_statistics.AnomalyCollection),
    (r'/admin/jobs', admin_statistics.JobsTiming),
    (r'/admin/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ')', admin_l10n.AdminL10NHandler),
    (r'/admin/files/(logo|favicon|css|homepage|script)', admin_file.FileInstance),
    (r'/admin/config', admin_config.AdminConfigHandler),
    (r'/admin/config/tls', https.ConfigHandler),
    (r'/admin/config/tls/files/(csr)', https.CSRFileHandler),
    (r'/admin/config/tls/files/(cert|chain|priv_key)', https.FileHandler),
    (r'/admin/files$', admin_file.FileCollection),
    (r'/admin/files/(.+)', admin_file.FileInstance),
    (r'/admin/tenants', admin_tenant.TenantCollection),
    (r'/admin/tenants/' + '([0-9]{1,20})', admin_tenant.TenantInstance),
    (r'/admin/overview/tips', admin_overview.Tips),
    (r'/admin/overview/files', admin_overview.Files),
    (r'/admin/manifest', admin_manifest.ManifestHandler),
    (r'/wizard', wizard.Wizard),

    (r'/admin/config/acme/run', https.AcmeHandler),
    (r'/.well-known/acme-challenge/([a-zA-Z0-9_\-]{42,44})', https.AcmeChallengeHandler),

    ## Special Files Handlers##
    (r'/robots.txt', robots.RobotstxtHandler),
    (r'/sitemap.xml', robots.SitemapHandler),
    (r'/s/(.+)', file.FileHandler),
    (r'/l10n/(' + '|'.join(LANGUAGES_SUPPORTED_CODES) + ')', l10n.L10NHandler),

    ## This handler attempts to route all non routed get requests
    (r'/([a-zA-Z0-9_\-\/\.]*)', staticfile.StaticFileHandler, {'path': Settings.client_path})
]


def decorate_method(h, method):
    value = getattr(h, 'check_roles')
    if isinstance(value, str):
        value = {value}

    f = getattr(h, method)

    if State.settings.enable_api_cache:
        if method == 'get':
            if h.cache_resource:
                f = apicache.decorator_cache_get(f)

        else:
            if h.invalidate_global_cache or h.invalidate_cache:
                f = apicache.decorator_cache_invalidate(f)

            if h.invalidate_tenant_states:
               f = getattr(h, 'decorator_invalidate_tenant_states')(f)

    f = getattr(h, 'decorator_authentication')(f, value)

    setattr(h, method, f)


class APIResourceWrapper(Resource):
    _registry = None
    isLeaf = True
    method_map = {'get': 200, 'post': 201, 'put': 202, 'delete': 200}

    def __init__(self):
        Resource.__init__(self)
        self._registry = []
        self.handler = None

        for tup in api_spec:
            args = {}
            if len(tup) == 2:
                pattern, handler = tup
            else:
                pattern, handler, args = tup

            if not pattern.startswith("^"):
                pattern = "^" + pattern

            if not pattern.endswith("$"):
                pattern += "$"

            if not hasattr(handler, '_decorated'):
                handler._decorated = True
                for m in ['get', 'put', 'post', 'delete']:
                    if hasattr(handler, m):
                        decorate_method(handler, m)

            self._registry.append((re.compile(pattern), handler, args))

    def should_redirect_tor(self, request):
        if request.client_using_tor and \
            request.hostname not in ['127.0.0.1'] + State.tenant_cache[request.tid].onionnames:
            return True

        return False

    def should_redirect_https(self, request):
        if State.tenant_cache[request.tid].private.https_enabled and \
           request.client_proto == 'http' and \
           request.client_ip not in Settings.local_hosts:
            return True

        return False

    def redirect(self, request, url):
        request.setResponseCode(301)
        request.setHeader(b"location", url)

    def redirect_https(self, request):
        _, _, path, query, frag = urlparse.urlsplit(request.uri)
        redirect_url = urlparse.urlunsplit(('https', State.tenant_cache[request.tid].hostname, path, query, frag))
        self.redirect(request, redirect_url)

    def redirect_tor(self, request):
        _, _, path, query, frag = urlparse.urlsplit(request.uri)
        redirect_url = urlparse.urlunsplit(('http', State.tenant_cache[request.tid].onionservice, path, query, frag))
        self.redirect(request, redirect_url)

    def handle_exception(self, e, request):
        """
        handle_exception is a callback that decorators all deferreds in render

        It responds to properly handled GL Exceptions by pushing the error msgs
        to the client and it spools a mail in the case the exception is unknown
        and unhandled.

        @param e: A `Twisted.python.Failure` instance that wraps a `GLException`
                  or a normal `Exception`
        @param request: The `twisted.web.Request`
        """
        if isinstance(e, errors.GLException):
            pass
        elif isinstance(e.value, errors.GLException):
            e = e.value
        else:
            extract_exception_traceback_and_schedule_email(e)
            e = errors.InternalServerError('Unexpected')

        request.setResponseCode(e.status_code)
        request.setHeader(b'content-type', b'application/json')

        response = json.dumps({
            'error_message': e.reason,
            'error_code': e.error_code,
            'arguments': getattr(e, 'arguments', [])
        })

        request.write(bytes(response))

    def preprocess(self, request):
        request.headers = request.getAllHeaders()

        request.hostname = request.getRequestHostname().split(':')[0]
        request.port = request.getHost().port

        if (request.hostname == 'localhost' or
            isIPAddress(request.hostname) or
            isIPv6Address(request.hostname)):
            request.tid = 1
        else:
            request.tid = State.tenant_hostname_id_map.get(request.hostname)

        request.client_ip = request.headers.get('gl-forwarded-for')
        request.client_proto = 'https'
        if request.client_ip is None:
            request.client_ip = request.getClientIP()
            request.client_proto = 'http'

        request.client_using_tor = request.client_ip in State.tor_exit_set or \
                                   request.port == 8083


        if 'x-tor2web' in request.headers:
            request.client_using_tor = False

        request.language = unicode(self.detect_language(request))
        if 'multilang' in request.args:
            request.language = None

    def render(self, request):
        """
        @param request: `twisted.web.Request`

        @return: empty `str` or `NOT_DONE_YET`
        """
        request_finished = [False]

        def _finish(ret):
            request_finished[0] = True

        request.notifyFinish().addBoth(_finish)

        self.preprocess(request)

        self.set_headers(request)

        if request.tid is None:
            self.handle_exception(errors.ResourceNotFound(), request)
            return b''

        if self.should_redirect_tor(request):
            self.redirect_tor(request)
            return b''

        if self.should_redirect_https(request):
            self.redirect_https(request)
            return b''

        match = None
        for regexp, handler, args in self._registry:
            match = regexp.match(request.path)
            if match:
                break

        if match is None:
            self.handle_exception(errors.ResourceNotFound(), request)
            return b''

        method = request.method.lower()
        if not method in self.method_map or not hasattr(handler, method):
            self.handle_exception(errors.MethodNotImplemented(), request)
            return b''

        f = getattr(handler, method)
        groups = [unicode(g) for g in match.groups()]

        self.handler = handler(State, request, **args)

        request.setResponseCode(self.method_map[method])

        if self.handler.root_tenant_only and request.tid != 1:
            self.handle_exception(errors.ForbiddenOperation(), request)
            return b''

        if self.handler.upload_handler and method == 'post':
            self.handler.process_file_upload()
            if self.handler.uploaded_file is None:
               return

        d = defer.maybeDeferred(f, self.handler, *groups)

        @defer.inlineCallbacks
        def concludeHandlerFailure(err):
            yield self.handler.execution_check()

            self.handle_exception(err, request)

            if not request_finished[0]:
                request.finish()

        @defer.inlineCallbacks
        def concludeHandlerSuccess(ret):
            """
            Concludes successful execution of a `BaseHandler` instance

            @param ret: A `dict`, `list`, `str`, `None` or something unexpected
            """
            yield self.handler.execution_check()

            if not request_finished[0]:
                if ret is not None:
                   if isinstance(ret, (types.DictType, types.ListType)):
                       ret = json.dumps(ret, separators=(',', ':'))
                       request.setHeader(b'content-type', b'application/json')

                   request.write(bytes(ret))

                request.finish()

        d.addErrback(concludeHandlerFailure)
        d.addCallback(concludeHandlerSuccess)

        return NOT_DONE_YET

    def set_headers(self, request):
        # to avoid version attacks

        request.setHeader("Server", "Globaleaks")

        request.setHeader('Content-Language', request.language)

        # to reduce possibility for XSS attacks.
        request.setHeader("X-Content-Type-Options", "nosniff")
        request.setHeader("X-XSS-Protection", "1; mode=block")

        # to disable caching
        request.setHeader("Cache-control", "no-cache, no-store, must-revalidate")
        request.setHeader("Pragma", "no-cache")
        request.setHeader("Expires", "-1")

        # to avoid information leakage via referrer
        request.setHeader("Referrer-Policy", "no-referrer")

        # to avoid Robots spidering, indexing, caching
        if not State.tenant_cache[1].allow_indexing:
            request.setHeader("X-Robots-Tag", "noindex")

        # to mitigate clickjaking attacks on iframes allowing only same origin
        # same origin is needed in order to include svg and other html <object>
        if not State.tenant_cache[1].allow_iframes_inclusion:
            request.setHeader("X-Frame-Options", "sameorigin")

        request.setHeader(b'x-check-tor', bytes(request.client_using_tor))


    def parse_accept_language_header(self, request):
        if "accept-language" in request.headers:
            languages = request.headers["accept-language"].split(",")
            locales = []
            for language in languages:
                parts = language.strip().split(";")
                if len(parts) > 1 and parts[1].startswith("q="):
                    try:
                        score = float(parts[1][2:])
                    except (ValueError, TypeError):
                        score = 0.0
                else:
                    score = 1.0
                locales.append((parts[0], score))

            if locales:
                locales.sort(key=lambda pair: pair[1], reverse=True)
                return [l[0] for l in locales]

        return State.tenant_cache[1].default_language

    def detect_language(self, request):
        language = request.headers.get('gl-language')
        if language is None:
            for l in self.parse_accept_language_header(request):
                if l in State.tenant_cache[1].languages_enabled:
                    language = l
                    break

        if language is None or language not in State.tenant_cache[1].languages_enabled:
            language = State.tenant_cache[1].default_language

        return language
