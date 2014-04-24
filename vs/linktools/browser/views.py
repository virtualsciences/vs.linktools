import re

from zope.component import getUtility
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.redirector.interfaces import IRedirectionStorage

from pareto.plonehtml import plonehtml
from pareto.uidfixer import uidfixer
from pareto.deadfiles import deadfiles


class LinkTools(BrowserView):
    template = ViewPageTemplateFile('linktools.pt')
    results_template = ViewPageTemplateFile('linktools-results.pt')

    def __call__(self):
        portal = getToolByName(self.context, "portal_url").getPortalObject()
        redirector = self.redirector = getUtility(IRedirectionStorage)
        self.uidfixer = uidfixer.UIDFixer(
            redirector, portal, ['www.knmp.nl', 'edit.knmp.nl', 'knmp.nl'])
        if self.request.get('remove-submit'):
            toremove = self.request['remove']
            for path in toremove:
                path = path.split('/')
                parent = self.context.restrictedTraverse(path[:-1])
                parent.manage_delObjects([path[-1]])
        elif not self.request.get('submit'):
            return self.template()
        return self.results_template()

    def results(self):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        processor = plonehtml.PloneHtmlProcessor(
            self._handler, self.request.get('dry'))
        data = {
            'uidfixer_results': [],
            'dead_links': [],
            'dead_files': [],
        }
        linkuids = []
        for context, field, results in processor.process(self.context):
            linkuids += results['linkuids']
            data['uidfixer_results'] += [{
                'object': context,
                'field': field,
                'href': href,
                'resolved': not not uid,
                'resolved_url': self._url_by_uid(uid, href),
            } for (href, uid) in results['uidfixer_results']]
            data['dead_links'] += [{
                'object': context,
                'field': field,
                'href': href,
            } for href in results['dead_links']]

        # so now we know all UIDs that have a link to them, let's walk through
        # all files to see if their UID is in there and if not report them
        # as dead
        catalog = getToolByName(self.context, 'portal_catalog')
        items = catalog(portal_type=('File',))
        data['total_files'] = len(items)
        dead_instances = deadfiles.find_dead_files(
            self.context, linkuids, ('File',), self.redirector)
        data['dead_files'] = [{
            'uid': instance.UID(),
            'url': instance.absolute_url(),
            'path': '/'.join(instance.getPhysicalPath()),
        } for instance in dead_instances]

        data['linkuids'] = linkuids
        return data

    _reg_uid_href = re.compile('href="resolveuid/([^"\/?#]+)')
    def _handler(self, html, context):
        """ this converts links to resolveuid and reports dead links and files

            this basically combines pareto.uidfixer and pareto.deadfiles,
            with an added bonus that it reports dead links (all of them,
            not just the fixed ones like uidfixer does), and it's all
            done in a single pass
        """
        ret = {}

        # fix resolveuid links where possible
        html, ufresults = self.uidfixer.replace_uids(html, context)
        ret['uidfixer_results'] = ufresults

        # results is now a list of tuples (href, uid) where uid is only
        # provided if the href was fixed
        fixeduids = [uid for (href, uid) in ufresults if uid]
        deadhrefs = [href for (href, uid) in ufresults if not uid]

        ret['dead_links'] = deadhrefs

        # now that we're pretty sure all internal links are proper resolveuid
        # ones, verify all resolveuid links' UIDs (including those just
        # generated, but doesn't matter) and store for determining whether
        # we have dead files later
        uids = ret['linkuids'] = deadfiles.find_uids(html, context)
        for uid in uids:
            if not self.uidfixer.verify_uid(uid, context):
                deadhrefs.append('resolveuid/%s' % (uid,))

        # report fix information, dead and working uids
        return html, [ret], not not fixeduids

    def _url_by_uid(self, uid, href):
        portal_catalog = self.context.portal_catalog
        if not uid:
            return ''
        brains = portal_catalog(UID=uid)
        return brains[0].getObject().absolute_url()
