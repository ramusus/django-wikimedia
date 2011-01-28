# -*- coding: utf-8 -*-
from django.db import models
from django.dispatch import Signal
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from BeautifulSoup import BeautifulSoup, Comment
import urllib, urllib2
import re

LANGUAGES = getattr(settings, 'WIKIPEDIA_LANGUAGES', [('en', _('English'))])

wikipedia_updated = Signal(providing_args=['instance','created'])

class WikipediaManager(models.Manager):
    '''
    Wikipedia manager
    '''
    _headers = {
        'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.1.8) Gecko/20100214 Linux Mint/8 (Helena) Firefox/3.5.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ru,en-us;q=0.7,en;q=0.3',
        'Accept-Encoding': 'deflate',
        'Accept-Charset': 'utf-8;q=0.7,*;q=0.7',
        'Keep-Alive': '300',
        'Connection': 'keep-alive',
        'Referer': 'http://wikipedia.org/',
        'Cookie': 'users_info[check_sh_bool]=none; search_last_date=2010-02-19; search_last_month=2010-02;                                        PHPSESSID=b6df76a958983da150476d9cfa0aab18',
    }

    def update(self, object, lang, title):

        if len(lang) != 2:
            raise ValueError('Attribute lang must be 2 symbols length')

        if lang not in [l[0] for l in LANGUAGES]:
            raise ValueError('Attribute lang not in allowed settings.WIKIPEDIA_LANGUAGES')

        content = self._get_content(lang, title)

        element, created = self.get_or_create(object_id=object.id, content_type=ContentType.objects.get_for_model(object), lang=lang, title=title)
        element.content = content
        element.content_object = object
        element.save()
        return element

    def _get_content(self, lang, title):
        self._url = 'http://%s.wikipedia.org/w/index.php' % lang
        self._params = {
            'title': title,
            'action': 'render',
        }
        self._params = dict([(key, unicode(val).encode('windows-1251', 'ignore')) for key, val in self._params.items()])

        response = urllib2.urlopen(self._get_request())
        return response.read()

    def _get_url(self):
        url = self._url
        if self._params:
            url += '?' + urllib.urlencode(self._params)
        return url

    def _get_request(self):
        return urllib2.Request(url=self._get_url(), headers=self._headers)

class WikipediaElement(models.Model):
    '''
    Wikipedia page model
    '''
    class Meta:
        unique_together = ('object_id', 'content_type', 'lang', 'title')
        ordering = ('-updated',)

    class Remove:
        edit_links = True
        contents = True
        comments = True
        external_links = True
        infobox = True
        sisterproject = True
        navbox = True
        disambiguation = True

    lang = models.CharField(_('Language'), max_length=2, choices=LANGUAGES)
    title = models.CharField(_('Title'), max_length=300)
    content = models.TextField(_('Content'))
    updated = models.DateTimeField(_('Date and time of last updating'), editable=False, auto_now=True)

    objects = WikipediaManager()

    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)
    content_object = generic.GenericForeignKey()

    def save(self, *args, **kwargs):
        '''
        Prepare wikipedia content, send signal after saving
        '''
        id = self.id
        self.process_content()
        super(WikipediaElement, self).save(*args, **kwargs)
        wikipedia_updated.send(sender=WikipediaElement, instance=self, created=bool(id))

    def process_content(self):
        '''
        Process wikipedia content before saving to DB
        '''
        self.content = BeautifulSoup(self.content)

        self.parse_content()
        self.remove_garbage()

        self.content = unicode(self.content)

    def parse_content(self):
        '''
        Parse wikipedia content page for useful information
        '''
        pass

    def remove_garbage(self):
        '''
        Remove unnecessary tags from wikipedia content page
        '''
        # span editsection
        if self.Remove.edit_links:
            [el.extract() for el in self.content.findAll('span', {'class': 'editsection'})]

        # table contents
        if self.Remove.contents:
            [el.extract() for el in self.content.findAll('table', {'id': 'toc', 'class': 'toc'})]

        # remove all comments
        if self.Remove.comments:
            [el.extract() for el in self.content.findAll(text=lambda text:isinstance(text, Comment))]

        # external links block (ru,en)
        if self.Remove.external_links:
            links_title = self.content.find(text=re.compile(u'(Ссылки|links)'))
            if links_title:
                # get h2
                links_title = links_title.parent.parent
                links = links_title.findNextSibling('ul')
                if links:
                    links_title.extract()
                    links.extract()

        table_classes = []
        div_classes = []

        if self.Remove.infobox:
            table_classes += ['infobox'] # table infobox
            div_classes += ['infobox'] # div infobox

        if self.Remove.sisterproject:
            # links to another wikimedia (en) table class="metadata mbox-small plainlinks"
            table_classes += ['metadata']
            # links to another wikimedia (ru) div class="infobox sisterproject noprint wikiquote-box"
            div_classes += ['sisterproject','wikiquote-box']

        if self.Remove.navbox:
            # links to another movies of director table class="navbox collapsible autocollapse nowraplinks"
            table_classes += ['navbox','NavFrame']

        if self.Remove.disambiguation:
            # disambiguation div class="dablink"
            div_classes += ['dablink']

        [el.extract() for el in self.content.findAll('table', {'class': re.compile('(%s)' % '|'.join(table_classes))})]
        [el.extract() for el in self.content.findAll('div', {'class': re.compile('(%s)' % '|'.join(div_classes))})]