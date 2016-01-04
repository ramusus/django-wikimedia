# -*- coding: utf-8 -*-
from importlib import import_module

from django.db import models
from django.conf import settings
from django.utils.translation import get_language, ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from utils import url_fix
import urllib2

try:
    # Django 1.9
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.generic import GenericForeignKey


__all__ = ['WikipageTitleError', 'WikipageManager', 'Wikipage', 'Wikiproject']

LANGUAGES = getattr(settings, 'WIKIMEDIA_LANGUAGES', [('en', _('English'))])


def get_parser():
    from django.conf import settings
    try:
        parser = getattr(settings, 'WIKIMEDIA_PARSER', 'wikimedia.parsers.WikipageParserBeautifulsoup')
        parser_path = parser.split('.')
        parser_module = import_module('.'.join(parser_path[:-1]))
        WikipageParser = getattr(parser_module, parser_path[-1])
    except ImportError, e:
        raise ImproperlyConfigured('Error importing wikipage parsing module %s: "%s"' % (parser, e))

    return WikipageParser()


class WikipageTitleError(ValueError):
    pass


class WikipageManager(models.Manager):

    '''
    Wikipage manager
    '''

    def __getattr__(self, name):
        '''
        Method allow return wikimedia content in the following format:
            object.wikimedia.wikipedia,
            object.wikimedia.wikipedia_en,
            object.wikimedia.wikiquote,
            object.wikimedia.wikiquote_ru,
            ...
        Attribute without language returns with respect to current language
        '''
        if name.find('_') == -1:
            project_code = name
            lang = get_language()
        else:
            project_code = '_'.join(name.split('_')[:-1])
            lang = name.split('_')[-1]

        # check if project_code and lang valid
        try:
            lang = self.get_language(lang)
            project = self.get_project(project_code)
        except:
            raise AttributeError("'WikimediaManager' object has no attribute '%s'" % name)

        try:
            return self.filter(project__code=project_code, lang=lang)[0].content
        except:
            return ''

    def update(self, title, lang, project_code='wikipedia', object=None, with_sister_projects=False):
        '''
        Method for update wikipage with specified title, lang for object
        Allows chaining updates with with_sister_projects=True
        '''
        lang = self.get_language(lang)
        project = self.get_project(project_code)

        try:
            if object:
                filter_delete_dict = dict(
                    object_id=object.id, content_type=ContentType.objects.get_for_model(object), lang=lang)
                page = self.get_or_create(project=project, lang=lang, title=title,
                                          object_id=object.id, content_type=ContentType.objects.get_for_model(object))[0]
            else:
                page = self.get_or_create(project=project, lang=lang, title=title)[0]

        except urllib2.HTTPError:
            raise WikipageTitleError('Incorrect %s title (%s) with lang "%s"' %
                                     (project_code, title.encode('utf-8'), lang))

        # update all found sister projects
        if with_sister_projects:

            # delete all others wikimedia pages for this object (every projects)
            if object:
                self.filter(**filter_delete_dict).exclude(id=page.id).delete()

            for project_code, title in page.sister_projects:
                try:
                    self.update(title, lang, project_code, object)
                except WikipageTitleError:
                    continue

        elif object:
            # if updating without sister projects => removing only existed pages of current project
            self.filter(project=project, **filter_delete_dict).exclude(id=page.id).delete()

        return page

    def get_language(self, lang):
        '''
        Validate if lang is correct and return value back
        '''
        if len(lang) != 2:
            raise ValueError('Attribute lang must be 2 symbols length')

        if lang not in [l[0] for l in LANGUAGES]:
            raise ValueError('Attribute lang not in allowed settings.WIKIPEDIA_LANGUAGES')

        return lang

    def get_project(self, project_code):
        '''
        Get project by code and return instance
        '''
        try:
            return Wikiproject.objects.get(code=project_code)
        except:
            raise ValueError('There is no wikiproject for updating with code "%s"' % project_code)


class Wikiproject(models.Model):

    '''
    Wikiproject model for wikimedia sisters projects or other sites based on wikimedia engines
    '''
    code = models.CharField(_('Name'), max_length=20, primary_key=True)
    domain = models.CharField(_('Domain'), max_length=50)
    subdomain_lang = models.BooleanField(_('Language subdomain'), default=False)

    def get_domain(self, lang):
        return '%s.%s' % (lang, self.domain) if self.subdomain_lang else self.domain

    def __unicode__(self):
        return '<Wikiproject: %s>' % self.code


class Wikipage(models.Model):

    '''
    Wikipedia page model
    # TODO: move Remove class to external entity with ability to connect it for different sites
    '''
    lang = models.CharField(_('Language'), max_length=2, choices=LANGUAGES, db_index=True)
    project = models.ForeignKey(Wikiproject)
    title = models.CharField(_('Title'), max_length=300, db_index=True)
    content = models.TextField(_('Content'))
    updated = models.DateTimeField(_('Date and time of last updating'), editable=False, auto_now=True, db_index=True)

    object_id = models.PositiveIntegerField(null=True)
    content_type = models.ForeignKey(ContentType, null=True, related_name='wikipages')
    content_object = GenericForeignKey()

    sister_projects = []

    objects = WikipageManager()

    class Meta:
        unique_together = ('lang', 'project', 'title')
        ordering = ('-updated',)
        get_latest_by = 'updated'

    def save(self, *args, **kwargs):
        '''
        Process wikipedia content before saving
        '''
        id = self.id
        self.set_content()

        if self.content:
            parser = get_parser()
            self.content = parser.process_content(self.content, self)

        super(Wikipage, self).save(*args, **kwargs)

    def set_content(self):
        '''
        Get page content for current project and defina self.content model attribute
        '''
        request = self._get_request()

        response = urllib2.urlopen(request)
        self.content = response.read()

    def get_domain(self):
        return self.project.get_domain(self.lang)

    def get_url(self):
        params = {
            'title': self.title,
            'action': 'render',
        }

        if not self.project.subdomain_lang:
            params['uselang'] = self.lang

        url = 'http://%s/w/index.php' % self.get_domain()
        url += '?' + '&'.join(['%s=%s' % (key, val) for key, val in params.items()])
        url = url_fix(url)
        return url

    def _get_request(self):

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.1.8) Gecko/20100214 Linux Mint/8 (Helena) Firefox/3.5.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru,en-us;q=0.7,en;q=0.3',
            'Accept-Encoding': 'deflate',
            'Accept-Charset': 'utf-8;q=0.7,*;q=0.7',
            'Keep-Alive': '300',
            'Connection': 'keep-alive',
            'Referer': 'http://%s/' % self.get_domain(),
            'Cookie': 'users_info[check_sh_bool]=none; search_last_date=2010-02-19; search_last_month=2010-02; PHPSESSID=b6df76a958983da150476d9cfa0aab18',
        }

        return urllib2.Request(url=self.get_url(), headers=headers)
