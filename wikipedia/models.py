# -*- coding: utf-8 -*-
from django.db import models
from django.dispatch import Signal
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from BeautifulSoup import BeautifulSoup, Comment, NavigableString
from utils import url_fix
import urllib2
import re

LANGUAGES = getattr(settings, 'WIKIPEDIA_LANGUAGES', [('en', _('English'))])

wikipedia_updated = Signal(providing_args=['instance','created'])

class WikipediaTitleError(ValueError):
    pass

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

        try:
            content = self._get_content(lang, title)
        except urllib2.HTTPError:
            raise WikipediaTitleError('Attribute title point to incorrect wikipedia title')

        element, created = self.get_or_create(object_id=object.id, content_type=ContentType.objects.get_for_model(object), lang=lang, title=title, defaults={
            'content': content,
        })
        if not created:
            element.content = content
            element.save()

        # delete all other wikipedia elements for this object
        self.filter(object_id=object.id, content_type=ContentType.objects.get_for_model(object), lang=lang).exclude(id=element.id).delete()

        return element

    def _get_content(self, lang, title):
        self._url = 'http://%s.wikipedia.org/w/index.php' % lang
        self._params = {
            'title': title,
            'action': 'render',
        }
        response = urllib2.urlopen(self._get_request())
        return response.read()

    def _get_url(self):
        url = self._url
        if self._params:
            url += '?' + '&'.join(['%s=%s' % (key, val) for key, val in self._params.items()])
        url = url_fix(url)
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
        table_classes = []
        div_classes = []
        block_titles = []
        span_classes = []

        edit_links = True
        contents = True
        comments = True
        external_links = True
        infobox = True
        sisterproject = True
        navbox = True
        reference = True
        reference_links = True
        see_also = True
        style_attribute = True
        class_attribute = True
        script = True
        disambiguation = True
        thumb_images = True
        audio = True

        external_links_titles = [u'Ссылки','links']

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

    @property
    def remove(self):
        return self.Remove

    def process_content(self):
        '''
        Process wikipedia content before saving to DB
        '''
        self.content = BeautifulSoup(self.content)

        self.parse_content()
        self.remove_garbage()

        self.content = unicode(self.content).strip()

    def parse_content(self):
        '''
        Parse wikipedia content page for useful information
        '''
        pass

    def remove_garbage(self):
        '''
        Remove unnecessary tags from wikipedia content page
        '''
        table_classes = self.remove.table_classes
        div_classes = self.remove.div_classes
        span_classes = self.remove.span_classes

        # span editsection
        if self.remove.edit_links:
            [el.extract() for el in self.content.findAll('span', {'class': 'editsection'})]

        # table contents
        if self.remove.contents:
            [el.extract() for el in self.content.findAll('table', {'id': 'toc', 'class': 'toc'})]

        # scripts
        if self.remove.script:
            [el.extract() for el in self.content.findAll('script')]

        # remove all comments
        if self.remove.comments:
            [el.extract() for el in self.content.findAll(text=lambda text:isinstance(text, Comment))]

        # external links block (ru,en)
        if self.remove.external_links:
            self.remove.block_titles += self.remove.external_links_titles

        if self.remove.see_also:
            self.remove.block_titles += ['See also', u'Cм[^ ]+ также']

        if self.remove.reference_links:
            [el.extract() for el in self.content.findAll('sup', {'class': 'reference'})]

        if self.remove.reference:
            # references block (en) div class="reflist references-column-count references-column-count-2"
            div_classes += ['reflist','references-small']
            self.remove.block_titles += [u'Примечания','References',u'Источники',]

        infobox = self.content.find(True, {'class': re.compile('infobox')})
        if infobox:
            if self.remove.disambiguation:
                [el.extract() for el in infobox.findAllPrevious(True)]
            if self.remove.infobox:
                infobox.extract()
                # sometimes there is another infoboxes on page http://ru.wikipedia.org/wiki/Король_говорит!
                table_classes += ['infobox']
                div_classes += ['infobox']

        if self.remove.sisterproject:
            # links to another wikimedia (en) table class="metadata mbox-small plainlinks"
            table_classes += ['metadata']
            # links to another wikimedia (ru) div class="infobox sisterproject noprint wikiquote-box"
            div_classes += ['sisterproject','wikiquote-box']

        if self.remove.navbox:
            # links to another movies of director table class="navbox collapsible autocollapse nowraplinks"
            table_classes += ['navbox','NavFrame']
            # links to another cities of this region
            table_classes += ['toccolours']
            div_classes += ['navbox','NavFrame']

        if self.remove.disambiguation:
            # disambiguation div class="dablink" (en)
            div_classes += ['dablink']

        if self.remove.thumb_images:
            div_classes += ['thumb']

        if self.remove.audio:
            [el.findParent('table').extract() for el in self.content.findAll('div', {'id': 'ogg_player_1'})]
            span_classes += ['audiolink','audiolinkinfo']

        # lock icon (en) <div class="metadata topicon" id="protected-icon">
        [el.extract() for el in self.content.findAll('div', {'id': 'protected-icon'})]
        div_classes += ['metadata']

        [el.extract() for el in self.content.findAll('table', {'class': re.compile('(%s)' % '|'.join(table_classes))})]
        [el.extract() for el in self.content.findAll('div', {'class': re.compile('(%s)' % '|'.join(div_classes))})]
        [el.extract() for el in self.content.findAll('span', {'class': re.compile('(%s)' % '|'.join(span_classes))})]
        self.remove_blocks()

        # remove all style attributes
        if self.remove.style_attribute:
            for el in self.content.findAll(style=True):
                del el['style']
            for el in self.content.findAll(bgcolor=True):
                del el['bgcolor']

        if self.remove.class_attribute:
            for el in self.content.findAll(True, {'class': True}):
                del el['class']

    def remove_blocks(self):
        '''
        Remove h2 title and all next tags siblings until next h2 title
        '''
        [el.extract() for el in self.find_block_contents(self.remove.block_titles)]

    def find_block_contents(self, titles):
        '''
        Find and return all block items with h2 title and all next tags siblings until next h2 title
        '''
        items = []
        for title in self.content.findAll(text=re.compile(u'(%s)' % u'|'.join(titles))):
            # get h2
            title = title.findParent('h2')
            if not title:
                continue
            next = title.nextSibling
            items += [title]
            while next and (isinstance(next, NavigableString) or next.name != 'h2'):
                items += [next]
                next = next.nextSibling
        return items