# -*- coding: utf-8 -*-
from django.db import models
from django.dispatch import Signal
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
import urllib, urllib2

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
        pass